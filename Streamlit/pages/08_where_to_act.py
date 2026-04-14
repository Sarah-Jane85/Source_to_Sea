import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from components.shared import (
    ANNUAL_INPUT_T, INTERCEPTORS_DEPLOYED, INTERCEPTORS_NEEDED,
    INTERCEPTORS_GAP, GUATEMALA_T_PER_YEAR, PHILIPPINES_TOP_T,
    TOP_101_PCT, COLORS, load_rivers, load_interceptors,
    apply_global_css, page_header
)

st.set_page_config(page_title="Where to Act", page_icon="🎯", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("Where to Act", logo_svg)

# ── Load data ─────────────────────────────────────────────────
rivers       = load_rivers()
interceptors = load_interceptors()

total_emission = rivers["emission"].sum()

# Top 101 uncovered rivers
covered_lats = interceptors["lat"].tolist()
covered_lons = interceptors["lon"].tolist()

# Get top rivers by emission
top_rivers = rivers.nlargest(500, "emission").copy()

# ── KPIs ──────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Top 101 Rivers", f"{TOP_101_PCT}%",
              delta="of global input", delta_color="off")
with k2:
    st.metric("Guatemala Benchmark", f"{GUATEMALA_T_PER_YEAR:,} t/yr",
              delta="per interceptor", delta_color="off")
with k3:
    st.metric("Interceptors Deployed", f"{INTERCEPTORS_DEPLOYED} / {INTERCEPTORS_NEEDED}")
with k4:
    st.metric("Still Needed", str(INTERCEPTORS_GAP), delta_color="inverse")    
with k5:
    st.metric("Top River (Philippines)", f"{PHILIPPINES_TOP_T:,} t/yr",
              delta="uncovered", delta_color="inverse")

# ── Map ───────────────────────────────────────────────────────
fig_map = go.Figure()

# Top uncovered rivers as bubbles
fig_map.add_trace(go.Scattergeo(
    lat=top_rivers["lat"],
    lon=top_rivers["lon"],
    mode="markers",
    marker=dict(
        size=top_rivers["emission"] / top_rivers["emission"].max() * 40 + 3,
        color=top_rivers["emission"],
        colorscale=[
            [0.0, "#a66800"],
            [0.5, "#f59e0b"],
            [1.0, "#ffffff"],
        ],

        showscale=True,
        colorbar=dict(
            title=dict(text="t/yr", font=dict(color="#64748b", size=9)),
            tickfont=dict(color="#64748b", size=9),
            thickness=10,
            len=0.5,
            bgcolor="#111827",
            bordercolor="#1f2d40",
        ),
        line=dict(color="#0a0e17", width=0.5),
        opacity=1.0,
    ),
    hovertemplate="<b>%{text}</b><br>%{customdata:,.0f} t/yr<extra></extra>",
    text=top_rivers["country"],
    customdata=top_rivers["emission"],
    name="High emission rivers",
))

# Deployed interceptors as stars
fig_map.add_trace(go.Scattergeo(
    lat=interceptors["lat"],
    lon=interceptors["lon"],
    mode="markers",
    marker=dict(
        size=12,
        color="#00d4aa",
        symbol="star",
        line=dict(color="#0a0e17", width=1),
    ),
    hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>",
    text=interceptors["river"],
    customdata=interceptors["country"],
    name="Deployed interceptors",
))

fig_map.update_layout(
    paper_bgcolor="#0a0e17",
    geo=dict(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#1f2d40",
        showland=True,
        landcolor="#111827",
        showocean=True,
        oceancolor="#0a0e17",
        showcountries=True,
        countrycolor="#1f2d40",
        projection_type="natural earth",
        bgcolor="#0a0e17",
    ),
    title=dict(text="Top emission river mouths · Stars = deployed interceptors",
               font=dict(color="#e2e8f0", size=13)),
    height=500,
    margin=dict(l=0, r=0, t=36, b=0),
    font=dict(color="#e2e8f0"),
    legend=dict(bgcolor="#111827", bordercolor="#1f2d40", x=0.01, y=0.99),
)
st.plotly_chart(fig_map, use_container_width=True)

# ── Top uncovered by country ──────────────────────────────────
st.markdown("---")
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### Top 10 Countries by Emission")
    top_countries = (
        rivers.groupby("country")["emission"]
        .sum()
        .reset_index()
        .nlargest(10, "emission")
        .sort_values("emission", ascending=True)
    )

    fig_countries = go.Figure(go.Bar(
        x=top_countries["emission"],
        y=top_countries["country"],
        orientation="h",
        marker=dict(color="#8b1a2d", line=dict(color="#0a0e17", width=0.5)),
        text=[f"{v/1000:.0f}k t" for v in top_countries["emission"]],
        textposition="outside",
        textfont=dict(color="#64748b", size=9),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} t/yr<extra></extra>",
    ))
    fig_countries.update_layout(
        paper_bgcolor="#0a0e17",
        plot_bgcolor="#111827",
        font=dict(color="#e2e8f0"),
        height=360,
        xaxis=dict(gridcolor="#1f2d40", tickformat=","),
        yaxis=dict(gridcolor="#1f2d40"),
        margin=dict(l=12, r=60, t=20, b=20),
    )
    st.plotly_chart(fig_countries, use_container_width=True)

with col2:
    st.markdown("### Interceptor Coverage by Country")
    intercept_countries = (
        interceptors.groupby("country")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )

    fig_intercept = go.Figure(go.Bar(
        x=intercept_countries["count"],
        y=intercept_countries["country"],
        orientation="h",
        marker=dict(color="#00856b", line=dict(color="#0a0e17", width=0.5)),
        text=intercept_countries["count"],
        textposition="outside",
        textfont=dict(color="#64748b", size=9),
        hovertemplate="<b>%{y}</b><br>%{x} interceptors<extra></extra>",
    ))
    fig_intercept.update_layout(
        paper_bgcolor="#0a0e17",
        plot_bgcolor="#111827",
        font=dict(color="#e2e8f0"),
        height=360,
        xaxis=dict(gridcolor="#1f2d40"),
        yaxis=dict(gridcolor="#1f2d40"),
        margin=dict(l=12, r=40, t=20, b=20),
    )
    st.plotly_chart(fig_intercept, use_container_width=True)