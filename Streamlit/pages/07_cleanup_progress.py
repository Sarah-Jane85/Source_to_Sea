import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from components.shared import (
    ANNUAL_INPUT_T, BEST_CLEANUP_T, BEST_CLEANUP_PCT,
    COLORS, load_cleanup, apply_global_css, page_header
)

st.set_page_config(page_title="Cleanup Progress", page_icon="🧹", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("Cleanup Progress", logo_svg)

st.set_page_config(page_title="Cleanup Progress", page_icon="🧹", layout="wide")

# ── Load data ─────────────────────────────────────────────────
df = load_cleanup()

# Annual totals across both organisations
annual = (
    df.groupby("year")["kg_removed_annual"]
    .sum()
    .reset_index()
)
annual["tonnes"] = annual["kg_removed_annual"] / 1000

# ── KPIs ──────────────────────────────────────────────────────
with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

k1, k2, k3, k4 = st.columns(4)
best = annual.loc[annual["tonnes"].idxmax()]
prev = annual.iloc[-2]["tonnes"]
curr = annual.iloc[-1]["tonnes"]
yoy  = (curr - prev) / prev * 100

with k1:
    st.metric("Best Year", f"{int(best['tonnes']):,} t", delta=f"{int(best['year'])}")
with k2:
    st.metric("Year-on-Year Growth", f"+{yoy:.1f}%", delta="vs previous year")
with k3:
    st.metric("% of Annual Input", f"{BEST_CLEANUP_PCT}%", delta="2025")
with k4:
    st.metric("Annual Plastic Input", f"{ANNUAL_INPUT_T:,} t", delta_color="off")

# ── Divider ────────────────────────────────────────────────────
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
# ── Line chart ────────────────────────────────────────────────
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=annual["year"],
    y=annual["tonnes"],
    mode="lines+markers",
    line=dict(color="#00d4aa", width=2.5),
    marker=dict(size=6, color="#00d4aa", line=dict(color="#0a0e17", width=1)),
    fill="tozeroy",
    fillcolor="rgba(0,212,170,0.08)",
    hovertemplate="<b>%{x}</b><br>%{y:,.0f} t removed<extra></extra>",
))

fig.add_hline(
    y=ANNUAL_INPUT_T,
    line=dict(color="#ff3b5c", width=1.5, dash="dot"),
    annotation_text=f"Annual input: {ANNUAL_INPUT_T:,} t/yr",
    annotation_font=dict(color="#ff3b5c", size=11),
)

fig.update_layout(
    paper_bgcolor="#0a0e17",
    plot_bgcolor="#111827",
    font=dict(color="#e2e8f0"),
    title="Annual Tonnes Removed — All Organisations",
    height=380,
    xaxis=dict(title="Year", gridcolor="#1f2d40", tickmode="linear", dtick=1),
    yaxis=dict(title="Tonnes Removed", gridcolor="#1f2d40", tickformat=",", type="log"),
    margin=dict(l=48, r=24, t=48, b=48),
)

st.plotly_chart(fig, use_container_width=True)

# ── Stacked bar by organisation ───────────────────────────────
st.markdown("### By Organisation")

org_colors = {
    "The Ocean Cleanup":       "#00d4aa",
    "Ocean Conservancy (ICC)": "#457B9D",
}

fig2 = go.Figure()
for org in df["organisation"].unique():
    org_data = (
        df[df["organisation"] == org]
        .groupby("year")["kg_removed_annual"]
        .sum() / 1000
    ).reset_index()
    org_data.columns = ["year", "tonnes"]

    fig2.add_trace(go.Bar(
        name=org,
        x=org_data["year"],
        y=org_data["tonnes"],
        marker=dict(color=org_colors.get(org, "#64748b")),
        hovertemplate="<b>%{x}</b><br>" + org + ": %{y:,.0f} t<extra></extra>",
    ))

fig2.update_layout(
    barmode="stack",
    paper_bgcolor="#0a0e17",
    plot_bgcolor="#111827",
    font=dict(color="#e2e8f0"),
    title="Cleanup by Organisation (stacked)",
    height=340,
    xaxis=dict(gridcolor="#1f2d40", tickmode="linear", dtick=1),
    yaxis=dict(title="Tonnes", gridcolor="#1f2d40", tickformat=","),
    legend=dict(bgcolor="#111827", bordercolor="#1f2d40", borderwidth=1),
    margin=dict(l=48, r=24, t=48, b=48),
)

st.plotly_chart(fig2, use_container_width=True)
