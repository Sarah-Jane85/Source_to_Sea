"""
fetch_overpass_secondpass.py
-----------------------------
Second-pass river name lookup using OpenStreetMap Overpass API.
Runs ONLY on points that GeoNames left unresolved.

BATCH MODE: processes BATCH_SIZE points per run, then stops automatically.
Safe to schedule - lock file prevents overlapping runs.

Usage:
    python Src/fetch_overpass_secondpass.py
"""

import os
import time
import requests
import pandas as pd
from tqdm import tqdm

# ── Config ───────────────────────────────────────────────────────────────────
GEONAMES_CSV    = r"Data\Clean\river_names_all.csv"
OUTPUT_CSV      = r"Data\Clean\overpass_secondpass.csv"
FINAL_PKL       = r"Data\Clean\river_names_all.parquet"
LOCK_FILE       = r"Data\Clean\overpass.lock"

SLEEP_S         = 1.0    # 1 second between calls
SAVE_EVERY      = 100
BATCH_SIZE      = 400
REQUEST_TIMEOUT = 12
MAX_RETRIES     = 1      # give up fast, don't retry

OVERPASS_URL    = "https://overpass-api.de/api/interpreter"
HEADERS         = {"User-Agent": "SourceToSea-PlasticTracker/1.0"}
RADII           = [5000]  # single radius — covers most cases, much faster
PRIORITY_TYPES  = ["river", "stream", "canal", "drain", "tidal_channel",
                   "waterway", "creek", "ditch"]
# ─────────────────────────────────────────────────────────────────────────────

# ── Lock file ─────────────────────────────────────────────────────────────────
if os.path.exists(LOCK_FILE):
    print("Another batch is still running (lock file found). Exiting safely.")
    exit()
open(LOCK_FILE, "w").close()


def get_name_overpass(lat, lon):
    """Query Overpass for named waterways near (lat, lon). Hard timeout."""
    for radius in RADII:
        query = (
            "[out:json][timeout:10];"
            "way[waterway][name](around:" + str(radius) + "," +
            str(lat) + "," + str(lon) + ");"
            "out tags 3;"
        )
        try:
            r = requests.post(
                OVERPASS_URL,
                data={"data": query},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code != 200:
                return ""

            elements = r.json().get("elements", [])
            if not elements:
                return ""

            # Priority match by waterway type
            for wtype in PRIORITY_TYPES:
                for el in elements:
                    tags = el.get("tags", {})
                    if tags.get("waterway") == wtype:
                        name = tags.get("name:en") or tags.get("name", "")
                        if name:
                            return name.strip()

            # Fallback to first named result
            for el in elements:
                name = (el.get("tags", {}).get("name:en") or
                        el.get("tags", {}).get("name", ""))
                if name:
                    return name.strip()

        except requests.exceptions.Timeout:
            return ""
        except Exception:
            return ""

    return ""


# ── Load GeoNames results & find unresolved ───────────────────────────────────
print("Loading GeoNames results...")
geonames_df = pd.read_csv(GEONAMES_CSV)
geonames_df["river_name"] = geonames_df["river_name"].fillna("").astype(str).str.strip()
unresolved = geonames_df[geonames_df["river_name"] == ""].copy().reset_index(drop=True)
print("  " + str(len(unresolved)) + " unresolved points to work through")

# ── Resume logic ──────────────────────────────────────────────────────────────
already_done = set()
if os.path.exists(OUTPUT_CSV):
    done_df = pd.read_csv(OUTPUT_CSV)
    already_done = set(done_df["point_id"].tolist())
    print("  Resuming - " + str(len(already_done)) + " already done, " +
          str(len(unresolved) - len(already_done)) + " remaining")
else:
    pd.DataFrame(columns=["point_id", "emission", "lat", "lon", "river_name"]
                 ).to_csv(OUTPUT_CSV, index=False)
    print("  Starting fresh")

todo = unresolved[~unresolved["point_id"].isin(already_done)].copy()
total_remaining = len(todo)

if total_remaining == 0:
    print("\nAll unresolved points queried! Merging final results...")
else:
    batch = todo.head(BATCH_SIZE)
    batches_left = -(-total_remaining // BATCH_SIZE)
    print("\nThis batch     : " + str(len(batch)) + " points")
    print("Batches left   : " + str(batches_left) + " (including this one)")
    print("Total remaining: " + str(total_remaining))
    print("Est. this run  : ~" + str(round(len(batch) * SLEEP_S / 60)) + " minutes\n")

    buffer = []
    try:
        for _, row in tqdm(batch.iterrows(), total=len(batch), desc="Overpass lookup"):
            name = get_name_overpass(row["lat"], row["lon"])
            buffer.append({
                "point_id":   int(row["point_id"]),
                "emission":   row["emission"],
                "lat":        row["lat"],
                "lon":        row["lon"],
                "river_name": name,
            })
            time.sleep(SLEEP_S)
            if len(buffer) >= SAVE_EVERY:
                pd.DataFrame(buffer).to_csv(OUTPUT_CSV, mode="a", header=False, index=False)
                buffer = []
    finally:
        if buffer:
            pd.DataFrame(buffer).to_csv(OUTPUT_CSV, mode="a", header=False, index=False)
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    remaining_after = total_remaining - len(batch)
    print("\nBatch complete!")
    print("Points still to go: " + str(remaining_after) +
          " (~" + str(-(-remaining_after // BATCH_SIZE)) + " more runs)\n")

# ── Merge results back into main CSV + parquet ────────────────────────────────
print("Merging into river_names_all...")
overpass_df = pd.read_csv(OUTPUT_CSV)
overpass_df["river_name"] = overpass_df["river_name"].fillna("").astype(str).str.strip()
overpass_hits = overpass_df[overpass_df["river_name"] != ""][["point_id", "river_name"]]
print("  Overpass resolved " + str(len(overpass_hits)) + " / " + str(len(overpass_df)) +
      " queried (" + str(round(len(overpass_hits)/max(len(overpass_df),1)*100)) + "%)")

merged = geonames_df.copy().set_index("point_id")
for _, row in overpass_hits.iterrows():
    pid = int(row["point_id"])
    if pid in merged.index and merged.at[pid, "river_name"] == "":
        merged.at[pid, "river_name"] = row["river_name"]
merged = merged.reset_index()

merged.to_csv(GEONAMES_CSV, index=False)
merged.to_parquet(FINAL_PKL, index=False)

n_resolved = (merged["river_name"] != "").sum()
print("\nDone! river_names_all updated.")
print(str(n_resolved) + " / " + str(len(merged)) + " points resolved (" +
      str(round(n_resolved/len(merged)*100)) + "%)")
print("\nTop 10 by emission (resolved):")
print(
    merged[merged["river_name"] != ""]
    .sort_values("emission", ascending=False)
    .head(10)[["emission", "river_name"]]
    .to_string(index=False)
)

if os.path.exists(LOCK_FILE):
    os.remove(LOCK_FILE)
