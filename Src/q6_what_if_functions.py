# q6_what_if_functions.py
# Modular functions for 07_Q6_what_if_scenarios.ipynb
# Covers Q6a (deployment strategy comparison) and Q6b (growth projection)

import math
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ── Constants ─────────────────────────────────────────────────────────────────

ANNUAL_INPUT_T       = 1_001_000   # t/yr — Meijer 2021
GUATEMALA_T_PER_YEAR = 10_000      # t/yr — best performing interceptor (Rio Las Vacas)
BEST_CLEANUP_T       = 28_629      # t/yr — best recorded cleanup year (2025)
HISTORICAL_CAGR      = 0.40        # 40% — observed cleanup sector growth rate 2019-2025
PLASTIC_GROWTH       = 0.04        # 4%  — global plastic production growth (PlasticsEurope 2024)

FIGURES_DIR = "../Figures"


# ── Data preparation ──────────────────────────────────────────────────────────

def merge_income_group(rivers: pd.DataFrame, pvp: pd.DataFrame) -> pd.DataFrame:
    """
    Merge income_group from plastic_vs_pollution (file7) onto rivers dataframe.
    Rivers parquet does not contain income_group — it must be joined from pvp.

    Parameters
    ----------
    rivers : pd.DataFrame
        Rivers with countries parquet (file1).
    pvp : pd.DataFrame
        Plastic vs pollution parquet (file7), contains country + income_group.

    Returns
    -------
    pd.DataFrame
        Rivers with income_group column added.
    """
    income_lookup = (
        pvp[['country', 'income_group']]
        .drop_duplicates(subset='country')
    )
    merged = rivers.merge(income_lookup, on='country', how='left')
    nulls = merged['income_group'].isna().sum()
    if nulls > 0:
        print(f"⚠ {nulls} river mouths could not be matched to an income group.")
    return merged


# ── Q6a helpers ───────────────────────────────────────────────────────────────

