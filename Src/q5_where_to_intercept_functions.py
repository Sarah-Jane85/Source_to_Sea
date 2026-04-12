# =============================================================
# q5_where_to_intercept.py
# Modular functions for Q5 — Where to clean up next
# Usage: from q5_where_to_intercept import *
# =============================================================

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.spatial import cKDTree
from shapely import wkb
from sklearn.cluster import HDBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# ── Constants ─────────────────────────────────────────────────
FIGURES_DIR = "../Figures"
THRESHOLD_KM = 50

INCOME_ORDER = {
    "Low-income countries": 1,
    "Lower-middle-income countries": 2,
    "Upper-middle-income countries": 3,
    "High-income countries": 4
}

COUNTRY_NAME_MAP = {
    "United States of America": "United States",
    "Solomon Is.": "Solomon Islands",
    "Dominican Rep.": "Dominican Republic",
    "Côte d'Ivoire": "Cote d'Ivoire",
    "Timor-Leste": "East Timor",
    "Eq. Guinea": "Equatorial Guinea",
    "Dem. Rep. Congo": "Democratic Republic of Congo",
    "N. Cyprus": "Cyprus"
}

MANUAL_OVERRIDES = {
    "003": "Vietnam",
    "006": "Guatemala",
}


# ── Data loading and preparation ──────────────────────────────

def load_rivers(rivers_raw: pd.DataFrame, df_countries: pd.DataFrame) -> pd.DataFrame:
    """
    Merge rivers with country income data, encode income score,
    and extract lat/lon from geometry.
    """
    rivers = rivers_raw.copy()
    rivers["country_clean"] = rivers["country"].replace(COUNTRY_NAME_MAP)
    rivers_merged = rivers.merge(
        df_countries, left_on="country_clean", right_on="country_name", how="left"
    )
    rivers_merged["income_score"] = rivers_merged["income_group"].map(INCOME_ORDER).fillna(2)
    rivers_merged["lon"] = rivers_merged["geometry"].apply(lambda g: wkb.loads(g).x)
    rivers_merged["lat"] = rivers_merged["geometry"].apply(lambda g: wkb.loads(g).y)
    print(f"Rivers loaded: {len(rivers_merged):,}")
    print(rivers_merged[["emission", "income_score"]].describe().round(2))
    return rivers_merged


