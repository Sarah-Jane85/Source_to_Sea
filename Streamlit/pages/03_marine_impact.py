import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from components.shared import (
    load_species, apply_global_css, page_header
)

st.set_page_config(page_title="Marine Impact", page_icon="🐢", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("Marine Impact", logo_svg)

# ── Load data ─────────────────────────────────────────────────
species = load_species()

# ── KPIs ──────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

total    = len(species)
ingested = species["has_ingestion"].sum()
entangled = species["is_entangled"].sum()
groups   = species["group"].nunique()

with k1:
    st.metric("Animals Recorded", f"{total:,}")
with k2:
    st.metric("Plastic Ingestion", f"{ingested:,}", delta=f"{ingested/total*100:.1f}% of records", delta_color="off")
with k3:
    st.metric("Entanglement", f"{entangled:,}", delta=f"{entangled/total*100:.1f}% of records", delta_color="off")
with k4:
    st.metric("Species Groups", str(groups))

st.markdown("<br>", unsafe_allow_html=True)

# ── Filter ────────────────────────────────────────────────────
col_f1, col_f2 = st.columns([2, 3])
with col_f1:
    selected_group = st.selectbox(
        "Filter by species group",
        options=["All"] + sorted(species["group"].dropna().unique().tolist())
    )

filtered = species if selected_group == "All" else species[species["group"] == selected_group]

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────
col1, col2 = st.columns(2, gap="large")

with col1:
    # Ingestion rate by species group
    ingestion_by_group = (
        filtered.groupby("group")
        .agg(
            total=("has_ingestion", "count"),
            ingested=("has_ingestion", "sum")
        )
        .reset_index()
    )
    ingestion_by_group["rate"] = ingestion_by_group["ingested"] / ingestion_by_group["total"] * 100
    ingestion_by_group = ingestion_by_group[ingestion_by_group["rate"] > 0] 
    ingestion_by_group = ingestion_by_group[ingestion_by_group["total"] >= 10]  
    ingestion_by_group = ingestion_by_group.sort_values("rate", ascending=True)

    fig_ing = go.Figure(go.Bar(
        x=ingestion_by_group["rate"],
        y=ingestion_by_group["group"],
        orientation="h",
        marker=dict(color="#8b1a2d", line=dict(color="#0a0e17", width=0.5)),
        text=[f"{v:.1f}%" for v in ingestion_by_group["rate"]],
        textposition="outside",
        textfont=dict(color="#64748b", size=9),
        hovertemplate="<b>%{y}</b><br>Ingestion rate: %{x:.1f}%<extra></extra>",
    ))
    fig_ing.update_layout(
        paper_bgcolor="#0a0e17",
        plot_bgcolor="#111827",
        font=dict(color="#e2e8f0"),
        title=dict(text="Plastic Ingestion Rate by Species Group<br><sup style='color:#64748b'>% of examined animals with plastic found</sup>",
           font=dict(color="#e2e8f0", size=16)),
        height=500,
        xaxis=dict(gridcolor="#1f2d40", ticksuffix="%", range=[0, 100]),
        yaxis=dict(gridcolor="#1f2d40"),
        margin=dict(l=12, r=60, t=40, b=20),
    )
    st.plotly_chart(fig_ing, use_container_width=True)

with col2:
    # Entanglement by species group
    entangle_by_group = (
        filtered.groupby("group")
        .agg(
            total=("is_entangled", "count"),
            entangled=("is_entangled", "sum")
        )
        .reset_index()
    )
    entangle_by_group["rate"] = entangle_by_group["entangled"] / entangle_by_group["total"] * 100
    entangle_by_group = entangle_by_group[entangle_by_group["rate"] > 0]  
    entangle_by_group = entangle_by_group[entangle_by_group["total"] >= 10]  
    entangle_by_group = entangle_by_group.sort_values("rate", ascending=True)

    fig_ent = go.Figure(go.Bar(
        x=entangle_by_group["rate"],
        y=entangle_by_group["group"],
        orientation="h",
        marker=dict(color="#a66800", line=dict(color="#0a0e17", width=0.5)),
        text=[f"{v:.1f}%" for v in entangle_by_group["rate"]],
        textposition="outside",
        textfont=dict(color="#64748b", size=9),
        hovertemplate="<b>%{y}</b><br>Entanglement rate: %{x:.1f}%<extra></extra>",
    ))
    fig_ent.update_layout(
        paper_bgcolor="#0a0e17",
        plot_bgcolor="#111827",
        font=dict(color="#e2e8f0"),
        title=dict(text="Entanglement Rate by Species Group",
                   font=dict(color="#e2e8f0", size=16)),
        height=500,
        xaxis=dict(gridcolor="#1f2d40", ticksuffix="%", range=[0, 100]),
        yaxis=dict(gridcolor="#1f2d40"),
        margin=dict(l=12, r=60, t=40, b=20),
    )
    st.plotly_chart(fig_ent, use_container_width=True)

# ── Plastic type heatmap ──────────────────────────────────────
st.markdown("### Plastic Type Profile by Species Group")
st.markdown("""
<div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#64748b; margin-top:-0.5rem; margin-bottom:0.5rem;">
  % of examined animals in each group found with each plastic type
</div>
""", unsafe_allow_html=True)

plastic_cols = ["hard", "soft", "rubber", "thread", "foam",
                "net", "rope", "line", "balloon", "bag", "fisheries"]

heat_df = (
    filtered.groupby("group")[plastic_cols]
    .apply(lambda x: (x > 0).mean() * 100)
    .round(1)
)

fig_heat = go.Figure(go.Heatmap(
    z=heat_df.values,
    x=heat_df.columns.tolist(),
    y=heat_df.index.tolist(),
    zmin=0,
    zmax=100,
    colorscale=[
        [0.0, "#0d1f2d"],
        [0.3, "#00856b"],
        [0.6, "#00d4aa"],
        [1.0, "#ffffff"],
    ],
    text=None,
    texttemplate=None,
    textfont=dict(size=9, color="#e2e8f0"),
    colorbar=dict(
        title=dict(text="%", font=dict(color="#64748b", size=9)),
        tickfont=dict(color="#64748b", size=9),
        bgcolor="#111827",
        bordercolor="#1f2d40",
        thickness=12,
    ),
    hovertemplate="<b>%{y} — %{x}</b><br>%{z:.1f}%<extra></extra>",
))

fig_heat.update_layout(
    paper_bgcolor="#0a0e17",
    plot_bgcolor="#111827",
    font=dict(color="#e2e8f0"),
    height=650,
    margin=dict(l=120, r=24, t=24, b=80),
    xaxis=dict(tickangle=-30),
)
st.plotly_chart(fig_heat, use_container_width=True)

# ── Map of species observations ───────────────────────────────
st.markdown("### Species Observation Locations")

map_data = filtered.dropna(subset=["latitude", "longitude"])

fig_map = go.Figure()

color_sequence = ["#00d4aa", "#ff3b5c", "#f59e0b", "#457B9D", "#8b1a2d",
                  "#00856b", "#e2e8f0", "#64748b", "#a66800", "#003d2e",
                  "#ff8fa1", "#1a3a2a", "#3d2800", "#0a2a4a", "#1f2d40",
                  "#457B9D", "#8b1a2d", "#00d4aa", "#f59e0b", "#ff3b5c"]

for i, group in enumerate(map_data["group"].dropna().unique()):
    subset = map_data[map_data["group"] == group]
    fig_map.add_trace(go.Scattergeo(
        lat=subset["latitude"],
        lon=subset["longitude"],
        mode="markers",
        marker=dict(size=4, opacity=0.6, color=color_sequence[i % len(color_sequence)]),
        name=group,
        hovertemplate=f"<b>{group}</b><extra></extra>",
    ))

for group in map_data["group"].dropna().unique():
    subset = map_data[map_data["group"] == group]
    fig_map.add_trace(go.Scattergeo(
        lat=subset["latitude"],
        lon=subset["longitude"],
        mode="markers",
        marker=dict(size=4, opacity=0.6),
        name=group,
        hovertemplate=f"<b>{group}</b><extra></extra>",
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
    title=dict(text="Where marine plastic impact was recorded",
               font=dict(color="#e2e8f0", size=13)),
    height=400,
    margin=dict(l=0, r=0, t=36, b=0),
    font=dict(color="#e2e8f0"),
    legend=dict(bgcolor="#111827", bordercolor="#1f2d40"),
)
st.plotly_chart(fig_map, use_container_width=True)