def get_continent_breakdown(rivers: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate total emission and % of global input by continent.

    Parameters
    ----------
    rivers : pd.DataFrame
        Rivers dataframe with emission and continent columns.

    Returns
    -------
    pd.DataFrame
        Continent, total emission, % of global input — sorted descending.
    """
    total = rivers['emission'].sum()
    df = (
        rivers.groupby('continent')['emission']
        .sum()
        .reset_index()
        .sort_values('emission', ascending=False)
    )
    df['pct_of_global'] = (df['emission'] / total * 100).round(2)
    return df


def get_income_breakdown(rivers: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate total emission and % of global input by income group.

    Parameters
    ----------
    rivers : pd.DataFrame
        Rivers dataframe with emission and income_group columns.

    Returns
    -------
    pd.DataFrame
        Income group, total emission, % of global input — sorted descending.
    """
    total = rivers['emission'].sum()
    df = (
        rivers.groupby('income_group')['emission']
        .sum()
        .reset_index()
        .sort_values('emission', ascending=False)
    )
    df['pct_of_global'] = (df['emission'] / total * 100).round(2)
    return df


def build_strategy_comparison(
    rivers: pd.DataFrame,
    ns: list = [10, 20, 50, 100, 150, 200]
) -> pd.DataFrame:
    """
    Compare three interceptor deployment strategies across different fleet sizes.

    Strategies:
    - Global optimal: top N rivers by emission globally
    - High-income only: top N rivers in high-income countries
    - Europe only: top N rivers in European countries

    Parameters
    ----------
    rivers : pd.DataFrame
        Rivers dataframe with emission, income_group and continent columns.
    ns : list
        List of interceptor counts to evaluate.

    Returns
    -------
    pd.DataFrame
        Comparison table with % of global annual input offset per strategy.
    """
    high_income = rivers[rivers['income_group'] == 'High-income countries']
    europe      = rivers[rivers['continent']    == 'Europe']
    results     = []

    for n in ns:
        glob_n = rivers.nlargest(n, 'emission')['emission'].sum()
        hi_n   = high_income.nlargest(n, 'emission')['emission'].sum()
        eu_n   = europe.nlargest(n, 'emission')['emission'].sum()
        results.append({
            'interceptors':     n,
            'global_optimal_%': round(glob_n / ANNUAL_INPUT_T * 100, 2),
            'high_income_%':    round(hi_n   / ANNUAL_INPUT_T * 100, 2),
            'europe_%':         round(eu_n   / ANNUAL_INPUT_T * 100, 2),
        })

    return pd.DataFrame(results)


def plot_strategy_comparison(df_compare: pd.DataFrame, save: bool = True) -> go.Figure:
    """
    Plot deployment strategy comparison as grouped bar subplots —
    one subplot per interceptor count, three bars per subplot.

    Parameters
    ----------
    df_compare : pd.DataFrame
        Output of build_strategy_comparison().
    save : bool
        If True, saves figure to FIGURES_DIR.

    Returns
    -------
    go.Figure
    """
    ns = df_compare['interceptors'].tolist()

    fig = make_subplots(
        rows=1, cols=len(ns),
        subplot_titles=[f"{n} interceptors" for n in ns],
        shared_yaxes=True,
    )

    for i, n in enumerate(ns):
        row = df_compare[df_compare['interceptors'] == n].iloc[0]
        values     = [row['global_optimal_%'], row['high_income_%'], row['europe_%']]
        labels     = ['Global', 'High-income', 'Europe']
        bar_colors = ['#00d4aa', '#f59e0b', '#457B9D']

        fig.add_trace(go.Bar(
            x=labels,
            y=values,
            marker_color=bar_colors,
            text=[f"{v:.2f}%" for v in values],
            textposition='outside',
            textfont=dict(size=11),
            showlegend=False,
        ), row=1, col=i + 1)

    fig.update_layout(
        title='Q6a — Deployment strategy comparison<br>'
              '<sup>% of global annual input offset per strategy</sup>',
        height=500,
        plot_bgcolor='white',
        yaxis=dict(
            title='% of global annual input',
            ticksuffix='%',
            range=[0, 52],
            gridcolor='#eeeeee',
        ),
    )
    for i in range(1, len(ns) + 1):
        fig.update_xaxes(showgrid=False, row=1, col=i)
        fig.update_yaxes(gridcolor='#eeeeee', row=1, col=i)

    if save:
        fig.write_html(f"{FIGURES_DIR}/q6a_strategy_comparison.html")
    return fig


# ── Q6b helpers ───────────────────────────────────────────────────────────────

def years_to_parity(
    growth_rates: list,
    current_t:    float = BEST_CLEANUP_T,
    target_t:     float = ANNUAL_INPUT_T,
    base_year:    int   = 2025,
) -> pd.DataFrame:
    """
    Calculate years until cleanup tonnage reaches annual plastic input
    at different CAGR rates, assuming fixed input.

    Parameters
    ----------
    growth_rates : list
        List of annual growth rates as decimals (e.g. [0.20, 0.40]).
    current_t : float
        Current annual cleanup tonnage.
    target_t : float
        Target annual input tonnage to match.
    base_year : int
        Starting year.

    Returns
    -------
    pd.DataFrame
        CAGR, years to parity, parity year.
    """
    results = []
    for rate in growth_rates:
        yrs = math.log(target_t / current_t) / math.log(1 + rate)
        results.append({
            'cagr_%':      int(rate * 100),
            'years':       round(yrs, 1),
            'parity_year': round(base_year + yrs),
        })
    return pd.DataFrame(results)


def years_to_parity_moving_target(
    growth_rates:   list,
    plastic_growth: float = PLASTIC_GROWTH,
    current_t:      float = BEST_CLEANUP_T,
    start_input:    float = ANNUAL_INPUT_T,
    base_year:      int   = 2025,
    max_years:      int   = 100,
) -> pd.DataFrame:
    """
    Calculate parity year when both cleanup and plastic input are growing.

    Parameters
    ----------
    growth_rates : list
        Cleanup CAGR rates to evaluate.
    plastic_growth : float
        Annual growth rate of plastic input.
    current_t : float
        Current annual cleanup tonnage.
    start_input : float
        Current annual plastic input.
    base_year : int
        Starting year.
    max_years : int
        Maximum years to search before giving up.

    Returns
    -------
    pd.DataFrame
        CAGR, parity year, input at parity — or None if no parity found.
    """
    results = []
    for rate in growth_rates:
        found = False
        for yr in range(1, max_years + 1):
            cleanup_t = current_t   * (1 + rate)          ** yr
            input_t   = start_input * (1 + plastic_growth) ** yr
            if cleanup_t >= input_t:
                results.append({
                    'cagr_%':          int(rate * 100),
                    'parity_year':     base_year + yr,
                    'input_at_parity': round(input_t),
                })
                found = True
                break
        if not found:
            results.append({
                'cagr_%':          int(rate * 100),
                'parity_year':     None,
                'input_at_parity': None,
            })
    return pd.DataFrame(results)


def interceptors_needed_per_year(
    target_years: list,
    efficiency:   float = 0.5,
    current_t:    float = BEST_CLEANUP_T,
    base_year:    int   = 2025,
) -> pd.DataFrame:
    """
    Calculate how many interceptors need to be deployed per year
    to reach parity with annual plastic input by each target year.

    Parameters
    ----------
    target_years : list
        List of target years (e.g. [2030, 2035, 2040, 2050]).
    efficiency : float
        Fraction of Guatemala benchmark each interceptor achieves (0-1).
    current_t : float
        Current annual cleanup tonnage already being removed.
    base_year : int
        Current year.

    Returns
    -------
    pd.DataFrame
        Target year, years left, total interceptors needed, per year deployment rate.
    """
    gap = ANNUAL_INPUT_T - current_t
    total_needed = math.ceil(gap / (GUATEMALA_T_PER_YEAR * efficiency))
    results = []
    for target in target_years:
        years_left = target - base_year
        per_year   = math.ceil(total_needed / years_left)
        results.append({
            'target_year':      target,
            'years_left':       years_left,
            'total_interceptors': total_needed,
            'deployments_per_year': per_year,
        })
    return pd.DataFrame(results)


def plot_growth_projection(
    growth_rates:   list,
    plastic_growth: float = PLASTIC_GROWTH,
    current_t:      float = BEST_CLEANUP_T,
    start_input:    float = ANNUAL_INPUT_T,
    base_year:      int   = 2025,
    end_year:       int   = 2054,
    save:           bool  = True,
) -> go.Figure:
    """
    Plot cleanup growth trajectories vs plastic input to a target year.

    Parameters
    ----------
    growth_rates : list
        Cleanup CAGR rates to plot.
    plastic_growth : float
        Annual growth rate of plastic input.
    current_t : float
        Current annual cleanup tonnage.
    start_input : float
        Current annual plastic input.
    base_year : int
        Starting year.
    end_year : int
        End year for x-axis.
    save : bool
        If True, saves figure to FIGURES_DIR.

    Returns
    -------
    go.Figure
    """
    years_range = list(range(base_year, end_year + 1))
    colors      = ['#1f4e8c', '#457B9D', '#00d4aa', '#f59e0b']

    fig = go.Figure()

    for rate, color in zip(growth_rates, colors):
        trajectory = [current_t * (1 + rate) ** (y - base_year) for y in years_range]
        fig.add_trace(go.Scatter(
            x=years_range,
            y=trajectory,
            mode='lines',
            name=f'Cleanup at {rate*100:.0f}% CAGR',
            line=dict(color=color, width=2),
        ))

    input_trajectory = [start_input * (1 + plastic_growth) ** (y - base_year) for y in years_range]
    fig.add_trace(go.Scatter(
        x=years_range,
        y=input_trajectory,
        mode='lines',
        name=f'Plastic input ({plastic_growth*100:.0f}% growth)',
        line=dict(color='red', width=2.5, dash='dot'),
    ))

    fig.update_layout(
        title=f'Q6b — Cleanup growth vs plastic input {base_year}–{end_year}<br>'
              f'<sup>Starting point: {current_t:,} t/yr cleanup vs {start_input:,} t/yr input ({base_year})</sup>',
        xaxis=dict(title='Year', tickmode='linear', dtick=5),
        yaxis=dict(
            title='Tonnes per year',
            tickformat=',',
            gridcolor='#eeeeee',
        ),
        plot_bgcolor='white',
        height=500,
        legend=dict(x=0.01, y=0.99),
    )

    if save:
        fig.write_html(f"{FIGURES_DIR}/q6b_growth_projection.html")
    return fig
