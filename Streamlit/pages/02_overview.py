import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
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

# ── KPIs (3 cards — removed Top 101 Rivers and Top Uncovered River) ───────────
k1, k2, k3 = st.columns(3)
with k1:
    st.metric("Annual Plastic Input", f"{ANNUAL_INPUT_T:,} t", delta_color="off")
with k2:
    st.metric("Best Cleanup Year", f"{BEST_CLEANUP_T:,} t", delta="2025")
with k3:
    st.metric("Cleanup Coverage", f"{BEST_CLEANUP_PCT}%", delta="of annual input", delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────
rivers       = load_rivers()
interceptors = load_interceptors()

@st.cache_data
def load_gyres():
    import os
    BASE_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(BASE_DIR, "Data", "Clean", "marine_microplastics.parquet")
    df = pd.read_parquet(path)
    # Filter to net samples with measurements > 0
    df_nets = df[df["sampling_method"].str.contains("net", case=False, na=False)].copy()
    df_nets = df_nets[df_nets["microplastics_measurement"] > 0].copy()
    df_nets = df_nets.rename(columns={"microplastics_measurement": "concentration"})
    return df_nets

# Published plastic accumulation estimates per gyre (sourced from
# Eriksen et al. 2014 PLOS One + Ocean Cleanup 2018, in metric tonnes)
GYRE_META = pd.DataFrame({
    "gyre":     ["North Pacific", "South Pacific", "North Atlantic", "South Atlantic", "Indian Ocean"],
    "lat":      [38,  -35,  35, -32, -28],
    "lon":      [-145, -115, -55, -15,  78],
    "tonnes":   [87_000, 35_000, 1_100, 21_000, 52_000],
    "color":    ["#ff3b5c", "#f59e0b", "#a66800", "#f59e0b", "#8b1a2d"],
})

# Our measured mean concentration per gyre (from the analysis above)
GYRE_CONC = {
    "North Pacific":  1.82,
    "Indian Ocean":   1.16,
    "South Atlantic": 0.76,
    "North Atlantic": 0.33,
    "South Pacific":  0.22,
}

df_nets = load_gyres()

# Assign each point to nearest gyre
def assign_gyre(lat, lon, gyres):
    dists = np.sqrt((gyres["lat"] - lat)**2 + (gyres["lon"] - lon)**2)
    return gyres.loc[dists.idxmin(), "gyre"]

df_nets["gyre"] = df_nets.apply(
    lambda r: assign_gyre(r["lat"], r["lng"], GYRE_META), axis=1
)

@st.cache_data  
def load_all_samples():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(BASE_DIR, "Data", "Clean", "marine_microplastics.parquet")
    df = pd.read_parquet(path)
    return df.dropna(subset=["lat", "lng"]).copy()

df_all = load_all_samples()

# ── Gyre Map ───────────────────────────────────────────────────
st.markdown("### Ocean Plastic Accumulation — The 5 Gyres")
st.markdown("""
<div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#64748b;
            margin-top:-0.5rem; margin-bottom:1rem; line-height:1.6;">
  Net-tow sample measurements of floating microplastics (pieces/m³).
  Gyre markers show published accumulation estimates
  <span style="color:#464748;">(Eriksen et al. 2014; Ocean Cleanup 2018)</span>
  cross-validated against our observed concentration data.
</div>
""", unsafe_allow_html=True)

col_map, col_cards = st.columns([3, 1], gap="large")

with col_map:
    fig_gyre = go.Figure()
    # ── All samples — background density ──────────────────────────
    fig_gyre.add_trace(go.Scattergeo(
        lat=df_all["lat"],
        lon=df_all["lng"],
        mode="markers",
        marker=dict(
            size=2,
            color="#2a4a6b",
            opacity=0.4,
            line=dict(width=0),
        ),
        hoverinfo="skip",
        showlegend=False,
    ))
    # ── Net samples — concentration coloured ──────────────────────
    plot_df = df_nets.sample(min(3000, len(df_nets)), random_state=42)

    fig_gyre.add_trace(go.Scattergeo(
    lat=plot_df["lat"],
    lon=plot_df["lng"],
    mode="markers",
    marker=dict(
        size=4,
        color=plot_df["concentration"],
        colorscale=[
            [0.0,  "#1a0a2e"],
            [0.15, "#ff1744"],
            [0.4,  "#ff6b35"],
            [0.7,  "#ffd700"],
            [1.0,  "#ffffff"],
        ],
        cmax=3,
        cmin=0,
        showscale=True,
        colorbar=dict(
            title=dict(text="pieces/m³", font=dict(color="#64748b", size=9)),
            tickfont=dict(color="#64748b", size=8),
            thickness=10,
            len=0.5,
            bgcolor="#111827",
            bordercolor="#1f2d40",
        ),
        opacity=0.9,
        line=dict(width=0),
    ),
    hovertemplate="%{customdata:.3f} pieces/m³<extra></extra>",
    customdata=plot_df["concentration"],
    name="Observations",
    showlegend=False,
))

    # ── Gyre star markers ──────────────────────────────────────────
    fig_gyre.add_trace(go.Scattergeo(
        lat=GYRE_META["lat"],
        lon=GYRE_META["lon"],
        mode="markers+text",
        marker=dict(
           size=14,
            color="#00d4aa",
            symbol="star",
            line=dict(color="#0a0e17", width=1),
        ),
        text=GYRE_META["gyre"],
        textposition="top center",
        textfont=dict(color="#e2e8f0", size=9, family="Space Mono"),
        hovertemplate="<b>%{text}</b><br>~%{customdata:,} t accumulated<extra></extra>",
        customdata=GYRE_META["tonnes"],
        name="Gyres",
        showlegend=False,
        ))

    # Gyre center markers — sized by published tonnes estimate
    fig_gyre.update_layout(
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
        height=420,
        margin=dict(l=0, r=0, t=10, b=0),
        font=dict(color="#e2e8f0"),
    )
    st.plotly_chart(fig_gyre, use_container_width=True)
    st.markdown("""
    <div style="font-size:0.75rem; color:#64748b; margin-top:-0.5rem; line-height:1.6;">
     ★ marks the gyre. Dot density reflects sampling effort, not plastic volume —
     the <strong style="color:#e2e8f0;">South Pacific</strong>, 
     <strong style="color:#e2e8f0;">South Atlantic</strong> and <strong style="color:#e2e8f0;">Indian Ocean</strong> gyres are under-represented
     in our dataset due to fewer net-tow expeditions in those regions.
    </div>
    """, unsafe_allow_html=True)

with col_cards:
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#64748b;
                letter-spacing:0.1em; margin-bottom:0.75rem;">GYRE ACCUMULATION</div>
    """, unsafe_allow_html=True)

    gyre_order = ["North Pacific", "Indian Ocean", "South Pacific",
              "South Atlantic", "North Atlantic"]
    border_colors = {
        "North Pacific":  "#ff3b5c",
        "Indian Ocean":   "#8b1a2d",
        "South Atlantic": "#f59e0b",
        "South Pacific":  "#a66800",
        "North Atlantic": "#a66800",
    }

    for gyre in gyre_order:
        row = GYRE_META[GYRE_META["gyre"] == gyre].iloc[0]
        conc = GYRE_CONC.get(gyre, 0)
        bc = border_colors.get(gyre, "#1f2d40")
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #1f2d40;
                    border-left:3px solid {bc}; border-radius:6px;
                    padding:0.7rem 0.9rem; margin-bottom:0.5rem;">
          <div style="font-size:0.75rem; color:#e2e8f0; font-weight:500;
                      margin-bottom:0.2rem;">{gyre}</div>
          <div style="display:flex; justify-content:space-between; align-items:baseline;">
            <span style="color:{bc}; font-family:'Orbitron',sans-serif;
                         font-size:1rem; font-weight:700;">
              ~{row['tonnes']//1000:,}k t
            </span>
            <span style="font-family:'Space Mono',monospace; font-size:0.65rem;
                         color:#64748b;">{conc:.2f} p/m³</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.7rem; color:#64748b; margin-top:0.5rem; line-height:1.5;">
      Tonnes: published estimates.<br>
      p/m³: our observed mean<br>from net-tow samples.
    </div>
    """, unsafe_allow_html=True)

