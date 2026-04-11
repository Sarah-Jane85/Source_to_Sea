# src/cleaning_functions.py
# Modular functions for 01_data_cleaning.ipynb
# Covers all 8 datasets

import os
import re
import yaml
import warnings
import pdfplumber
import numpy as np
import polars as pl
import pandas as pd
import geopandas as gpd
from pathlib import Path
import matplotlib.pyplot as plt
from shapely.geometry import Point

warnings.filterwarnings("ignore")


# ── Shared utilities ──────────────────────────────────────────────────────────

def load_config(path: str = "../config.yaml") -> dict:
    """Load config.yaml and return as dict."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_clean_parquet(df: pd.DataFrame, path: Path) -> None:
    """Save cleaned DataFrame as parquet."""
    df.to_parquet(path, index=False)
    print(f"Saved → {path}  ({path.stat().st_size / 1024:.1f} KB, {len(df):,} rows)")


def inspect_dataframe(df: pd.DataFrame, name: str = "DataFrame") -> None:
    """Print shape, dtypes, null counts and basic stats."""
    print(f"\n{'='*55}\n  {name}  —  {df.shape[0]:,} rows × {df.shape[1]} cols\n{'='*55}")
    print("\n── Columns ──");      print(df.columns.tolist())
    print("\n── Dtypes ──");       print(df.dtypes)
    print("\n── Null counts ──")
    null_counts = df.isnull().sum()
    null_pct    = (null_counts / len(df) * 100).round(2)
    print(pd.DataFrame({"nulls": null_counts, "null_%": null_pct}))
    print("\n── Stats ──");        print(df.describe())


def remove_duplicates(df: pd.DataFrame, key_cols: list = None) -> pd.DataFrame:
    """Remove exact duplicates, then logical duplicates on key_cols if provided."""
    n_exact = df.duplicated().sum()
    print(f"Exact duplicates: {n_exact}")
    df = df.drop_duplicates()

    if key_cols:
        key_cols = [c for c in key_cols if c in df.columns]
        n_logical = df.duplicated(subset=key_cols).sum()
        print(f"Logical duplicates on {key_cols}: {n_logical}")
        df = df.drop_duplicates(subset=key_cols, keep="first")

    return df


def split_countries_and_regions(df: pd.DataFrame) -> tuple:
    """Separate country-level rows from aggregate rows (iso_code == 'REGION')."""
    mask      = df["iso_code"] == "REGION"
    countries = df[~mask].reset_index(drop=True)
    regions   = df[ mask].reset_index(drop=True)
    print(f"Countries: {len(countries):,} rows, {countries['country'].nunique()} unique")
    print(f"Regions  : {len(regions):,} rows")
    return countries, regions


# ── Dataset 1: rivers_with_countries ─────────────────────────────────────────

def load_rivers(path: str) -> gpd.GeoDataFrame:
    """Load Meijer2021 shapefile."""
    return gpd.read_file(path)


def assign_countries_to_rivers(rivers: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Spatial join rivers to country polygons.
    First pass: 10m resolution. Then progressive buffer for unmatched points.
    Falls back to 'Ocean' for truly oceanic points.
    """
    world = gpd.read_file("https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip")

    rivers_with_countries = gpd.sjoin(
        rivers,
        world[["geometry", "NAME", "CONTINENT"]],
        how="left",
        predicate="within"
    ).rename(columns={
        "dots_exten": "emission",
        "NAME": "country",
        "CONTINENT": "continent"
    }).drop(columns=["index_right"])

    print(f"Unknown after 10m join: {rivers_with_countries['country'].isna().sum()}")

    for buffer_size in [0.1, 0.25, 0.5, 1.0]:
        still_unknown = rivers_with_countries[
            rivers_with_countries["country"].isna()
        ].drop(columns=["country", "continent"])

        if len(still_unknown) == 0:
            break

        world_buffered = world.copy()
        world_buffered["geometry"] = world.geometry.buffer(buffer_size)

        filled = gpd.sjoin(
            still_unknown,
            world_buffered[["geometry", "NAME", "CONTINENT"]],
            how="left",
            predicate="within"
        ).rename(columns={"NAME": "country", "CONTINENT": "continent"}).drop(columns=["index_right"])

        filled = filled[~filled.index.duplicated(keep="first")]
        rivers_with_countries.update(filled[["country", "continent"]])

        remaining = rivers_with_countries["country"].isna().sum()
        print(f"Buffer {buffer_size}° → {remaining} unknown remaining")

    rivers_with_countries["country"]   = rivers_with_countries["country"].fillna("Ocean")
    rivers_with_countries["continent"] = rivers_with_countries["continent"].fillna("Ocean")
    return rivers_with_countries


