# src/q2_functions.py
# Modular functions for 03_Q2_accumulation.ipynb
# Covers H2 (proximity analysis) and H3 (accumulation vs cleanup)

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats


# ── Constants ─────────────────────────────────────────────────────────────────

EARTH_RADIUS_KM = 6371.0

GYRE_CENTERS = pd.DataFrame({
    'Gyre': ['North Pacific', 'South Pacific', 'North Atlantic', 'South Atlantic', 'Indian Ocean'],
    'lat':  [40,  -35,  40, -30, -25],
    'lng':  [-160, -110, -40, -15,  80]
})

NET_KEYWORDS = ['net']  # str.contains with case=False catches all variants

CONTAINER_KEYWORDS = [
    'Grab sample', 'Intake seawater pump', 'Stainless steel bucket', 'Aluminum bucket',
    'CTD rosette sampler', 'Day grab', 'Ekman dredge', 'Megacorer', 'Stainless steel spoon',
    'Trowel', 'Metal scoop', 'Metal spoon', 'stainless-steel sampler', 'Petite Ponar benthic grab',
    'Sediment grab sampler', 'Van Veen grab', 'shovel', 'Van Dorn sampler', 'Shipek grab sampler',
    'glass jar', 'Kubiena box', 'stainless-steel spatula', 'stainless steel spatula',
    'stainless steel bucket', 'Niskin bottle', 'box corer', 'Ekman grab', 'PVC cylinder',
    'Surface water intake'
]


# ── Data loading ──────────────────────────────────────────────────────────────

def load_observed_plastic(engine, nets_only: bool = False) -> pd.DataFrame:
    """Load observed_plastic from SQL, optionally filtered to net samples only."""
    where = "WHERE concentration > 0"
    if nets_only:
        where += " AND sampling_method LIKE '%net%'"
    return pd.read_sql(f"SELECT lat, lng, concentration, sampling_method FROM observed_plastic {where}", engine)


def load_emission_points(engine, limit: int = 1000) -> pd.DataFrame:
    """Load top N emission points from SQL ordered by emission volume."""
    query = f"""
        SELECT lat, lon, emission_tons_year
        FROM emission_points
        ORDER BY emission_tons_year DESC
        LIMIT {limit}
    """
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        if "Unknown column 'lon'" in str(e):
            return pd.read_sql(query.replace('lon', 'lng'), engine)
        raise e


def prepare_observed_plastic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean marine_microplastics parquet for SQL upload.
    Renames measurement col to 'concentration', extracts year, drops nulls.
    """
    df = df.copy()
    df['sample_date']  = pd.to_datetime(df['sample_date'], errors='coerce')
    df['year']         = df['sample_date'].dt.year
    df = df.rename(columns={'microplastics_measurement': 'concentration'})
    df['sampling_method'] = df['sampling_method'].astype(str)
    df['concentration']   = pd.to_numeric(df['concentration'], errors='coerce')
    df = df.dropna(subset=['year', 'lat', 'lng', 'concentration', 'sampling_method'])
    return df[['year', 'lat', 'lng', 'concentration', 'sampling_method']].copy()


# ── Distance calculation ──────────────────────────────────────────────────────

def haversine_min_distance(plastic_df: pd.DataFrame, rivers_df: pd.DataFrame) -> np.ndarray:
    """
    Vectorized haversine distance from each plastic point to nearest river.
    Returns array of minimum distances in km (one per plastic sample).

    plastic_df must have columns: lat, lng
    rivers_df  must have columns: lat, lon (or lng)
    """
    lon_col = 'lon' if 'lon' in rivers_df.columns else 'lng'

    rivers_rad  = np.radians(rivers_df[['lat', lon_col]].values)
    plastic_rad = np.radians(plastic_df[['lat', 'lng']].values)

    dlat = plastic_rad[:, None, 0] - rivers_rad[None, :, 0]
    dlon = plastic_rad[:, None, 1] - rivers_rad[None, :, 1]
    a = (np.sin(dlat / 2.0) ** 2
         + np.cos(plastic_rad[:, None, 0]) * np.cos(rivers_rad[None, :, 0]) * np.sin(dlon / 2.0) ** 2)
    distances = EARTH_RADIUS_KM * 2 * np.arcsin(np.sqrt(a))
    return distances.min(axis=1), distances.argmin(axis=1)


def categorize_proximity(dist_km: float) -> str:
    """Assign a proximity zone label based on distance to nearest river."""
    if dist_km <= 50:
        return 'Near River (<50km)'
    elif dist_km <= 200:
        return 'Regional (50-200km)'
    return 'Open Ocean / Far (>200km)'


# ── H2: Proximity analysis ────────────────────────────────────────────────────

def run_proximity_analysis(plastic_df: pd.DataFrame, rivers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate distance from each plastic sample to nearest river,
    assign proximity zone, and return aggregated summary.
    """
    min_dist, _ = haversine_min_distance(plastic_df, rivers_df)
    plastic_df  = plastic_df.copy()
    plastic_df['dist_to_nearest_river_km'] = min_dist
    plastic_df['proximity_zone']           = plastic_df['dist_to_nearest_river_km'].apply(categorize_proximity)

    global_avg = plastic_df['concentration'].mean()
    summary    = (plastic_df.groupby('proximity_zone')
                             .agg(sample_count=('concentration', 'count'),
                                  avg_density=('concentration', 'mean'),
                                  max_hotspot=('concentration', 'max'))
                             .reset_index())
    summary['relative_density_index'] = (summary['avg_density'] / global_avg).round(2)
    return summary


