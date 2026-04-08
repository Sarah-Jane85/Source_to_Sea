# src/q1_functions.py
# Modular functions for 02_Q1_plastic_sources.ipynb

import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely import wkb
import plotly.express as px
from sqlalchemy import create_engine


# ── Country name maps (reused across multiple functions) ──────────────────────

COUNTRY_NAME_MAP = {
    "United States of America": "United States",
    "Solomon Is.":              "Solomon Islands",
    "Dominican Rep.":           "Dominican Republic",
    "Cote d'Ivoire":            "Cote d'Ivoire",
    "Timor-Leste":              "East Timor",
    "Eq. Guinea":               "Equatorial Guinea",
    "Dem. Rep. Congo":          "Democratic Republic of Congo",
    "N. Cyprus":                "Cyprus"
}

INCOME_OVERRIDES = {
    "United States":                "High-income countries",
    "Solomon Islands":              "Lower-middle-income countries",
    "Dominican Republic":           "Upper-middle-income countries",
    "Cote d'Ivoire":                "Lower-middle-income countries",
    "East Timor":                   "Lower-middle-income countries",
    "Equatorial Guinea":            "Upper-middle-income countries",
    "Democratic Republic of Congo": "Low-income countries",
    "Cyprus":                       "High-income countries",
    "Ocean":                        "Ocean"
}


# ── DB connection ─────────────────────────────────────────────────────────────

def get_engine(password: str, db: str = "river_risk_index"):
    """Create SQLAlchemy engine for MySQL."""
    return create_engine(f"mysql+mysqlconnector://root:{password}@localhost/{db}")


# ── Countries master table ────────────────────────────────────────────────────

def build_countries_master(df7: pd.DataFrame, df1: pd.DataFrame) -> pd.DataFrame:
    """
    Build countries_master from plastic_vs_pollution (file7)
    and rivers_with_countries (file1).
    Returns df with country_id, continent_id, country_name, income_group, iso_code.
    """
    continent_map = {
        'Africa': 1, 'Asia': 2, 'Europe': 3,
        'North America': 4, 'South America': 5,
        'Oceania': 6, 'Antarctica': 7
    }
    countries_master = df7[['country', 'iso_code', 'income_group']].drop_duplicates(subset='country')
    continent_lookup = df1[['country', 'continent']].drop_duplicates(subset='country')
    countries_master = countries_master.merge(continent_lookup, on='country', how='left')
    countries_master['continent_id'] = countries_master['continent'].map(continent_map).fillna(8).astype(int)
    countries_master = countries_master.reset_index(drop=True)
    countries_master['country_id'] = countries_master.index + 1
    return countries_master[['country_id', 'continent_id', 'country', 'income_group', 'iso_code']].rename(
        columns={'country': 'country_name'}
    )


# ── Plastic generation table ──────────────────────────────────────────────────

def build_plastic_generation_db(df6: pd.DataFrame, countries_db: pd.DataFrame) -> pd.DataFrame:
    """
    Merge plastic_generation with countries_db to get country_id.
    Applies manual fixes for 3 known unmatched countries.
    """
    pg = df6.merge(
        countries_db[['country_id', 'country_name']],
        left_on='country', right_on='country_name', how='left'
    ).reset_index(drop=True)
    pg['plastic_generation_id'] = pg.index + 1

    fixes = {'Belize': 247, 'Channel Islands': 248, 'Montenegro': 249}
    for country, cid in fixes.items():
        pg.loc[pg['country'] == country, 'country_id'] = cid

    pg_db = pg[['plastic_generation_id', 'year', 'plastic_generation_tonnes',
                'plastic_generation_million_tonnes', 'country_id']]
    print(f"Nulls remaining:\n{pg_db.isnull().sum()}")
    return pg_db


# ── Emission points table ─────────────────────────────────────────────────────