def plot_rivers_known_unknown(rivers_with_countries: gpd.GeoDataFrame) -> None:
    """Plot known vs unknown country assignments on world map."""
    fig, ax = plt.subplots(figsize=(15, 8))
    world = gpd.read_file("https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip")
    world.plot(ax=ax, color='#e8e7e1', edgecolor='#c0bfb8', linewidth=0.4)

    known   = rivers_with_countries[rivers_with_countries["country"].notna()]
    unknown = rivers_with_countries[rivers_with_countries["country"].isna()]

    ax.scatter(unknown.geometry.apply(lambda p: p.x), unknown.geometry.apply(lambda p: p.y),
               s=1.5, color='#E24B4A', alpha=0.6, label=f'Unknown ({len(unknown):,})')
    ax.scatter(known.geometry.apply(lambda p: p.x), known.geometry.apply(lambda p: p.y),
               s=0.8, color='#3B8BD4', alpha=0.4, label=f'Known ({len(known):,})')

    ax.set_title("River emission points: known vs unknown country", fontsize=14, pad=12)
    ax.legend(loc='lower left', markerscale=4, framealpha=0.8)
    ax.set_xlim(-180, 180); ax.set_ylim(-90, 90); ax.set_axis_off()
    plt.tight_layout(); plt.show()


# ── Dataset 2: plastic_adrift ─────────────────────────────────────────────────

def load_plastic_adrift(path: str) -> pl.DataFrame:
    """Load and clean plastic adrift CSV (Polars)."""
    df = pl.read_csv(path)
    df = df.with_columns([
        (pl.col("year") + 2021).alias("year"),
        pl.when(pl.col("lng") > 180)
          .then(pl.col("lng") - 360)
          .otherwise(pl.col("lng"))
          .alias("lng")
    ])
    print(f"lng range after fix: {df['lng'].min()} to {df['lng'].max()}")
    return df


# ── Dataset 3: marine_microplastics ──────────────────────────────────────────

def load_marine_microplastics(path: str) -> pl.DataFrame:
    """Load, clean and rename marine microplastics CSV (Polars)."""
    df = pl.read_csv(path, ignore_errors=True)

    cols_to_keep = [
        "OBJECTID", "Latitude (degree)", "Longitude (degree)", "Ocean",
        "Marine Setting", "Sampling Method", "Mesh Size (mm)",
        "Microplastics Measurement", "Unit", "Concentration Class",
        "Sample Date", "x", "y"
    ]
    df = df.select(cols_to_keep).rename({
        "Latitude (degree)":       "lat",
        "Longitude (degree)":      "lng",
        "Marine Setting":          "setting",
        "Sampling Method":         "sampling_method",
        "Mesh Size (mm)":          "mesh_size_mm",
        "Microplastics Measurement": "microplastics_measurement",
        "Concentration Class":     "concentration_class",
        "Sample Date":             "sample_date",
        "Ocean":                   "ocean",
        "Unit":                    "unit"
    })
    df = df.with_columns(
        pl.col("sample_date").str.to_date(format="%m/%d/%Y %I:%M:%S %p", strict=False)
    )

    # add sample_datetime as alias for compatibility
    df = df.with_columns(pl.col("sample_date").alias("sample_datetime"))

    print(f"Shape: {df.shape}")
    print(f"sample_date nulls: {df['sample_date'].null_count()}")
    return df


# ── Dataset 5: ocean_plastic ──────────────────────────────────────────────────

