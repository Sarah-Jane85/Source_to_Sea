# src/q4_cleanup_impact_functions.py
# Modular functions for 05_Q4_cleanup_impact.ipynb
# Covers H1 (scale gap + growth trend) and H2 (interceptor projection)

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ── Constants ─────────────────────────────────────────────────────────────────

GUATEMALA_KG_PER_YEAR   = 10_000_000          # Rio Las Vacas, Interceptor 006
GUATEMALA_TONS_PER_YEAR = GUATEMALA_KG_PER_YEAR / 1_000

ORG_COLORS = {
    "Ocean Conservancy (ICC)": "#457B9D",
    "The Ocean Cleanup":       "#E63946",
}

COLOR_INPUT   = "#E63946"
COLOR_BEST    = "#457B9D"
COLOR_TOTAL   = "#2A9D8F"
COLOR_ACC     = "#E63946"
COLOR_CLEANUP = "#457B9D"
COLOR_COUNT   = "#aaaaaa"

FIGURES_DIR = "../Figures"


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data(config: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load microplastics, cleanup efforts, and rivers parquets.
    Returns (microplastic, df_cleanup, rivers).
    """
    microplastic = pd.read_parquet(config["output_data_modular"]["file3"])
    df_cleanup   = pd.read_parquet(config["output_data_modular"]["file8"])
    rivers       = pd.read_parquet(config["output_data_modular"]["file1"])
    return microplastic, df_cleanup, rivers


# ── H1 helpers ────────────────────────────────────────────────────────────────

def get_scale_gap_stats(df_cleanup: pd.DataFrame, rivers: pd.DataFrame) -> dict:
    """
    Calculate the scale gap between annual plastic input and cleanup removal.
    Returns dict with key metrics.
    """
    meijer_tons_per_year = rivers["emission"].sum()
    meijer_kg_per_year   = meijer_tons_per_year * 1_000

    annual = (
        df_cleanup
        .groupby("year")["kg_removed_annual"]
        .sum()
        .reset_index()
        .rename(columns={"kg_removed_annual": "kg_removed"})
    )
    annual["tons_removed"] = annual["kg_removed"] / 1_000

    best_year     = annual.loc[annual["tons_removed"].idxmax()]
    total_removed = annual["tons_removed"].sum()
    pct_best      = best_year["tons_removed"] / meijer_tons_per_year * 100
    pct_total     = total_removed / meijer_tons_per_year * 100
    years_covered = annual["year"].max() - annual["year"].min() + 1

    stats = {
        "meijer_tons_per_year": meijer_tons_per_year,
        "meijer_kg_per_year":   meijer_kg_per_year,
        "annual":               annual,
        "best_year":            best_year,
        "total_removed":        total_removed,
        "pct_best":             pct_best,
        "pct_total":            pct_total,
        "years_covered":        years_covered,
    }

    print("=== SCALE GAP ===")
    print(f"Annual plastic input (Meijer 2021) : {meijer_tons_per_year:>12,.0f} t/yr")
    print(f"Best single cleanup year ({int(best_year['year'])})  : {best_year['tons_removed']:>12,.0f} t  ({pct_best:.2f}% of input)")
    print(f"All-time total ({int(annual['year'].min())}–{int(annual['year'].max())})      : {total_removed:>12,.0f} t  ({pct_total:.2f}% of ONE year)")

    return stats


def get_annual_org_stats(df_cleanup: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Calculate annual removal by organisation, cumulative totals, and YoY growth.
    Returns (annual_org, annual_total_cumsum, yoy).
    """
    annual_org = (
        df_cleanup
        .groupby(["year", "organisation"])["kg_removed_annual"]
        .sum()
        .reset_index()
    )
    annual_org["tons_removed"] = annual_org["kg_removed_annual"] / 1_000

    annual_total        = annual_org.groupby("year")["tons_removed"].sum().reset_index()
    annual_total_cumsum = annual_total.set_index("year")["tons_removed"].cumsum()
    yoy                 = annual_total.set_index("year")["tons_removed"].pct_change() * 100

    return annual_org, annual_total_cumsum, yoy


# ── H1 plots ──────────────────────────────────────────────────────────────────

def plot_accumulation_vs_cleanup(microplastic: pd.DataFrame, df_cleanup: pd.DataFrame,
                                  save_path: str = None) -> None:
    """
    3-panel chart: avg concentration, cumulative cleanup, both indexed to 2008=100.
    Identical to H3 chart in Q2 — reproduced here for Q4 context.
    """
    df_nets = microplastic[microplastic["sampling_method"].str.contains("net", case=False, na=False)].copy()
    df_nets["year"] = pd.to_datetime(df_nets["sample_date"]).dt.year

    accumulation  = df_nets[df_nets["year"] >= 2008].groupby("year")["microplastics_measurement"].mean()
    sample_counts = df_nets[df_nets["year"] >= 2008].groupby("year").size()
    cleanup       = df_cleanup.groupby("year")["kg_removed_cumulative"].max()

    common_years = accumulation.index.intersection(cleanup.index)
    acc_norm     = accumulation[common_years] / accumulation[common_years].iloc[0] * 100
    clean_norm   = cleanup[common_years] / cleanup[common_years].iloc[0] * 100

    fig = plt.figure(figsize=(14, 9))
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 2)
    ax3 = fig.add_subplot(2, 1, 2)

    fig.suptitle("H1: Plastic Accumulation vs. Cleanup Efforts (2008–present)\nNet-based samples only",
                 fontsize=13, fontweight="bold")

    ax1b = ax1.twinx()
    ax1b.bar(sample_counts.index, sample_counts.values, color=COLOR_COUNT, alpha=0.3, label="Sample count")
    ax1b.set_ylabel("Number of samples", color=COLOR_COUNT, fontsize=8)
    ax1b.tick_params(axis="y", labelcolor=COLOR_COUNT)
    ax1.plot(accumulation.index, accumulation.values, color=COLOR_ACC, marker="o", linewidth=2, zorder=3)
    ax1.fill_between(accumulation.index, accumulation.values, alpha=0.15, color=COLOR_ACC)
    ax1.set_title("Avg Microplastic Concentration\n(net-based samples)")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Avg Concentration (pieces/m³)", color=COLOR_ACC)
    ax1.tick_params(axis="y", labelcolor=COLOR_ACC)
    lines1, _ = ax1.get_legend_handles_labels()
    lines1b, lb1 = ax1b.get_legend_handles_labels()
    ax1.legend(lines1 + lines1b, ["Avg concentration"] + lb1, loc="upper left", fontsize=7)

    ax2.fill_between(cleanup.index, cleanup.values, alpha=0.2, color=COLOR_CLEANUP)
    ax2.plot(cleanup.index, cleanup.values, color=COLOR_CLEANUP, marker="s", linewidth=2, label="Cumulative removed")
    ax2.set_title("Cumulative Plastic Removed by Cleanup\n(all organisations)")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Cumulative Plastic Removed (kg)")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M kg"))
    ax2.legend(loc="upper left", fontsize=7)

    ax3.plot(acc_norm.index, acc_norm.values, color=COLOR_ACC, marker="o", linewidth=2,
             label="Microplastic concentration (2008=100)")
    ax3.plot(clean_norm.index, clean_norm.values, color=COLOR_CLEANUP, marker="s", linewidth=2,
             label="Cumulative cleanup (2008=100)")
    ax3.fill_between(acc_norm.index, acc_norm.values, alpha=0.1, color=COLOR_ACC)
    ax3.fill_between(clean_norm.index, clean_norm.values, alpha=0.1, color=COLOR_CLEANUP)
    ax3.axhline(100, color="black", linestyle="--", linewidth=0.8, alpha=0.5, label="2008 baseline")
    ax3.set_title("Relative Growth: Concentration vs. Cleanup Effort\n(both indexed to 2008 = 100)")
    ax3.set_xlabel("Year")
    ax3.set_ylabel("Index (2008 = 100)")
    ax3.legend(loc="upper left", fontsize=9)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved → {save_path}")
    plt.show()


