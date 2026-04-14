"""
fetch_river_names.py - v3
Uses GeoNames findNearbyStreams first, then findNearby H class.
This was the version that resolved 29% including the major rivers.
"""

import os, time, requests, pandas as pd
from tqdm import tqdm
from shapely import wkb

GEONAMES_USER = "sarah_jane"
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, "Data", "Clean")
OUTPUT    = os.path.join(CLEAN_DIR, "river_names_v3.parquet")
TOP_N     = 10
SLEEP_S   = 0.5

print("Loading rivers...")
df = pd.read_parquet(os.path.join(CLEAN_DIR, "rivers_with_countries.parquet"))
df["lon"] = df["geometry"].apply(lambda g: wkb.loads(g).x)
df["lat"] = df["geometry"].apply(lambda g: wkb.loads(g).y)
df = df.drop(columns=["geometry"])

top_per_country = (
    df.sort_values("emission", ascending=False)
    .groupby("country")
    .head(TOP_N)
    .reset_index(drop=True)
)
print(f"Points to look up: {len(top_per_country):,}")
print(f"Estimated time   : ~{len(top_per_country) * SLEEP_S / 60:.0f} minutes")

def get_river_name(lat, lon):
    # Try 1: streams specifically
    try:
        r = requests.get(
            "http://api.geonames.org/findNearbyStreamsJSON",
            params={"lat": lat, "lng": lon,
                    "username": GEONAMES_USER, "maxRows": 1},
            timeout=8,
        )
        data = r.json()
        if data.get("geonames"):
            name = data["geonames"][0].get("name", "")
            if name:
                return name
    except Exception:
        pass

    # Try 2: any H feature nearby
    try:
        r = requests.get(
            "http://api.geonames.org/findNearbyJSON",
            params={"lat": lat, "lng": lon,
                    "username":     GEONAMES_USER,
                    "featureClass": "H",
                    "maxRows":      1,
                    "radius":       10},
            timeout=8,
        )
        data = r.json()
        if data.get("geonames"):
            name = data["geonames"][0].get("name", "")
            if name:
                return name
    except Exception:
        pass

    return ""

print("\nFetching river names from GeoNames...")
names = []
for _, row in tqdm(top_per_country.iterrows(), total=len(top_per_country)):
    name = get_river_name(row["lat"], row["lon"])
    names.append(name)
    time.sleep(SLEEP_S)

top_per_country["river_name"] = names
top_per_country.to_parquet(OUTPUT, index=False)

resolved = (top_per_country["river_name"] != "").sum()
total    = len(top_per_country)
print(f"\n✅ Saved {total:,} rows to {OUTPUT}")
print(f"   {resolved} names resolved ({resolved/total*100:.0f}%)")
print(f"   {total - resolved} returned empty")

print("\nTop 20 resolved names:")
print(
    top_per_country[top_per_country["river_name"] != ""]
    .head(20)[["country", "emission", "river_name"]]
    .to_string(index=False)
)