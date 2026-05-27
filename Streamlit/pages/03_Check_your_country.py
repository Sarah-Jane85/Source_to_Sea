import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from components.shared import (
    COLORS, load_river_names, load_interceptors,
    apply_global_css, page_header
)

st.set_page_config(page_title="Explore by Country", page_icon="🗺️", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("Explore by Country", logo_svg)

# ── Load data ─────────────────────────────────────────────────
rivers       = load_river_names()
interceptors = load_interceptors()

# ── Country selector ──────────────────────────────────────────
countries_sorted = sorted(rivers["country"].unique())
default_idx = countries_sorted.index("Philippines") if "Philippines" in countries_sorted else 0
selected = st.selectbox("Select a country", options=countries_sorted, index=default_idx)

# ── Filter ────────────────────────────────────────────────────
country_rivers    = rivers[rivers["country"] == selected].copy().reset_index(drop=True)
country_intercept = interceptors[interceptors["country"] == selected]

total_input  = country_rivers["emission"].sum()
global_total = rivers["emission"].sum()
pct_global   = total_input / global_total * 100

# ── Top 3 by emission (all points, name optional) ─────────────
top3 = country_rivers.nlargest(3, "emission")[
    ["river_name", "emission", "lat", "lon"]
].reset_index(drop=True)

def display_name(row):
    name = str(row["river_name"]).strip() if row["river_name"] else ""
    if name:
        return name, False
    return f"{row['lat']:.3f}°, {row['lon']:.3f}°", True

# ── KPIs ──────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Total Plastic Input", f"{total_input:,.0f} t/yr")
with k2:
    st.metric("% of Global Input", f"{pct_global:.2f}%")
with k3:
    st.metric("River Mouths", f"{len(country_rivers):,}")
with k4:
    st.metric("Interceptors", str(len(country_intercept)))

st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)

# ── Map + Card ────────────────────────────────────────────────
col_map, col_card = st.columns([3, 2], gap="large")