def build_interceptors() -> pd.DataFrame:
    """Return the manually curated interceptors dataframe.
    
    Status types:
    - 'In operation'
    - 'Operation paused'
    - 'Installed for testing'
    - 'Port call / mobilisation' (ocean system, not river)
    - 'Maintenance'
    """
    interceptor_data = [
        # ── Indonesia ─────────────────────────────────────────
        {"interceptor_id": "001", "river": "Cengkareng Drain",     "city": "Jakarta",        "country": "Indonesia",          "lat": -6.1144,   "lon": 106.7436,   "year_deployed": 2019, "type": "Original",        "status": "In operation"},
        # ── Malaysia ──────────────────────────────────────────
        {"interceptor_id": "002", "river": "Klang River",          "city": "Selangor",       "country": "Malaysia",           "lat":  3.0319,   "lon": 101.3841,   "year_deployed": 2019, "type": "Original",        "status": "In operation"},
        {"interceptor_id": "005", "river": "Klang River",          "city": "Klang",          "country": "Malaysia",           "lat":  3.0350,   "lon": 101.3900,   "year_deployed": 2022, "type": "Original Gen3",   "status": "Maintenance"},
        # ── Vietnam ───────────────────────────────────────────
        {"interceptor_id": "003", "river": "Can Tho River",        "city": "Can Tho",        "country": "Vietnam",            "lat": 10.0341,   "lon": 105.7878,   "year_deployed": 2021, "type": "Original",        "status": "In operation"},
        # ── Dominican Republic ────────────────────────────────
        {"interceptor_id": "004", "river": "Rio Ozama",            "city": "Santo Domingo",  "country": "Dominican Republic", "lat": 18.4777,   "lon": -69.8803,   "year_deployed": 2021, "type": "Original",        "status": "Operation paused"},
        # ── United States ─────────────────────────────────────
        {"interceptor_id": "007", "river": "Ballona Creek",        "city": "Los Angeles",    "country": "United States",      "lat": 33.9800,   "lon": -118.4300,  "year_deployed": 2022, "type": "Original Gen3",   "status": "In operation"},
        # ── Jamaica ───────────────────────────────────────────
        {"interceptor_id": "008", "river": "Kingston Pen Gully",   "city": "Kingston",       "country": "Jamaica",            "lat": 17.9927,   "lon": -76.7894,   "year_deployed": 2022, "type": "Barrier",         "status": "In operation"},
        {"interceptor_id": "009", "river": "Barnes Gully",         "city": "Kingston",       "country": "Jamaica",            "lat": 17.9940,   "lon": -76.7850,   "year_deployed": 2022, "type": "Barrier",         "status": "In operation"},
        {"interceptor_id": "010", "river": "Rae Town Gully",       "city": "Kingston",       "country": "Jamaica",            "lat": 17.9910,   "lon": -76.7820,   "year_deployed": 2022, "type": "Tender",          "status": "In operation"},
        {"interceptor_id": "011", "river": "Tivoli Gully",         "city": "Kingston",       "country": "Jamaica",            "lat": 17.9960,   "lon": -76.7980,   "year_deployed": 2022, "type": "Guard",           "status": "In operation"},
        {"interceptor_id": "012", "river": "D'Aguilar Gully",      "city": "Kingston",       "country": "Jamaica",            "lat": 17.9980,   "lon": -76.7930,   "year_deployed": 2023, "type": "Guard",           "status": "In operation"},
        {"interceptor_id": "013", "river": "Mountain View Gully",  "city": "Kingston",       "country": "Jamaica",            "lat": 17.9970,   "lon": -76.7700,   "year_deployed": 2023, "type": "Barrier",         "status": "In operation"},
        {"interceptor_id": "014", "river": "Shoemaker Gully",      "city": "Kingston",       "country": "Jamaica",            "lat": 17.9950,   "lon": -76.7860,   "year_deployed": 2023, "type": "Barrier",         "status": "In operation"},
        {"interceptor_id": "015", "river": "Sandy Gully",          "city": "Kingston",       "country": "Jamaica",            "lat": 17.999322, "lon": -76.845990, "year_deployed": 2024, "type": "Guard",           "status": "In operation"},
        {"interceptor_id": "016", "river": "Balmagie Gully",       "city": "Kingston",       "country": "Jamaica",            "lat": 17.998279, "lon": -76.841219, "year_deployed": 2025, "type": "Guard",           "status": "In operation"},
        # ── Guatemala ─────────────────────────────────────────
        {"interceptor_id": "006", "river": "Rio Las Vacas",        "city": "Guatemala City", "country": "Guatemala",          "lat": 14.7200,   "lon": -90.5500,   "year_deployed": 2023, "type": "Barricade",       "status": "In operation"},
        {"interceptor_id": "021", "river": "Rio Motagua",          "city": "El Quetzalito",  "country": "Guatemala",          "lat": 15.7300,   "lon": -88.5700,   "year_deployed": 2024, "type": "Barricade XL",    "status": "In operation"},
        # ── Honduras ──────────────────────────────────────────
        {"interceptor_id": "023", "river": "Rio Chamelecon",       "city": "San Pedro Sula", "country": "Honduras",           "lat": 15.771882, "lon": -87.841552, "year_deployed": 2025, "type": "Guard",           "status": "Installed for testing"},
        # ── Thailand ──────────────────────────────────────────
        {"interceptor_id": "019", "river": "Chao Phraya River",    "city": "Bangkok",        "country": "Thailand",           "lat": 13.7200,  "lon": 100.5300,     "year_deployed": 2024, "type": "Original Gen3",   "status": "In operation"},
        # ── Panama ────────────────────────────────────────────
        {"interceptor_id": "020", "river": "Panama Bay tributary", "city": "Panama City",    "country": "Panama",             "lat":  8.9940,  "lon": -79.5190,     "year_deployed": 2025, "type": "Original",        "status": "In operation"},
        {"interceptor_id": "022", "river": "Rio Abajo",            "city": "Panama City",    "country": "Panama",             "lat": 9.013421, "lon": -79.485937,   "year_deployed": 2025, "type": "Guard",           "status": "Installed for testing"},
        # ── Ocean System (not a river interceptor) ────────────
        {"interceptor_id": "S03", "river": "Pacific Ocean",        "city": "Victoria",       "country": "Canada",             "lat": 48.4284,  "lon": -123.3656,    "year_deployed": 2023, "type": "Ocean System",    "status": "Port call / mobilisation"},
    ]
    df = pd.DataFrame(interceptor_data)
    df["has_interceptor"] = True

    # Summary stats
    river_df = df[df["type"] != "Ocean System"]
    active    = river_df[~river_df["status"].isin(["Operation paused", "Maintenance"])]
    paused    = river_df[river_df["status"] == "Operation paused"]
    maintenance = river_df[river_df["status"] == "Maintenance"]
    testing   = river_df[river_df["status"] == "Installed for testing"]

    print(f"Total interceptors (incl. ocean system) : {len(df)}")
    print(f"River interceptors total                : {len(river_df)}")
    print(f"  — In operation                        : {len(river_df[river_df['status'] == 'In operation'])}")
    print(f"  — Installed for testing               : {len(testing)}")
    print(f"  — Operation paused                    : {len(paused)}")
    print(f"  — Maintenance                         : {len(maintenance)}")
    print(f"Countries covered                       : {river_df['country'].nunique()}")

    return df