def plot_scale_gap(stats: dict, save: bool = True) -> go.Figure:
    """
    Two-panel bar chart: best cleanup year vs annual input, and total cumulative vs one year input.
    """
    best_year     = stats["best_year"]
    years_covered = stats["years_covered"]
    pct_best      = stats["pct_best"]
    pct_total     = stats["pct_total"]
    meijer        = stats["meijer_tons_per_year"]
    total_removed = stats["total_removed"]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            f"Best cleanup year ({int(best_year['year'])}) vs. annual input",
            f"{years_covered} years of cleanup vs. one year of input"
        ]
    )

    for val, color, label in [
        (meijer,                   COLOR_INPUT, f"Annual input<br>(Meijer 2021)<br>{meijer:,.0f} t"),
        (best_year["tons_removed"], COLOR_BEST,  f"Best year ({int(best_year['year'])})<br>{best_year['tons_removed']:,.0f} t"),
    ]:
        fig.add_trace(go.Bar(
            x=[label], y=[val],
            marker_color=color,
            text=f"{val:,.0f} t",
            textposition="outside",
            showlegend=False,
        ), row=1, col=1)

    for val, color, label in [
        (meijer,        COLOR_INPUT, f"One year of input<br>(Meijer 2021)<br>{meijer:,.0f} t"),
        (total_removed, COLOR_TOTAL, f"{years_covered}-year cleanup total<br>{total_removed:,.0f} t"),
    ]:
        fig.add_trace(go.Bar(
            x=[label], y=[val],
            marker_color=color,
            text=f"{val:,.0f} t",
            textposition="outside",
            showlegend=False,
        ), row=1, col=2)

    fig.update_yaxes(type="log", title_text="Tons (log scale)", row=1, col=1)
    fig.update_yaxes(type="log", title_text="Tons (log scale)", row=1, col=2)
    fig.update_layout(
        title=dict(
            text=(
                f"H1: The Scale Gap — Plastic Input vs. Cleanup Removed<br>"
                f"<sup>Best cleanup year removes {pct_best:.1f}% of annual input. "
                f"{years_covered} years of cleanup = {pct_total:.1f}% of ONE year's input.</sup>"
            ),
            font=dict(size=15)
        ),
        template="plotly_white",
        height=500,
        margin=dict(t=100, b=80)
    )

    if save:
        fig.write_html(f"{FIGURES_DIR}/q4_h1_scale_gap.html")
    return fig