def build_emission_points(rivers_full: pd.DataFrame, df_countries: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare emission_points table from Meijer rivers data.
    Extracts lat/lon from geometry, merges country_id/continent_id,
    applies income group overrides. Returns df ready for SQL upload.
    """
    rivers_full = rivers_full.copy()
    rivers_full["lon"] = rivers_full["geometry"].apply(lambda g: wkb.loads(g).x)
    rivers_full["lat"] = rivers_full["geometry"].apply(lambda g: wkb.loads(g).y)
    rivers_full = rivers_full.drop(columns=["geometry"])
    rivers_full["country_clean"] = rivers_full["country"].replace(COUNTRY_NAME_MAP)

    df_merged = rivers_full.merge(
        df_countries[['country_id', 'country_name', 'continent_id', 'income_group']],
        left_on="country_clean", right_on="country_name", how="left"
    )

    mask = df_merged["income_group"].isna() & df_merged["country_clean"].isin(INCOME_OVERRIDES)
    df_merged.loc[mask, "income_group"] = df_merged.loc[mask, "country_clean"].map(INCOME_OVERRIDES)

    final_df = df_merged[['country_id', 'continent_id', 'lat', 'lon', 'emission', 'income_group']].copy()
    final_df = final_df.rename(columns={'emission': 'emission_tons_year'})

    initial_count = len(final_df)
    final_df = final_df.dropna(subset=['country_id', 'continent_id'])
    print(f"Dropped {initial_count - len(final_df)} rows due to missing country/continent IDs.")
    print(f"Final shape: {final_df.shape}")

    final_df['country_id']   = final_df['country_id'].astype(int)
    final_df['continent_id'] = final_df['continent_id'].astype(int)
    return final_df


# ── Choropleth data prep ──────────────────────────────────────────────────────

def prep_choropleth_data(engine) -> pd.DataFrame:
    """Load emissions from SQL, clean names, merge ISO codes, aggregate by country."""
    df_raw = pd.read_sql("SELECT country, emission FROM all_emission_points WHERE emission > 0", engine)
    df_raw['country_clean'] = df_raw['country'].replace(COUNTRY_NAME_MAP)
    df_countries = pd.read_sql("SELECT country_name, iso_code FROM countries", engine)
    df_merged = df_raw.merge(df_countries, left_on='country_clean', right_on='country_name', how='inner')
    return (df_merged.groupby(['country_name', 'iso_code'])['emission']
                     .sum().reset_index()
                     .rename(columns={'emission': 'total_emissions'}))


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_emission_distribution(engine) -> None:
    """Two histograms: full distribution (log y) and zoomed to <1000 tons."""
    df = pd.read_sql("SELECT emission FROM all_emission_points WHERE emission > 0", engine)

    fig = px.histogram(df, x="emission", nbins=50, log_y=True,
                       title="Distribution of River Plastic Emissions (Univariate)",
                       labels={"emission": "Emission (tons/year)"},
                       color_discrete_sequence=["#1f77b4"])
    fig.update_layout(showlegend=False)
    fig.show()

    df_zoom = df[df['emission'] < 1000]
    fig2 = px.histogram(df_zoom, x="emission", nbins=50,
                        title="Distribution of Emissions (Rivers < 1,000 tons/year)",
                        labels={"emission": "Emission (tons/year)"},
                        color_discrete_sequence=["#1f77b4"])
    fig2.update_layout(showlegend=False)
    fig2.show()


def plot_emissions_by_income_group(engine) -> None:
    """Boxplot of emissions split by income group."""
    df = pd.read_sql("""
        SELECT emission, income_group
        FROM all_emission_points
        WHERE income_group IS NOT NULL AND emission > 0
    """, engine)
    fig = px.box(df, x="income_group", y="emission", log_y=True,
                 title="Plastic Emissions by Country Income Group (Bivariate)",
                 labels={"income_group": "Income Group", "emission": "Emission (tons/year)"},
                 color_discrete_sequence=["#006994"])
    fig.update_layout(showlegend=False, xaxis_tickangle=-45)
    fig.show()


def plot_choropleth(engine) -> None:
    """Choropleth map of global river plastic emissions by country."""
    df_map = prep_choropleth_data(engine)
    fig = px.choropleth(
        df_map,
        locations="iso_code",
        color="total_emissions",
        hover_name="country_name",
        color_continuous_scale="Reds",
        title="Global River Plastic Emissions by Country (Tons/Year)",
        labels={"total_emissions": "Emission (tons)"}
    )
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True, bgcolor='rgba(255,255,255,0)'),
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Tons/Year", len=0.6)
    )
    fig.show()