# ── Interceptor matching ──────────────────────────────────────

def match_interceptors_to_rivers(
    rivers_merged: pd.DataFrame,
    interceptors_df: pd.DataFrame,
    threshold_km: float = THRESHOLD_KM
) -> pd.DataFrame:
    """
    For each interceptor, find the nearest river within threshold_km
    using cKDTree. Applies manual overrides for distant matches.
    Returns rivers_merged with has_interceptor and interceptor_note columns.
    """
    rivers_clean = rivers_merged[["lat", "lon"]].dropna().copy()
    rivers_clean["original_index"] = rivers_clean.index

    tree = cKDTree(rivers_clean[["lat", "lon"]].values)
    interceptor_coords = interceptors_df[["lat", "lon"]].values
    distances, positions = tree.query(interceptor_coords)

    interceptors_df = interceptors_df.copy()
    interceptors_df["nearest_river_pos"] = positions
    interceptors_df["nearest_river_original_idx"] = rivers_clean.iloc[positions]["original_index"].values
    interceptors_df["dist_to_nearest_river_km"] = distances * 111

    rivers_merged = rivers_merged.copy()
    rivers_merged["has_interceptor"] = False
    rivers_merged["interceptor_note"] = ""

    for _, row in interceptors_df.iterrows():
        real_idx = row["nearest_river_original_idx"]
        if row["dist_to_nearest_river_km"] <= threshold_km:
            rivers_merged.loc[real_idx, "has_interceptor"] = True
            rivers_merged.loc[real_idx, "interceptor_note"] = row["interceptor_id"]
        elif row["interceptor_id"] in MANUAL_OVERRIDES:
            country = MANUAL_OVERRIDES[row["interceptor_id"]]
            fallback_idx = (
                rivers_merged[rivers_merged["country"] == country]["emission"].idxmax()
            )
            rivers_merged.loc[fallback_idx, "has_interceptor"] = True
            rivers_merged.loc[fallback_idx, "interceptor_note"] = f"{row['interceptor_id']}_approx"
            print(f"[{row['interceptor_id']}] Manual override → {country}")

    covered = rivers_merged["has_interceptor"].sum()
    total_emission = rivers_merged["emission"].sum()
    covered_emission = rivers_merged[rivers_merged["has_interceptor"]]["emission"].sum()
    print(f"\nRivers flagged      : {covered}")
    print(f"Emission covered    : {covered_emission/total_emission:.1%} of total")
    return rivers_merged


# ── HDBSCAN clustering ────────────────────────────────────────