def load_ocean_plastic(path: Path) -> pd.DataFrame:
    """Load raw plastic-waste-accumulated-in-oceans.csv."""
    df = pd.read_csv(path)
    print(f"Loaded → {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def rename_ocean_plastic_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise column names to snake_case."""
    return df.copy().rename(columns={
        "Entity": "country",
        "Code":   "iso_code",
        "Year":   "year",
        "Plastic leakage to aquatic environment - Leakage type: Accumulated stock in oceans": "plastic_ocean_tonnes",
    })


def handle_missing_ocean_plastic(df: pd.DataFrame) -> pd.DataFrame:
    """Fill iso_code NaN with 'REGION', drop rows with no plastic value."""
    df = df.copy()
    rows_before = len(df)
    df["iso_code"] = df["iso_code"].fillna("REGION")
    df = df.dropna(subset=["plastic_ocean_tonnes"])
    print(f"Rows before: {rows_before:,} → after: {len(df):,} (removed {rows_before - len(df)})")
    return df


def fix_dtypes_ocean_plastic(df: pd.DataFrame) -> pd.DataFrame:
    """Cast year → Int64, tonnes → float, strings → str."""
    df = df.copy()
    df["year"]                  = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["plastic_ocean_tonnes"]  = pd.to_numeric(df["plastic_ocean_tonnes"], errors="coerce")
    for col in ["country", "iso_code"]:
        df[col] = df[col].astype(str).str.strip()
    return df


def add_derived_columns_ocean_plastic(df: pd.DataFrame) -> pd.DataFrame:
    """Add plastic_ocean_million_tonnes and decade columns."""
    df = df.copy()
    df["plastic_ocean_million_tonnes"] = (df["plastic_ocean_tonnes"] / 1_000_000).round(4)
    df["decade"] = (df["year"].astype(int) // 10 * 10)
    return df


def sanity_check_ocean_plastic(df: pd.DataFrame) -> None:
    """Check for negatives, year range, and top 5 countries."""
    neg = (df["plastic_ocean_tonnes"] < 0).sum()
    print(f"Negative values : {'none ✅' if neg == 0 else f'{neg} found ⚠️'}")
    print(f"Year range      : {df['year'].min()} – {df['year'].max()}")
    print("\nTop 10 countries by avg plastic_ocean_tonnes:")
    print(df.groupby("country")["plastic_ocean_tonnes"].mean()
            .sort_values(ascending=False).head(10).reset_index().to_string(index=False))


def plot_global_ocean_trend(regions_df: pd.DataFrame, countries_df: pd.DataFrame) -> None:
    """Plot total ocean plastic over time."""
    world = regions_df[regions_df["country"].str.lower() == "world"].sort_values("year")
    if world.empty:
        world = countries_df.groupby("year", as_index=False)["plastic_ocean_tonnes"].sum()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(world["year"], world["plastic_ocean_tonnes"] / 1e6,
            color="steelblue", linewidth=2.5, marker="o", markersize=4)
    ax.fill_between(world["year"], world["plastic_ocean_tonnes"] / 1e6, alpha=0.15, color="steelblue")
    ax.set_title("Plastic Waste in Oceans — Global Trend")
    ax.set_xlabel("Year"); ax.set_ylabel("Million Tonnes")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout(); plt.show()


def clean_ocean_plastic(path: Path) -> tuple:
    """Full pipeline for ocean_plastic. Returns (countries_df, regions_df)."""
    df = load_ocean_plastic(path)
    df = rename_ocean_plastic_columns(df)
    df = handle_missing_ocean_plastic(df)
    df = fix_dtypes_ocean_plastic(df)
    df = remove_duplicates(df, key_cols=["country", "year"])
    countries, regions = split_countries_and_regions(df)
    countries = add_derived_columns_ocean_plastic(countries)
    sanity_check_ocean_plastic(countries)
    return countries, regions


# ── Dataset 6: plastic_generation ────────────────────────────────────────────

def clean_plastic_generation(path: str) -> pd.DataFrame:
    """Full pipeline for plastic_generation."""
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Entity": "country",
        "Code":   "iso_code",
        "Year":   "year",
        "Plastic waste generation (tonnes, total)": "plastic_generation_tonnes",
    })
    df["year"]                      = df["year"].astype("Int64")
    df["plastic_generation_tonnes"] = df["plastic_generation_tonnes"].astype(float)
    df["country"]                   = df["country"].astype(str).str.strip()
    df["iso_code"]                  = df["iso_code"].astype(str).str.strip()
    df = remove_duplicates(df, key_cols=["country", "year"])
    df["plastic_generation_million_tonnes"] = (df["plastic_generation_tonnes"] / 1_000_000).round(4)

    neg = (df["plastic_generation_tonnes"] < 0).sum()
    print(f"Negative values: {'none ✅' if neg == 0 else f'{neg} found ⚠️'}")
    print(f"Year range: {df['year'].min()} – {df['year'].max()}, Countries: {df['country'].nunique()}")
    return df


