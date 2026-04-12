import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from components.shared import (
    ANNUAL_INPUT_T, BEST_CLEANUP_T, BEST_CLEANUP_PCT,
    INTERCEPTORS_DEPLOYED, INTERCEPTORS_NEEDED, INTERCEPTORS_GAP,
    TOP_101_PCT, PHILIPPINES_TOP_T,
    COLORS, load_rivers, load_interceptors,
    apply_global_css, page_header
)

st.set_page_config(page_title="Overview", page_icon="🌊", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("Global Overview", logo_svg)

# ── KPIs ──────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Annual Plastic Input", f"{ANNUAL_INPUT_T:,} t", delta_color="off")
with k2:
    st.metric("Best Cleanup Year", f"{BEST_CLEANUP_T:,} t", delta="2025")
with k3:
    st.metric("Cleanup Coverage", f"{BEST_CLEANUP_PCT}%", delta="of annual input", delta_color="off")
with k4:
    st.metric("Top 101 Rivers", f"{TOP_101_PCT}%", delta="of global input", delta_color="off")
with k5:
    st.metric("Top Uncovered River", f"{PHILIPPINES_TOP_T:,} t/yr", delta="Philippines", delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────
rivers      = load_rivers()
interceptors = load_interceptors()

# Aggregate by country for choropleth
countries = (
    rivers.groupby("country")["emission"]
    .sum()
    .reset_index()
    .rename(columns={"emission": "total_emission"})
    .sort_values("total_emission", ascending=False)
)

# ── Map + Donut ───────────────────────────────────────────────
col_map, col_donut = st.columns([3, 2], gap="large")

with col_map:
    fig_map = go.Figure()

    fig_map.add_trace(go.Choropleth(
        locations=countries["country"],
        locationmode="country names",
        z=countries["total_emission"],
        colorscale=[
            [0.0, "#0a0e17"],
            [0.3, "#3d2800"],
            [0.6, "#a66800"],
            [1.0, "#f59e0b"],
        ],
        marker_line_color="#1f2d40",
        marker_line_width=0.5,
        colorbar=dict(
            title=dict(text="t/yr", font=dict(color="#64748b", size=10)),
            tickfont=dict(color="#64748b", size=9),
            bgcolor="#111827",
            bordercolor="#1f2d40",
            borderwidth=1,
            thickness=12,
            len=0.6,
        ),
        hovertemplate="<b>%{location}</b><br>%{z:,.0f} t/yr<extra></extra>",
    ))

    fig_map.add_trace(go.Scattergeo(
        lat=interceptors["lat"],
        lon=interceptors["lon"],
        mode="markers",
        marker=dict(size=8, color="#00d4aa", symbol="circle",
                    line=dict(color="#0a0e17", width=1)),
        name="Interceptors",
        hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>",
        text=interceptors["name"] if "name" in interceptors.columns else interceptors["river"],
        customdata=interceptors["country"],
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
        title=dict(text="Plastic Input by Country · Teal dots = interceptors",
                   font=dict(color="#e2e8f0", size=13)),
        height=420,
        margin=dict(l=0, r=0, t=36, b=0),
        legend=dict(bgcolor="#111827", bordercolor="#1f2d40", font=dict(color="#e2e8f0")),
        font=dict(color="#e2e8f0"),
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_donut:
    st.markdown(f"""
    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #00d4aa;
                border-radius:6px; padding:1.2rem; margin-bottom:1rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#64748b; margin-bottom:0.75rem;">
        INTERCEPTOR STATUS
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem;">
        <div>
          <div style="color:#00d4aa; font-size:1.6rem; font-weight:700;">19</div>
          <div style="color:#64748b; font-size:0.8rem;">deployed</div>
        </div>
        <div>
          <div style="color:#ff3b5c; font-size:1.6rem; font-weight:700;">82</div>
          <div style="color:#64748b; font-size:0.8rem;">still needed</div>
        </div>
        <div>
          <div style="color:#f59e0b; font-size:1.6rem; font-weight:700;">101</div>
          <div style="color:#64748b; font-size:0.8rem;">target total</div>
        </div>
        <div>
          <div style="color:#e2e8f0; font-size:1.6rem; font-weight:700;">2.9%</div>
          <div style="color:#64748b; font-size:0.8rem;">cleaned / 34.5% coverable</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

     # Top 5 countries bar
    top5 = countries.head(5)
    fig_bar = go.Figure(go.Bar(
        x=top5["total_emission"],
        y=top5["country"],
        orientation="h",
        marker=dict(color="#8b1a2d", line=dict(color="#0a0e17", width=0.5)),
        text=[f"{v/1000:.0f}k t" for v in top5["total_emission"]],
        textposition="outside",
        textfont=dict(color="#64748b", size=9),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} t/yr<extra></extra>",
    ))
    fig_bar.update_layout(
        paper_bgcolor="#0a0e17",
        plot_bgcolor="#111827",
        font=dict(color="#e2e8f0"),
        title=dict(text="Top 5 Plastic Emitting Countries", font=dict(color="#e2e8f0", size=13)),
        height=220,
        xaxis=dict(gridcolor="#1f2d40", tickformat=","),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=12, r=60, t=40, b=20),
    )
    st.plotly_chart(fig_bar, use_container_width=True)