def run_coastal_bivariate(plastic_df: pd.DataFrame, rivers_df: pd.DataFrame,
                          threshold_km: int = 50) -> tuple:
    """
    Link coastal plastic samples to nearest river emission volume.
    Returns (coastal_df with bins, summary_df).
    Falls back to 200km if nothing found at threshold.
    """
    min_dist, min_idx = haversine_min_distance(plastic_df, rivers_df)
    plastic_df = plastic_df.copy()
    plastic_df['dist_to_nearest_major_river'] = min_dist

    coastal = plastic_df[plastic_df['dist_to_nearest_major_river'] <= threshold_km].copy()
    if len(coastal) == 0:
        print(f"No samples within {threshold_km}km — expanding to 200km...")
        threshold_km = 200
        coastal = plastic_df[plastic_df['dist_to_nearest_major_river'] <= threshold_km].copy()

    print(f"Analyzing {len(coastal)} samples within {threshold_km}km of top rivers.")

    # Link emission volume
    filtered_mask          = plastic_df.index.isin(coastal.index)
    coastal['river_idx']   = min_idx[filtered_mask]
    emission_vals          = rivers_df['emission_tons_year'].values
    coastal['source_emission'] = emission_vals[coastal['river_idx']]

    # Bin by emission quartile
    n_bins = 4 if coastal['source_emission'].nunique() >= 4 else 2
    labels = ['Low (Q1)', 'Medium (Q2)', 'High (Q3)', 'Very High (Q4)'][:n_bins]
    coastal['emission_bin'] = pd.qcut(coastal['source_emission'], q=n_bins,
                                      labels=labels, duplicates='drop')
    coastal = coastal.dropna(subset=['emission', 'emission_bin', 'concentration']
                             if 'emission' in coastal.columns
                             else ['source_emission', 'emission_bin', 'concentration'])

    summary = (coastal.groupby('emission_bin', observed=True)
                      .agg(sample_count=('concentration', 'count'),
                           avg_density=('concentration', 'mean'),
                           max_density=('concentration', 'max'),
                           avg_emission=('source_emission', 'mean'))
                      .reset_index())
    return coastal, summary, threshold_km


def run_statistical_tests(coastal: pd.DataFrame) -> None:
    """Run Pearson, Spearman and one-way ANOVA on coastal plastic vs emission volume."""
    if coastal['emission_bin'].nunique() < 2:
        print("Not enough groups for statistical tests.")
        return

    try:
        r, p = stats.pearsonr(coastal['source_emission'], coastal['concentration'])
        print(f"\n1. PEARSON CORRELATION:  r = {r:.4f},  p = {p:.4e}")
    except Exception as e:
        print(f"\n1. PEARSON: failed ({e})")

    try:
        rho, p = stats.spearmanr(coastal['source_emission'], coastal['concentration'])
        print(f"2. SPEARMAN CORRELATION: rho = {rho:.4f},  p = {p:.4e}")
    except Exception as e:
        print(f"2. SPEARMAN: failed ({e})")

    try:
        groups     = [g['concentration'].values for _, g in coastal.groupby('emission_bin')]
        f_stat, p  = stats.f_oneway(*groups)
        print(f"3. ONE-WAY ANOVA:        F = {f_stat:.4f},  p = {p:.4e}")
        sig = "✅ Significant" if p < 0.05 else "⚠️  Not significant"
        print(f"   → {sig} (alpha = 0.05)")
    except Exception as e:
        print(f"3. ANOVA: failed ({e})")