# ── Dataset 7: plastic_vs_pollution ──────────────────────────────────────────

def clean_plastic_vs_pollution(path: str) -> tuple:
    """Full pipeline for plastic_vs_pollution. Returns (countries_df, regions_df)."""
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Entity":                                   "country",
        "Code":                                     "iso_code",
        "Year":                                     "year",
        "Plastic pollution per capita":             "plastic_pollution_per_capita",
        "Plastic waste generation per capita":      "plastic_generation_per_capita",
        "World Bank's 2025 income classification":  "income_group",
    })
    df["iso_code"]     = df["iso_code"].fillna("REGION")
    df["income_group"] = df["income_group"].fillna("Unknown")
    df["year"]                          = df["year"].astype("Int64")
    df["plastic_pollution_per_capita"]  = df["plastic_pollution_per_capita"].astype(float)
    df["plastic_generation_per_capita"] = df["plastic_generation_per_capita"].astype(float)
    for col in ["country", "iso_code", "income_group"]:
        df[col] = df[col].astype(str).str.strip()
    df = remove_duplicates(df, key_cols=["country", "year"])
    return split_countries_and_regions(df)


# ── Dataset 8: ocean_cleanup_efforts ─────────────────────────────────────────

def build_toc_dataset() -> pd.DataFrame:
    """Create The Ocean Cleanup dataset from hardcoded milestones."""
    toc_data = {
        "year":         [2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "kg_removed":   [103000, 397000, 500000, 2000000, 8000000, 11500000, 25000000],
        "organisation": "The Ocean Cleanup",
        "cleanup_type": "Ocean + River",
        "source_url":   "https://theoceancleanup.com/milestones"
    }
    df = pd.DataFrame(toc_data)
    df["kg_removed_annual"]     = df["kg_removed"]
    df["kg_removed_cumulative"] = df["kg_removed"].cumsum()
    return df.drop(columns=["kg_removed"])


def build_icc_dataset() -> pd.DataFrame:
    """Create ICC (Ocean Conservancy) dataset from published annual reports."""
    icc_data = {
        "year": list(range(2008, 2026)),
        "volunteers": [
            378000, 408000, 520000, 519000, 560000, 648000,
            561000, 788000, 800000, 892000, 704000, 530000,
            630000, 486000, 486000, 550000, 486000, 500000
        ],
        "kg_removed": [
            round(x * 0.453592) for x in [
                7200000, 7600000, 8000000, 9200000, 10200000, 12400000,
                10100000, 18400000, 18600000, 23600000, 19700000, 9100000,
                16800000, 8000000, 7900000, 8200000, 7400000, 8000000
            ]
        ],
        "countries": [
            104, 108, 108, 112, 151, 153,
            91, 112, 112, 122, 112, 80,
            100, 116, 116, 120, 120, 125
        ],
        "organisation": "Ocean Conservancy (ICC)",
        "cleanup_type": "Beach + Waterway",
        "source_url": "https://oceanconservancy.org/work/plastics/cleanups-icc/annual-data-release/"
    }
    df = pd.DataFrame(icc_data)
    df["kg_removed_annual"]     = df["kg_removed"]
    df["kg_removed_cumulative"] = df["kg_removed"].cumsum()
    return df.drop(columns=["kg_removed"])


def combine_cleanup_efforts(toc_df: pd.DataFrame, icc_df: pd.DataFrame) -> pd.DataFrame:
    """Combine TOC and ICC into one unified cleanup_efforts DataFrame."""
    combined = pd.concat([toc_df, icc_df], ignore_index=True)
    combined = combined.sort_values(["year", "organisation"]).reset_index(drop=True)
    combined["volunteers"] = combined["volunteers"].fillna(0).astype(int)
    combined["countries"]  = combined["countries"].fillna(0).astype(int)
    print(f"Shape: {combined.shape}")
    print(f"Organisations: {combined['organisation'].unique()}")
    print(f"Year range   : {combined['year'].min()} – {combined['year'].max()}")
    return combined


def sanity_check_cleanup_efforts(df: pd.DataFrame) -> None:
    """Check for negatives and print summary per organisation."""
    neg = (df["kg_removed_annual"] < 0).sum()
    print(f"Negative kg values: {'none ✅' if neg == 0 else f'{neg} ⚠️'}")
    print("\nTotal kg removed per organisation:")
    print(df.groupby("organisation")["kg_removed_annual"].sum()
            .apply(lambda x: f"{x:,.0f} kg").to_string())


def build_cleanup_efforts() -> pd.DataFrame:
    """Full pipeline: build, combine and validate cleanup_efforts."""
    toc = build_toc_dataset()
    icc = build_icc_dataset()
    df  = combine_cleanup_efforts(toc, icc)
    sanity_check_cleanup_efforts(df)
    return df


# ── Dataset 8 (extra): top50_rivers_ranked from PDF ──────────────────────────

def parse_rivers_from_pdf(pdf_path: str) -> pd.DataFrame:
    """Extract top-50 river rankings from supplementary PDF."""
    rivers_ranked = []
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(20, 30):
            page = pdf.pages[i]
            text = page.extract_text()
            if text:
                for line in text.split('\n'):
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        match = re.match(r'^(\d+)\s+(.+?)\s+(\S+)\s+([\d.E+]+)\s+', line.strip())
                        if match and int(match.group(1)) <= 1000:
                            rivers_ranked.append({
                                'ranking':           match.group(1),
                                'river_name':        match.group(2),
                                'country':           match.group(3),
                                'emission_tons_year': match.group(4)
                            })

    df = pd.DataFrame(rivers_ranked).drop_duplicates(subset='ranking')

    # Manual fixes for known parsing errors
    fixes = {
        '23': ('Msimbazi River',        'Tanzania'),
        '49': ('Rio Ozama',             'Dominican Republic'),
        '21': ('Ebrie Lagoon / Komoe',  'Ivory Coast'),
    }
    for ranking, (river, country) in fixes.items():
        df.loc[df['ranking'] == ranking, 'river_name'] = river
        df.loc[df['ranking'] == ranking, 'country']    = country

    df = df[df['ranking'].astype(int) <= 50]
    df['ranking']           = df['ranking'].astype(int)
    df['emission_tons_year'] = df['emission_tons_year'].astype(float)

    print(f"Shape: {df.shape}")
    return df

# ── Dataset 9: species ────────────────────────────────────────────────────────

def clean_species(path: str) -> pd.DataFrame:
    """Load and clean marine species plastic ingestion dataset."""
    df = pd.read_csv(path, encoding="latin1", low_memory=False)

    cols_to_keep = [
        "Citation", "id", "Taxa", "Group", "Species", "Family",
        "Age", "Size", "Size_avg", "Sex", "Latitude", "Longitude",
        "Death", "COD", "harddeath", "softdeath", "threaddeath",
        "rubberdeath", "foamdeath", "clothdeath", "nrdeath",
        "hard", "soft", "rubber", "thread", "foam", "cloth ",
        "net", "rope", "line", "balloon", "bag", "bottle",
        "fisheries", "nurdle", "NR", "total", "volume", "mass",
        "acute injury", "Obstruction or perforation?"
    ]
    df = df[cols_to_keep].copy()
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(" ", "_").str.replace("?", "", regex=False))

    # Drop 99% null column
    df = df.drop(columns=["obstruction_or_perforation"])

    # Decode cause of death
    cod_map = {
        "KND": "Known Natural Death",
        "KD":  "Known Death",
        "Ind": "Indeterminate",
        "IND": "Indeterminate",
        "PD":  "Plastic Death"
    }
    df["cod_label"] = df["cod"].map(cod_map).fillna("Unknown")

    # Fix numeric columns
    plastic_cols = [
        "hard", "soft", "rubber", "thread", "foam", "cloth",
        "net", "rope", "line", "balloon", "bag", "bottle",
        "fisheries", "nurdle", "nr", "total", "volume", "mass"
    ]
    for col in plastic_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["size_avg"]  = pd.to_numeric(df["size_avg"],  errors="coerce")
    df["group"]     = df["group"].str.strip().str.title()

    # Derived columns
    ingestion_cols    = ["hard", "soft", "foam", "nurdle", "nr",
                         "balloon", "bag", "bottle", "rubber"]
    entanglement_cols = ["net", "rope", "line", "fisheries"]

    df["has_ingestion"]        = (df[ingestion_cols].sum(axis=1) > 0).astype(int)
    df["is_entangled"]         = (df[entanglement_cols].sum(axis=1) > 0).astype(int)
    df["ghost_net_entanglement"] = (
        (df["fisheries"] > 0) | (df["net"] > 0) |
        (df["rope"] > 0)      | (df["line"] > 0)
    ).astype(int)
    df["log_size"]  = np.log1p(df["size_avg"])
    df["is_large"]  = (df["size_avg"] >= 200).astype(int)

    def assign_gyre(lat, lon):
        if pd.isna(lat) or pd.isna(lon): return "Unknown"
        if 20 <= lat <= 45 and -170 <= lon <= -130: return "North Pacific"
        if -50 <= lat <= -15 and -140 <= lon <= -70: return "South Pacific"
        if 20 <= lat <= 45 and -70 <= lon <= -20:  return "North Atlantic"
        if -45 <= lat <= -15 and -40 <= lon <= 20: return "South Atlantic"
        if -40 <= lat <= 10 and 40 <= lon <= 100:  return "Indian Ocean"
        return "Outside Gyres"

    df["gyre_region"] = df.apply(
        lambda row: assign_gyre(row["latitude"], row["longitude"]), axis=1
    )

    print(f"Shape: {df.shape}")
    print(f"Ingestion records : {df['has_ingestion'].sum():,}")
    print(f"Entanglement records: {df['is_entangled'].sum():,}")
    return df