def plot_cleanup_growth(annual_org: pd.DataFrame, annual_total_cumsum: pd.Series,
                         yoy: pd.Series, save: bool = True) -> go.Figure:
    """
    3-panel chart: stacked annual bars by org, cumulative line, YoY growth %.
    """
    orgs      = annual_org["organisation"].unique()
    all_years = sorted(annual_org["year"].unique())
    yoy_vals  = yoy.reindex(all_years).values

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[
            "Annual tons removed by organisation",
            "Cumulative tons removed",
            "Year-on-year growth (%)"
        ],
        column_widths=[0.4, 0.35, 0.25]
    )

    for org in orgs:
        org_data = (
            annual_org[annual_org["organisation"] == org]
            .set_index("year")["tons_removed"]
            .reindex(all_years, fill_value=0)
        )
        fig.add_trace(go.Bar(
            x=all_years, y=org_data.values,
            name=org,
            marker_color=ORG_COLORS.get(org, "#888888"),
        ), row=1, col=1)

    for org in orgs:
        org_data = (
            annual_org[annual_org["organisation"] == org]
            .set_index("year")["tons_removed"]
            .reindex(all_years, fill_value=0)
            .cumsum()
        )
        fig.add_trace(go.Scatter(
            x=all_years, y=org_data.values,
            name=org,
            mode="lines+markers",
            marker=dict(size=5),
            line=dict(color=ORG_COLORS.get(org, "#888888"), width=2),
            showlegend=False,
        ), row=1, col=2)

    fig.add_trace(go.Bar(
        x=all_years,
        y=yoy_vals,
        marker_color=[
            "#2A9D8F" if (v is not None and not np.isnan(v) and v >= 0) else "#E63946"
            for v in yoy_vals
        ],
        showlegend=False,
    ), row=1, col=3)

    fig.add_hline(y=0, line_color="black", line_width=0.8, row=1, col=3)
    fig.update_layout(
        barmode="stack",
        title=dict(
            text=(
                "H1: Cleanup Effort Growth Over Time (2008–2025)<br>"
                "<sup>Removal rates are accelerating — but still far below the ~1M t/yr plastic input baseline</sup>"
            ),
            font=dict(size=15)
        ),
        template="plotly_white",
        height=500,
        legend=dict(x=0.01, y=-0.15, orientation="h"),
        margin=dict(t=100, b=100)
    )
    fig.update_yaxes(title_text="Tons removed", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative tons", row=1, col=2)
    fig.update_yaxes(title_text="Growth (%)", ticksuffix="%", row=1, col=3)
    fig.update_xaxes(tickangle=45)

    if save:
        fig.write_html(f"{FIGURES_DIR}/q4_h1_cleanup_growth.html")
    return fig

# ── H2 helpers ────────────────────────────────────────────────────────────────

def get_interceptor_stats(stats: dict, annual_org: pd.DataFrame) -> dict:
    """
    Calculate interceptor projection numbers.
    Returns dict with key H2 metrics.
    """
    meijer            = stats["meijer_tons_per_year"]
    annual_total      = annual_org.groupby("year")["tons_removed"].sum().reset_index()
    current_removal   = annual_total["tons_removed"].iloc[-1]
    remaining_gap     = meijer - current_removal
    interceptors_needed      = meijer / GUATEMALA_TONS_PER_YEAR
    interceptors_to_close    = remaining_gap / GUATEMALA_TONS_PER_YEAR

    h2_stats = {
        "meijer_tons_per_year":   meijer,
        "current_removal":        current_removal,
        "remaining_gap":          remaining_gap,
        "interceptors_needed":    interceptors_needed,
        "interceptors_to_close":  interceptors_to_close,
    }

    print("=== H2: INTERCEPTOR PROJECTION ===")
    print(f"Annual plastic input (Meijer 2021)     : {meijer:>10,.0f} t/yr")
    print(f"Best interceptor benchmark (Guatemala) : {GUATEMALA_TONS_PER_YEAR:>10,.0f} t/yr")
    print(f"Current removal (latest year, all orgs): {current_removal:>10,.0f} t/yr")
    print(f"Remaining gap                          : {remaining_gap:>10,.0f} t/yr")
    print(f"")
    print(f"→ Interceptors needed to offset annual input : {interceptors_needed:.0f}")
    print(f"→ Interceptors needed to close current gap   : {interceptors_to_close:.0f}")
    print(f"→ Currently deployed                         : ~20")

    return h2_stats


def get_top_rivers(rivers: pd.DataFrame, n: int = 101) -> tuple[pd.DataFrame, float]:
    """
    Get top N rivers by emission, calculate their share of global input.
    Returns (top_n_df, pct_of_global).
    """
    top = rivers.nlargest(n, "emission").copy()
    total_emission = rivers["emission"].sum()
    pct = top["emission"].sum() / total_emission * 100
    print(f"Top {n} rivers account for {pct:.1f}% of global river plastic input")
    return top, pct


def plot_interceptor_projection(h2_stats: dict, top_rivers: pd.DataFrame,
                                 top_pct: float, save: bool = True) -> go.Figure:
    """
    3-panel chart: deployed vs needed, top 101 share, top 101 by continent.
    """
    top_by_continent = (
        top_rivers.groupby("continent")["emission"]
        .sum()
        .sort_values(ascending=True)
        .reset_index()
    )

    interceptors_needed = round(h2_stats["interceptors_needed"])
    already_deployed    = 20
    still_needed        = interceptors_needed - already_deployed

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[
            "Interceptors: deployed vs. needed",
            f"Top {interceptors_needed} rivers: share of global input",
            f"Top {interceptors_needed} rivers by continent (t/yr)"
        ],
        column_widths=[0.22, 0.30, 0.48]
    )

    fig.add_trace(go.Bar(
        x=["Deployed", "Still needed"],
        y=[already_deployed, still_needed],
        marker_color=["#2A9D8F", "#E63946"],
        text=[already_deployed, still_needed],
        textposition="outside",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=[f"Top {interceptors_needed} rivers", f"Remaining ~31,700 rivers"],
        y=[round(top_pct, 1), round(100 - top_pct, 1)],
        marker_color=["#E63946", "#d3d3d3"],
        text=[f"{top_pct:.1f}%", f"{100 - top_pct:.1f}%"],
        textposition="outside",
        showlegend=False,
    ), row=1, col=2)

    fig.add_trace(go.Bar(
        x=top_by_continent["emission"],
        y=top_by_continent["continent"],
        orientation="h",
        marker_color="#457B9D",
        text=top_by_continent["emission"].apply(lambda x: f"{x/1000:.0f}k t"),
        textposition="outside",
        showlegend=False,
    ), row=1, col=3)

    fig.update_layout(
        title=dict(
            text=(
                f"H2: ~{interceptors_needed} interceptors on the world's worst rivers would offset annual plastic input<br>"
                "<sup>87 of the top 101 rivers are in Asia — this is where deployment needs to scale fastest</sup>"
            ),
            font=dict(size=15)
        ),
        template="plotly_white",
        height=500,
        margin=dict(t=100, b=30, r=30, l=20)
    )
    fig.update_yaxes(title_text="Interceptors", row=1, col=1)
    fig.update_yaxes(title_text="% of global input", row=1, col=2)
    fig.update_xaxes(title_text="Tons/yr", tickformat=".0f", row=1, col=3)

    if save:
        fig.write_html(f"{FIGURES_DIR}/q4_h2_interceptor_projection.html")
    return fig