# ── H3: Accumulation vs cleanup ───────────────────────────────────────────────

def get_net_samples(df_micro: pd.DataFrame, start_year: int = 2008) -> pd.DataFrame:
    """Filter microplastics to net-based sampling methods and extract year."""
    df = df_micro[df_micro['sampling_method'].str.contains('net', case=False, na=False)].copy()
    df['year'] = pd.to_datetime(df['sample_date']).dt.year
    return df[df['year'] >= start_year]


def get_accumulation_by_year(df_nets: pd.DataFrame) -> pd.Series:
    """Mean microplastic concentration per year."""
    return df_nets.groupby('year')['microplastics_measurement'].mean()


def get_sample_counts(df_nets: pd.DataFrame) -> pd.Series:
    """Number of net samples per year."""
    return df_nets.groupby('year').size()


def get_cleanup_by_year(df_cleanup: pd.DataFrame) -> pd.Series:
    """Max cumulative kg removed per year."""
    df_cleanup = df_cleanup.copy()
    df_cleanup['year'] = df_cleanup['year'].astype(int)
    return df_cleanup.groupby('year')['kg_removed_cumulative'].max()


def normalize_to_baseline(series: pd.Series, base_year: int = 2008) -> pd.Series:
    """Index a series so that base_year = 100."""
    return series / series[base_year] * 100


def plot_h3(accumulation: pd.Series, sample_counts: pd.Series,
            cleanup: pd.Series, acc_norm: pd.Series, clean_norm: pd.Series,
            save_path: str = None) -> None:
    """
    3-panel H3 chart:
    - Top-left:  avg concentration with sample count bars
    - Top-right: cumulative cleanup
    - Bottom:    both indexed to 2008 = 100
    """
    color_acc     = '#E63946'
    color_cleanup = '#457B9D'
    color_count   = '#aaaaaa'

    fig = plt.figure(figsize=(14, 9))
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(2, 1, 2)

    fig.suptitle('H3: Plastic Accumulation vs. Cleanup Efforts (2008–present)\nNet-based samples only',
                 fontsize=13, fontweight='bold')

    # Top-left: concentration + sample count bars
    ax1b = ax1.twinx()
    ax1b.bar(sample_counts.index, sample_counts.values, color=color_count, alpha=0.3, label='Sample count')
    ax1b.set_ylabel('Number of samples', color=color_count, fontsize=8)
    ax1b.tick_params(axis='y', labelcolor=color_count)
    ax1.plot(accumulation.index, accumulation.values, color=color_acc, marker='o', linewidth=2, zorder=3)
    ax1.fill_between(accumulation.index, accumulation.values, alpha=0.15, color=color_acc)
    ax1.set_title('Avg Microplastic Concentration\n(net-based samples)')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Avg Concentration (pieces/m³)', color=color_acc)
    ax1.tick_params(axis='y', labelcolor=color_acc)
    lines1, _    = ax1.get_legend_handles_labels()
    lines1b, lb1 = ax1b.get_legend_handles_labels()
    ax1.legend(lines1 + lines1b, ['Avg concentration'] + lb1, loc='upper left', fontsize=7)

    # Top-right: cumulative cleanup
    ax2.fill_between(cleanup.index, cleanup.values, alpha=0.2, color=color_cleanup)
    ax2.plot(cleanup.index, cleanup.values, color=color_cleanup, marker='s', linewidth=2, label='Cumulative removed')
    ax2.set_title('Cumulative Plastic Removed by Cleanup\n(all organisations)')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Cumulative Plastic Removed (kg)')
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M kg'))
    ax2.legend(loc='upper left', fontsize=7)

    # Bottom: normalized
    ax3.plot(acc_norm.index, acc_norm.values, color=color_acc, marker='o', linewidth=2,
             label='Microplastic concentration (2008=100)')
    ax3.plot(clean_norm.index, clean_norm.values, color=color_cleanup, marker='s', linewidth=2,
             label='Cumulative cleanup (2008=100)')
    ax3.fill_between(acc_norm.index, acc_norm.values, alpha=0.1, color=color_acc)
    ax3.fill_between(clean_norm.index, clean_norm.values, alpha=0.1, color=color_cleanup)
    ax3.axhline(100, color='black', linestyle='--', linewidth=0.8, alpha=0.5, label='2008 baseline')
    ax3.set_title('Relative Growth: Concentration vs. Cleanup Effort\n(both indexed to 2008 = 100)')
    ax3.set_xlabel('Year')
    ax3.set_ylabel('Index (2008 = 100)')
    ax3.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved → {save_path}")
    plt.show()