# ── Divider ────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)

# ── Country map + Interceptor status ──────────────────────────
countries = (
    rivers.groupby("country")["emission"]
    .sum()
    .reset_index()
    .rename(columns={"emission": "total_emission"})
    .sort_values("total_emission", ascending=False)
)

col_map2, col_right = st.columns([2, 2], gap="large")

with col_map2:
    fig_map = go.Figure()

    fig_map.add_trace(go.Choropleth(
        locations=countries["country"],
        locationmode="country names",
        z=countries["total_emission"],
        colorscale=[
            [0.0, "#111827"],
            [0.2, "#7a3500"],
            [0.5, "#c45200"],
            [0.8, "#f59e0b"],
            [1.0, "#ffd700"],
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
        title=dict(text="Plastic Input by Country<br><sup>Teal dots = interceptors</sup>",
                   font=dict(color="#e2e8f0", size=16)),
        height=500,
        margin=dict(l=0, r=0, t=36, b=0),
        legend=dict(bgcolor="#111827", bordercolor="#1f2d40", font=dict(color="#e2e8f0")),
        font=dict(color="#e2e8f0"),
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_right:
    # Interceptor status card
    st.markdown(f"""
    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #00d4aa;
                border-radius:6px; padding:1.2rem; margin-bottom:1rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#64748b;
                  margin-bottom:0.75rem; letter-spacing:0.08em;">INTERCEPTOR STATUS</div>
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
        title=dict(text="Top 5 Plastic Emitting Countries",
                   font=dict(color="#e2e8f0", size=16)),
        height=300,
        xaxis=dict(gridcolor="#1f2d40", tickformat=","),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=12, r=60, t=40, b=20),
    )
    st.plotly_chart(fig_bar, use_container_width=True)