# ── Dataset 10: fish_to_human ─────────────────────────────────────────────────

def build_fish_to_human() -> pd.DataFrame:
    """
    Manually curated microplastics-in-fish dataset.
    Sources: Danopoulos et al. 2020, Frontiers Marine Science 2023,
             Black Sea study 2023, Iberian Peninsula study 2023.
    """
    data = [
        ("Sardina pilchardus",     "Sardine",           2.3, "Filter feeder",    "Pelagic",  True,  "Mediterranean",    "Danopoulos et al. 2020"),
        ("Engraulis encrasicolus", "Anchovy",           1.4, "Selective feeder", "Pelagic",  True,  "Mediterranean",    "Danopoulos et al. 2020"),
        ("Trachurus trachurus",    "Horse mackerel",    3.8, "Opportunistic",    "Pelagic",  False, "Iberian Peninsula","Frontiers 2023"),
        ("Gadus morhua",           "Atlantic cod",      4.1, "Opportunistic",    "Demersal", False, "Baltic Sea",       "Baltic Sea study 2023"),
        ("Mullus barbatus",        "Red mullet",        6.1, "Demersal feeder",  "Demersal", False, "Black Sea",        "Black Sea study 2023"),
        ("Dicentrarchus labrax",   "European seabass",  7.6, "Opportunistic",    "Demersal", False, "Black Sea",        "Black Sea study 2023"),
        ("Sparus aurata",          "Gilthead seabream", 9.0, "Omnivore",         "Demersal", False, "Black Sea",        "Black Sea study 2023"),
        ("Oncorhynchus mykiss",    "Rainbow trout",     9.3, "Opportunistic",    "Farmed",   False, "Black Sea",        "Black Sea study 2023"),
        ("Merlangius merlangus",   "Whiting",           4.7, "Opportunistic",    "Demersal", False, "Black Sea",        "Black Sea study 2023"),
        ("Thunnus thynnus",        "Bluefin tuna",      3.2, "Apex predator",    "Pelagic",  False, "Mediterranean",    "Frontiers 2023"),
    ]
    df = pd.DataFrame(data, columns=[
        "species", "common_name", "mp_per_individual", "feeding_type",
        "habitat", "consumed_whole", "region", "source"
    ])
    print(f"Shape: {df.shape}")
    return df    