# ── Plots: H2 ─────────────────────────────────────────────────────────────────

def plot_proximity_bar(summary: pd.DataFrame, title_suffix: str = "") -> None:
    """Bar chart of avg density by proximity zone."""
    fig = px.bar(
        summary, x='proximity_zone', y='avg_density',
        title=f'H2: Macro-Plastic Density vs. River Proximity{title_suffix}',
        labels={'proximity_zone': 'Distance from River', 'avg_density': 'Avg Concentration (particles/m³)'},
        color='avg_density', color_continuous_scale='Reds', text_auto='.2f'
    )
    fig.update_layout(showlegend=False)
    fig.show()


def plot_proximity_pie(summary: pd.DataFrame, total_samples: int) -> None:
    """Pie chart of sample distribution across proximity zones."""
    fig = px.pie(
        summary, values='sample_count', names='proximity_zone',
        title=f'H2 Sample Distribution (Nets Only)\nTotal Samples: {total_samples}',
        color_discrete_sequence=px.colors.sequential.Blues, hole=0.4
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.show()


def plot_within_50km_bar(plastic_df: pd.DataFrame, rivers_df: pd.DataFrame, title_suffix: str = "") -> None:
    """Simple bar: samples within 50km vs farther away."""
    min_dist, _ = haversine_min_distance(plastic_df, rivers_df)
    near        = (min_dist <= 50).sum()
    total       = len(plastic_df)
    pct         = (near / total) * 100

    fig = px.bar(
        x=['Within 50km of Rivers', 'Farther Away'],
        y=[near, total - near],
        title=f'H2: {pct:.1f}% of Samples are Within 50km of River Mouths{title_suffix}',
        color=[near, total - near], color_continuous_scale='Reds', text_auto=True
    )
    fig.update_layout(showlegend=False, yaxis_title='Number of Samples')
    fig.show()
    print(f"Total: {total}, Within 50km: {near} ({pct:.2f}%)")


def plot_bivariate_bar(summary: pd.DataFrame, threshold_km: int) -> None:
    """Bar chart of avg density by emission quartile bin."""
    fig = px.bar(
        summary, x='emission_bin', y='avg_density',
        title=f'River Emission vs. Macro-Plastic Density (Nets Only)\n(Avg Density within {threshold_km}km)',
        labels={'emission_bin': 'River Emission Category', 'avg_density': 'Avg Density (particles/m³)'},
        color='avg_density', color_continuous_scale='Reds', text_auto='.2f'
    )
    fig.update_layout(showlegend=False)
    fig.show()


def plot_bivariate_scatter(coastal: pd.DataFrame) -> None:
    """Scatter of source emission vs concentration (log x). Only runs if < 5000 points."""
    if len(coastal) >= 5000:
        print("Skipping scatter (too many points).")
        return
    fig = px.scatter(
        coastal, x='source_emission', y='concentration',
        title='Individual Samples: Source Emission vs. Macro-Plastic Density',
        labels={'source_emission': 'River Emission (Tons/Year)', 'concentration': 'Plastic Density'},
        opacity=0.3, log_x=True
    )
    fig.update_traces(marker=dict(size=8))
    fig.show()


def plot_gyre_map(plastic_df: pd.DataFrame) -> None:
    """Scatter mapbox of plastic concentration with gyre center markers."""
    fig = px.scatter_mapbox(
        plastic_df, lat='lat', lon='lng', color='concentration',
        color_continuous_scale='Reds', size_max=10, opacity=0.8,
        title='Q2: Global Macro-Plastic Distribution (Nets Only)',
        mapbox_style='carto-positron', zoom=1, center={'lat': 20, 'lon': 0}
    )
    fig.update_coloraxes(cmax=5, cmin=0)

    fig.add_trace(px.scatter_mapbox(
        GYRE_CENTERS, lat='lat', lon='lng',
        color_discrete_sequence=['blue'], size_max=15
    ).data[0])

    for _, row in GYRE_CENTERS.iterrows():
        fig.add_annotation(
            x=row['lng'], y=row['lat'], text=row['Gyre'],
            font=dict(color='blue', size=12, family='Arial Black'),
            showarrow=False, bgcolor='white', bordercolor='blue'
        )

    fig.update_layout(margin={'r': 0, 't': 50, 'l': 0, 'b': 0})
    fig.show()


# ── Methodological bias analysis ──────────────────────────────────────────────

def aggregate_by_year(data: pd.DataFrame, group_name: str) -> pd.DataFrame:
    """Mean microplastics_measurement per year for a given group."""
    if len(data) == 0:
        return pd.DataFrame()
    agg = data.groupby('year')['microplastics_measurement'].mean().reset_index()
    agg.columns = ['year', 'avg_microplastics_measurement']
    agg['group'] = group_name
    return agg


def plot_method_bias(df: pd.DataFrame) -> None:
    """
    Compare net vs container sampling trends over time (log y scale).
    Shows methodological divergence post-2013.
    """
    df_net       = df[df['sampling_method'].str.contains('net', case=False, na=False)]
    df_container = df[df['sampling_method'].str.contains(
        '|'.join(CONTAINER_KEYWORDS), case=False, na=False)]

    stats_net       = aggregate_by_year(df_net, 'Net Sampling (Standard)')
    stats_container = aggregate_by_year(df_container, 'Container Sampling (Micro/High-Res)')

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stats_net['year'], y=stats_net['avg_microplastics_measurement'],
                             mode='lines+markers', name='Net Sampling (Standard)',
                             line=dict(color='green', width=3), marker=dict(size=8)))
    fig.add_trace(go.Scatter(x=stats_container['year'], y=stats_container['avg_microplastics_measurement'],
                             mode='lines+markers', name='Container/Jar Sampling (High-Res)',
                             line=dict(color='red', width=3, dash='dot'), marker=dict(size=8)))
    fig.update_layout(
        title='<b>Methodological Bias: Why Raw Trends Are Misleading</b>'
              '<br><sup>Comparing Net vs. Container Sampling Methods</sup>',
        xaxis_title='Year', yaxis_title='Avg Measurement (particles/m³)',
        yaxis_type='log', hovermode='x unified', template='plotly_white', height=600
    )
    fig.show()

    if not stats_container.empty and not stats_net.empty:
        max_net       = stats_net['avg_microplastics_measurement'].max()
        max_container = stats_container['avg_microplastics_measurement'].max()
        ratio         = max_container / max_net if max_net > 0 else 0
        print(f"\nMax Avg (Net): {max_net:.4f}")
        print(f"Max Avg (Container): {max_container:.4f}")
        print(f"Container methods show ~{ratio:.1f}x higher density")


def plot_method_shift(df: pd.DataFrame) -> None:
    """Plot the % of container samples over time to show the 2013 methodological shift."""
    df = df.copy()
    df['method_type'] = 'Other'
    df.loc[df['sampling_method'].str.contains('net', case=False, na=False), 'method_type'] = 'Net'
    df.loc[df['sampling_method'].str.contains(
        '|'.join(CONTAINER_KEYWORDS), case=False, na=False), 'method_type'] = 'Container'

    method_trend = df.groupby(['year', 'method_type']).size().unstack(fill_value=0)
    method_trend['Container_Pct'] = (method_trend.get('Container', 0)
                                     / (method_trend.get('Net', 0) + method_trend.get('Container', 0) + 1e-9)) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=method_trend.index, y=method_trend['Container_Pct'],
        mode='lines+markers', name='% Container Samples',
        line=dict(color='purple', width=3), fill='tozeroy'
    ))
    fig.update_layout(
        title='<b>The Shift in Sampling Methods (2006–Present)</b>'
              '<br><sup>Rise of Container Sampling explains the Density Spike</sup>',
        xaxis_title='Year', yaxis_title='% of Samples using Containers',
        template='plotly_white', height=400
    )
    fig.show()