def run_hdbscan(
    rivers_merged: pd.DataFrame,
    min_cluster_size: int = 1000,
    min_samples: int = 50
) -> pd.DataFrame:
    """
    Run HDBSCAN clustering on log_emission + income_score + has_interceptor.
    Adds cluster_hdbscan column to rivers_merged.
    """
    rivers = rivers_merged.copy()
    rivers["log_emission"] = np.log1p(rivers["emission"])
    rivers["has_interceptor_int"] = rivers["has_interceptor"].astype(int)

    features = rivers[["log_emission", "income_score", "has_interceptor_int"]].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    clusterer = HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples)
    rivers["cluster_hdbscan"] = clusterer.fit_predict(X_scaled)

    print(f"Cluster distribution:")
    print(rivers["cluster_hdbscan"].value_counts().sort_index())
    print(f"\nNoise points (-1): {(rivers['cluster_hdbscan'] == -1).sum():,}")
    return rivers


def cluster_summary(rivers: pd.DataFrame) -> pd.DataFrame:
    """Print mean emission and income score per cluster."""
    summary = (
        rivers.groupby("cluster_hdbscan")
        .agg(
            n_rivers=("emission", "count"),
            avg_emission=("emission", "mean"),
            total_emission=("emission", "sum"),
            avg_income_score=("income_score", "mean"),
        )
        .round(1)
        .reset_index()
    )
    print(summary.to_string(index=False))
    return summary


# ── H1: Interceptor coverage ──────────────────────────────────

def compute_coverage(rivers: pd.DataFrame) -> dict:
    """
    Compute what share of global river plastic emission
    is covered vs uncovered by interceptors.
    """
    total = rivers["emission"].sum()
    covered = rivers[rivers["has_interceptor"]]["emission"].sum()
    uncovered = total - covered
    result = {
        "total_emission": total,
        "covered_emission": covered,
        "uncovered_emission": uncovered,
        "covered_pct": covered / total * 100,
        "uncovered_pct": uncovered / total * 100,
    }
    print(f"Total emission    : {total:,.0f} t/yr")
    print(f"Covered           : {covered:,.0f} t/yr ({result['covered_pct']:.1f}%)")
    print(f"Uncovered         : {uncovered:,.0f} t/yr ({result['uncovered_pct']:.1f}%)")
    return result


# ── H3: Top 5 uncovered rivers ────────────────────────────────

def top5_uncovered_rivers(rivers: pd.DataFrame) -> pd.DataFrame:
    """
    Find top 5 uncovered rivers by emission and compute
    their cumulative share of total global emission.
    """
    total_emission = rivers["emission"].sum()
    uncovered = rivers[~rivers["has_interceptor"]].copy()
    top5 = (
        uncovered.nlargest(5, "emission")[["country", "emission", "lat", "lon"]]
        .reset_index(drop=True)
    )
    top5["rank"] = range(1, 6)
    top5["cumulative_emission"] = top5["emission"].cumsum()
    top5["cumulative_share_pct"] = top5["cumulative_emission"] / total_emission * 100
    print(top5[["rank", "country", "emission", "cumulative_share_pct"]].to_string(index=False))
    return top5


# ── Visualizations ────────────────────────────────────────────

