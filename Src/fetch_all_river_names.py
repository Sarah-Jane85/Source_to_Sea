"""
fetch_all_river_names.py
------------------------
Reverse-geocodes ALL 31,819 Meijer 2021 emission points directly using
GeoNames — NO country filter, purely coordinate-based.

This fixes the Schelde / cross-border river problem: we go straight from
lat/lon -> river name, skipping country lookup entirely.

BATCH MODE: processes BATCH_SIZE points per run, then stops automatically.
Run once per hour to stay under GeoNames free tier (1,000 req/hour).
Progress is saved after every 100 rows — just run again to continue.

Usage:
    python Src/fetch_all_river_names.py        <- run once per hour
"""

import os
import time
import requests
import pandas as pd
import geopandas as gpd
from tqdm import tqdm

# ── Config ───────────────────────────────────────────────────────────────────
GEONAMES_USER = "YOUR_USERNAME_HERE"   # <- replace with your GeoNames username

INPUT_SHP  = r"Data\Raw\meijer2021\Meijer2021_midpoint_emissions.shp"
OUTPUT_CSV = r"Data\Clean\river_names_all.csv"
OUTPUT_PKL = r"Data\Clean\river_names_all.parquet"
LOCK_FILE  = r"Data\Clean\geonames.lock"

SLEEP_S    = 4.0   # seconds between calls — safely under 1,000/hour
SAVE_EVERY = 100   # checkpoint every N rows
BATCH_SIZE = 900   # stop automatically after this many points per run
# ─────────────────────────────────────────────────────────────────────────────

# ── Lock file — prevents two instances running at once ───────────────────────
if os.path.exists(LOCK_FILE):
    print("Another batch is still running (lock file found). Exiting safely.")
    exit()

open(LOCK_FILE, "w").close()  # create lock
# ─────────────────────────────────────────────────────────────────────────────


def get_river_name(lat: float, lon: float, username: str) -> str:
    """
    Query GeoNames findNearbyJSON (featureClass H) for the nearest
    river/stream/water feature to (lat, lon).

    Tries increasing search radii: 5km -> 15km -> 30km.
    Within each radius, prefers actual river/stream feature codes
    over generic water bodies.

    Returns name string or "" if nothing found.
    """
    priority_codes = ["STM", "STRM", "RVR", "STMI", "STMH",
                      "CHNM", "CHN", "ESTY", "BAY", "LK", "INLT"]

    for radius in [5, 15, 30]:
        try:
            r = requests.get(
                "http://api.geonames.org/findNearbyJSON",
                params={
                    "lat": lat,
                    "lng": lon,
                    "username": username,
                    "featureClass": "H",
                    "radius": radius,
                    "maxRows": 5,
                },
                timeout=10,
            )
            results = r.json().get("geonames", [])
            if not results:
                continue

            # Try priority codes first
            for code in priority_codes:
                for item in results:
                    if item.get("fcode") == code:
                        return item.get("name", "")

            # Fall back to closest result regardless of code
            return results[0].get("name", "")

        except Exception:
            time.sleep(2)  # wait a bit after error before trying next radius
            continue

        time.sleep(0.1)

    return ""


# ── Load shapefile ────────────────────────────────────────────────────────────
print("Loading shapefile...")
gdf = gpd.read_file(INPUT_SHP)
gdf["lon"] = gdf.geometry.x
gdf["lat"] = gdf.geometry.y
gdf = gdf.reset_index(drop=True)
gdf["point_id"] = gdf.index
print(f"  {len(gdf):,} emission points loaded")

# ── Resume logic ──────────────────────────────────────────────────────────────
already_done = set()
if os.path.exists(OUTPUT_CSV):
    done_df = pd.read_csv(OUTPUT_CSV)
    already_done = set(done_df["point_id"].tolist())
    print(f"  Resuming — {len(already_done):,} done so far, "
          f"{len(gdf) - len(already_done):,} remaining")
else:
    pd.DataFrame(columns=["point_id", "emission", "lat", "lon", "river_name"]
                 ).to_csv(OUTPUT_CSV, index=False)
    print("  Starting fresh")

todo = gdf[~gdf["point_id"].isin(already_done)].copy()
total_remaining = len(todo)

if total_remaining == 0:
    print("\nAll points already resolved! Building final parquet...")
else:
    # Take only this batch
    batch = todo.head(BATCH_SIZE)
    batches_left = -(-total_remaining // BATCH_SIZE)  # ceiling division
    print(f"\nThis batch     : {len(batch):,} points")
    print(f"Batches left   : {batches_left} (including this one)")
    print(f"Total remaining: {total_remaining:,}")
    print(f"Est. this run  : ~{len(batch) * SLEEP_S / 60:.0f} minutes\n")

    # ── Batch loop ────────────────────────────────────────────────────────────
    buffer = []

    try:
        for _, row in tqdm(batch.iterrows(), total=len(batch), desc="Fetching names"):
            name = get_river_name(row["lat"], row["lon"], GEONAMES_USER)

            buffer.append({
                "point_id":   int(row["point_id"]),
                "emission":   row["dots_exten"],
                "lat":        row["lat"],
                "lon":        row["lon"],
                "river_name": name,
            })

            time.sleep(SLEEP_S)

            if len(buffer) >= SAVE_EVERY:
                pd.DataFrame(buffer).to_csv(OUTPUT_CSV, mode="a", header=False, index=False)
                buffer = []

    finally:
        # Always save buffer and release lock, even if script crashes
        if buffer:
            pd.DataFrame(buffer).to_csv(OUTPUT_CSV, mode="a", header=False, index=False)
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    print(f"\nBatch complete! Run the script again in ~1 hour for the next batch.")
    remaining_after = total_remaining - len(batch)
    print(f"Points still to go: {remaining_after:,} "
          f"(~{-(-remaining_after // BATCH_SIZE)} more runs)\n")

# ── Rebuild parquet from full CSV ─────────────────────────────────────────────
print("Updating parquet...")
final = pd.read_csv(OUTPUT_CSV)
final = final.drop_duplicates(subset="point_id").sort_values("point_id").reset_index(drop=True)
final["river_name"] = final["river_name"].fillna("").astype(str).str.strip()
final.to_parquet(OUTPUT_PKL, index=False)

# Release lock if still exists (e.g. all done path)
if os.path.exists(LOCK_FILE):
    os.remove(LOCK_FILE)

n_done     = len(final)
n_resolved = (final["river_name"] != "").sum()
print(f"  {n_done:,} / {len(gdf):,} points in parquet")
print(f"  {n_resolved:,} names resolved so far ({n_resolved/n_done*100:.0f}% of queried)")

if n_resolved > 0:
    print("\nTop 10 by emission so far:")
    print(
        final[final["river_name"] != ""]
        .sort_values("emission", ascending=False)
        .head(10)[["emission", "river_name"]]
        .to_string(index=False)
    )