with col_map:
    fig_map = go.Figure()

    fig_map.add_trace(go.Scattergeo(
        lat=country_rivers["lat"],
        lon=country_rivers["lon"],
        mode="markers",
        marker=dict(
            size=country_rivers["emission"] / country_rivers["emission"].max() * 20 + 3,
            color=country_rivers["emission"],
            colorscale=[
                [0.0, "#3d2800"],
                [0.5, "#a66800"],
                [1.0, "#f59e0b"],
            ],
            showscale=True,
            colorbar=dict(
                title=dict(text="t/yr", font=dict(color="#64748b", size=9)),
                tickfont=dict(color="#64748b", size=8),
                thickness=10, len=0.55,
                bgcolor="#111827", bordercolor="#1f2d40",
            ),
            line=dict(color="#0a0e17", width=0.5),
        ),
        hovertemplate="Emission: %{customdata:,.0f} t/yr<extra></extra>",
        customdata=country_rivers["emission"],
        name="River mouths",
    ))

    if len(country_intercept):
        fig_map.add_trace(go.Scattergeo(
            lat=country_intercept["lat"],
            lon=country_intercept["lon"],
            mode="markers",
            marker=dict(size=12, color="#00d4aa", symbol="star",
                        line=dict(color="#0a0e17", width=1)),
            text=country_intercept["river"],
            hovertemplate="<b>%{text}</b><br>Interceptor<extra></extra>",
            name="Interceptors",
        ))

    fig_map.update_layout(
        paper_bgcolor="#0a0e17",
        geo=dict(
            showframe=False, showcoastlines=True, coastlinecolor="#1f2d40",
            showland=True, landcolor="#111827",
            showocean=True, oceancolor="#0a0e17",
            showcountries=True, countrycolor="#1f2d40",
            projection_type="mercator",
            center=dict(lat=country_rivers["lat"].mean(), lon=country_rivers["lon"].mean()),
            projection_scale=4, bgcolor="#0a0e17",
        ),
        title=dict(text=f"River mouths in {selected}", font=dict(color="#e2e8f0", size=13)),
        height=420, margin=dict(l=0, r=0, t=36, b=0),
        font=dict(color="#e2e8f0"),
        legend=dict(bgcolor="#111827", bordercolor="#1f2d40"),
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_card:
    avg_emission   = country_rivers["emission"].mean()
    sorted_rivers  = country_rivers.sort_values("emission", ascending=False).copy()
    sorted_rivers["cumsum"] = sorted_rivers["emission"].cumsum()
    top_points     = (sorted_rivers["cumsum"] <= total_input * 0.8).sum() + 1
    top_points_pct = top_points / len(country_rivers) * 100

    # Interceptors string
    if len(country_intercept):
        intercept_str = "<br>".join([
            '<span style="color:#00d4aa;">●</span> ' + row["river"] + " (" + row["status"] + ")"
            for _, row in country_intercept.iterrows()
        ])
    else:
        intercept_str = '<span style="color:#8b1a2d;">None deployed</span>'

    # Build card as a list of strings, then join — avoids f-string escaping HTML
    parts = []
    parts.append(
        '<div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #f59e0b;'
        ' border-radius:6px; padding:1.4rem;">'
    )

    # Header
    parts.append(
        '<div style="font-family:\'Space Mono\',monospace; font-size:0.95rem;'
        ' color:#e2e8f0; margin-bottom:1.2rem;">'
        + selected.upper() + ' — EMISSION PROFILE</div>'
    )

    # Stats grid
    parts.append(
        '<div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-bottom:1.2rem;">'
        '<div>'
        '<div style="color:#f59e0b; font-size:1.5rem; font-weight:700;">' + f"{len(country_rivers):,}" + '</div>'
        '<div style="color:#64748b; font-size:0.8rem;">river mouths</div>'
        '</div>'
        '<div>'
        '<div style="color:#f59e0b; font-size:1.5rem; font-weight:700;">' + f"{total_input:,.0f} t" + '</div>'
        '<div style="color:#64748b; font-size:0.8rem;">total emission/yr</div>'
        '</div>'
        '<div>'
        '<div style="color:#f59e0b; font-size:1.5rem; font-weight:700;">' + f"{pct_global:.2f}%" + '</div>'
        '<div style="color:#64748b; font-size:0.8rem;">of global input</div>'
        '</div>'
        '<div>'
        '<div style="color:#f59e0b; font-size:1.5rem; font-weight:700;">' + f"{avg_emission:.1f} t" + '</div>'
        '<div style="color:#64748b; font-size:0.8rem;">avg per river mouth</div>'
        '</div>'
        '</div>'
    )

    # Concentration effect
    parts.append(
        '<div style="border-top:1px solid #1f2d40; padding-top:1rem; margin-bottom:1rem;">'
        '<div style="font-family:\'Space Mono\',monospace; font-size:0.65rem;'
        ' color:#64748b; margin-bottom:0.4rem;">CONCENTRATION EFFECT</div>'
        '<div style="color:#e2e8f0; font-size:0.85rem;">'
        '<span style="color:#f59e0b; font-weight:700;">' + f"{top_points_pct:.1f}%" + '</span>'
        ' of river mouths account for '
        '<span style="color:#f59e0b; font-weight:700;">80%</span> of emissions'
        '</div></div>'
    )

    # Top 3 section header
    parts.append(
        '<div style="border-top:1px solid #1f2d40; padding-top:1rem; margin-bottom:0.6rem;">'
        '<div style="font-family:\'Space Mono\',monospace; font-size:0.65rem;'
        ' color:#64748b; margin-bottom:0.6rem;">TOP 3 EMISSION POINTS</div>'
    )

    # River rows
    for _, row in top3.iterrows():
        label, is_fallback = display_name(row)
        name_color = "#64748b" if is_fallback else "#e2e8f0"
        name_size  = "0.75rem" if is_fallback else "0.85rem"
        emission_str = f"{row['emission']:,.0f} t/yr"
        parts.append(
            '<div style="display:flex; justify-content:space-between; align-items:center;'
            ' padding:0.45rem 0.75rem; margin-bottom:0.3rem;'
            ' background:#0a0e17; border-radius:4px; border-left:3px solid #f59e0b;">'
            '<span style="color:' + name_color + '; font-size:' + name_size + ';">' + label + '</span>'
            '<span style="color:#f59e0b; font-size:0.8rem; font-family:\'Space Mono\',monospace;'
            ' white-space:nowrap; margin-left:0.5rem;">' + emission_str + '</span>'
            '</div>'
        )

    parts.append('</div>')  # close top 3 section

    # Interceptors
    parts.append(
        '<div style="border-top:1px solid #1f2d40; padding-top:1rem;">'
        '<div style="font-family:\'Space Mono\',monospace; font-size:0.65rem;'
        ' color:#64748b; margin-bottom:0.4rem;">INTERCEPTORS</div>'
        '<div style="color:#e2e8f0; font-size:0.85rem;">' + intercept_str + '</div>'
        '</div>'
    )

    parts.append('</div>')  # close card

    st.markdown("".join(parts), unsafe_allow_html=True)