def plot_interceptor_map(rivers: pd.DataFrame, interceptors_df: pd.DataFrame, save: bool = True) -> go.Figure:
    """World map showing interceptor locations and matched rivers."""
    matched_rivers = rivers[rivers["has_interceptor"]].copy()

    fig = go.Figure()

    fig.add_trace(go.Scattergeo(
        lat=matched_rivers["lat"],
        lon=matched_rivers["lon"],
        mode="markers",
        marker=dict(size=6, color="#1D9E75", opacity=0.7),
        name="Matched rivers",
        hovertemplate="<b>%{text}</b><br>Emission: %{customdata:.1f} t/yr<extra></extra>",
        text=matched_rivers["country"],
        customdata=matched_rivers["emission"],
    ))

    fig.add_trace(go.Scattergeo(
        lat=interceptors_df["lat"],
        lon=interceptors_df["lon"],
        mode="markers",
        marker=dict(size=12, color="#E24B4A", symbol="star"),
        name="Interceptors",
        hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>",
        text=interceptors_df["river"],
        customdata=interceptors_df["country"],
    ))

    fig.update_layout(
        title=dict(text="Q5 — Interceptor locations and matched rivers", font=dict(size=15)),
        geo=dict(showland=True, landcolor="#F1EFE8", showocean=True, oceancolor="#E1F5EE",
                 showcountries=True, countrycolor="#D3D1C7", projection_type="natural earth"),
        margin=dict(t=50, b=0, l=0, r=0),
        height=500, width=800,
        legend=dict(x=0.01, y=0.99),
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/q5_interceptor_map.html")
    return fig


def plot_cluster_map(rivers: pd.DataFrame, save: bool = True) -> go.Figure:
    """World map coloured by HDBSCAN cluster."""
    color_map = {-1: "#E24B4A", 0: "#378ADD", 1: "#1D9E75", 2: "#EF9F27", 3: "#9F77DD"}
    label_map = {-1: "Noise (extreme emitters)", 0: "Cluster 0", 1: "Cluster 1 (top priority)", 2: "Cluster 2", 3: "Cluster 3"}

    fig = go.Figure()
    for cluster_id in sorted(rivers["cluster_hdbscan"].unique()):
        subset = rivers[rivers["cluster_hdbscan"] == cluster_id]
        fig.add_trace(go.Scattergeo(
            lat=subset["lat"],
            lon=subset["lon"],
            mode="markers",
            marker=dict(size=3, color=color_map.get(cluster_id, "#888"), opacity=0.5),
            name=label_map.get(cluster_id, f"Cluster {cluster_id}"),
        ))

    fig.update_layout(
        title=dict(text="Q5 H2 — River clusters by emission + income profile (HDBSCAN)", font=dict(size=15)),
        geo=dict(showland=True, landcolor="#F1EFE8", showocean=True, oceancolor="#E1F5EE",
                 showcountries=True, countrycolor="#D3D1C7", projection_type="natural earth"),
        margin=dict(t=50, b=0, l=0, r=0),
        height=500, width=800,
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/q5_cluster_map.html")
    return fig


def plot_top5_uncovered(top5: pd.DataFrame, rivers: pd.DataFrame, save: bool = True) -> go.Figure:
    """Bar chart of top 5 uncovered rivers by emission with cumulative share."""
    total_emission = rivers["emission"].sum()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top5["country"] + " (#" + top5["rank"].astype(str) + ")",
        y=top5["emission"],
        marker_color="#E24B4A",
        text=[f"{e:,.0f} t/yr" for e in top5["emission"]],
        textposition="outside",
        name="Emission",
    ))
    fig.add_trace(go.Scatter(
        x=top5["country"] + " (#" + top5["rank"].astype(str) + ")",
        y=top5["cumulative_share_pct"],
        mode="lines+markers",
        line=dict(color="#378ADD", width=2),
        marker=dict(size=8),
        yaxis="y2",
        name="Cumulative share (%)",
    ))

    fig.update_layout(
        title=dict(text="Q5 H3 — Top 5 uncovered rivers by plastic emission", font=dict(size=15)),
        xaxis_title="River / Country",
        yaxis=dict(title="Emission (t/yr)", tickformat=",", range=[0, top5["emission"].max() * 1.15]),
        yaxis2=dict(title="Cumulative share of global emission (%)", overlaying="y", side="right", ticksuffix="%"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=12),
        margin=dict(t=80, b=80, l=80, r=80),
        height=460, width=720,
        legend=dict(x=0.01, y=0.99),
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/q5_h3_top5_uncovered.html")
    return fig


def plot_high_income_bubble(rivers: pd.DataFrame, save: bool = True) -> go.Figure:
    """
    Bubble chart: high income countries by emission vs pollution per capita.
    Bubble size = total emission.
    """
    high_income = rivers[rivers["income_score"] == 4].copy()
    country_agg = (
        high_income.groupby("country_clean")
        .agg(total_emission=("emission", "sum"), n_rivers=("emission", "count"))
        .reset_index()
    )

    fig = px.scatter(
        country_agg,
        x="n_rivers",
        y="total_emission",
        size="total_emission",
        color="total_emission",
        hover_name="country_clean",
        color_continuous_scale=[[0, "#E1F5EE"], [0.5, "#1D9E75"], [1.0, "#04342C"]],
        labels={"n_rivers": "Number of rivers", "total_emission": "Total emission (t/yr)"},
        title="Q5 — High income countries: number of rivers vs total plastic emission",
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="sans-serif", size=12),
        margin=dict(t=80, b=60, l=60, r=40),
        height=480, width=700,
    )
    if save:
        fig.write_html(f"{FIGURES_DIR}/q5_high_income_bubble.html")
    return fig
