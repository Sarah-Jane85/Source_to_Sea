import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from components.shared import (
    load_species, load_fish_to_human, apply_global_css, page_header
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

# ── From Ocean to Plate ───────────────────────────────────────

st.markdown("---")
with open("assets/sushi_icon.svg", "r") as f:
    sushi_svg = f.read()

sushi_svg_small = sushi_svg.replace('width="800px" height="800px"', 'width="50px" height="50px"')

st.markdown("""
<div style="display:flex; align-items:center; gap:0.75rem;">
  <h3 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; margin:0;">
    From Ocean to Plate
  </h3>
  <div style="width:50px; height:50px; flex-shrink:0;">""" + sushi_svg_small + """</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#64748b;
            margin-top:0.5rem; margin-bottom:1rem; line-height:1.6;">
  Microplastic particles found per individual fish examined.<br>
  Fish consumed whole <strong style="color:#f59e0b;">(★) mean the entire plastic load
  is ingested by the consumer.</strong>
</div>
""", unsafe_allow_html=True)

fish = load_fish_to_human()
fish = fish.sort_values("mp_per_individual", ascending=True)

habitat_colors = {
    "Pelagic":  "#00d4aa",
    "Demersal": "#f59e0b",
    "Farmed":   "#ff3b5c",
}

bar_colors = [habitat_colors.get(h, "#64748b") for h in fish["habitat"]]

# Add star to consumed_whole fish
fish["label"] = fish["common_name"] + fish["consumed_whole"].apply(
    lambda x: " ★" if x else ""
)

col_fish, col_info = st.columns([3, 2], gap="large")

with col_fish:
    fig_fish = go.Figure(go.Bar(
        x=fish["mp_per_individual"],
        y=fish["label"],
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(color="#0a0e17", width=0.5),
        ),
        text=[f"{v:.1f} MPs" for v in fish["mp_per_individual"]],
        textposition="outside",
        textfont=dict(color="#64748b", size=9),
        hovertemplate="<b>%{y}</b><br>%{x:.1f} microplastic particles per individual"
                      "<br>Habitat: %{customdata[0]}"
                      "<br>Feeding: %{customdata[1]}"
                      "<br>Region: %{customdata[2]}<extra></extra>",
        customdata=fish[["habitat", "feeding_type", "region"]].values,
    ))

    fig_fish.update_layout(
        paper_bgcolor="#0a0e17",
        plot_bgcolor="#111827",
        font=dict(color="#e2e8f0"),
        title=dict(text="Microplastics per Individual Fish",
                   font=dict(color="#e2e8f0", size=14)),
        height=420,
        xaxis=dict(
            title="Microplastic particles per individual",
            gridcolor="#1f2d40",
        ),
        yaxis=dict(gridcolor="#1f2d40"),
        margin=dict(l=12, r=80, t=40, b=40),
    )
    st.plotly_chart(fig_fish, use_container_width=True)

with col_info:
    # Legend
    st.markdown("""
    <div style="background:#111827; border:1px solid #1f2d40; border-radius:6px;
                padding:1.2rem; margin-bottom:0.75rem; margin-top:-5rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#64748b;
                  letter-spacing:0.08em; margin-bottom:0.75rem;">HABITAT</div>
      <div style="display:flex; flex-direction:column; gap:0.5rem;">
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <div style="width:12px; height:12px; border-radius:2px;
                      background:#00d4aa;"></div>
          <span style="font-size:0.82rem; color:#e2e8f0;">Pelagic (open water)</span>
        </div>
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <div style="width:12px; height:12px; border-radius:2px;
                      background:#f59e0b;"></div>
          <span style="font-size:0.82rem; color:#e2e8f0;">Demersal (bottom-dwelling)</span>
        </div>
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <div style="width:12px; height:12px; border-radius:2px;
                      background:#ff3b5c;"></div>
          <span style="font-size:0.82rem; color:#e2e8f0;">Farmed</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Key findings
    st.markdown(f"""
    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #ff3b5c;
                border-radius:6px; padding:1.2rem; margin-bottom:0.75rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#64748b;
                  letter-spacing:0.08em; margin-bottom:0.5rem;">SURPRISING FINDING</div>
      <div style="font-size:0.85rem; color:#e2e8f0; line-height:1.6;">
        <strong style="color:#ff3b5c;">Farmed rainbow trout</strong> has the highest
        contamination at <strong style="color:#ff3b5c;">9.3 MPs</strong> per individual —
        more than wild-caught species. Likely from microplastic-contaminated feed
        and water in aquaculture systems.
      </div>
    </div>

    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #00d4aa;
                border-radius:6px; padding:1.2rem; margin-bottom:0.75rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#64748b;
                  letter-spacing:0.08em; margin-bottom:0.5rem;">★ CONSUMED WHOLE</div>
      <div style="font-size:0.85rem; color:#e2e8f0; line-height:1.6;">
        <strong style="color:#00d4aa;">Sardines and anchovies</strong> are typically
        eaten whole — meaning the consumer ingests 100% of the plastic load
        found in the fish, gut and all.
      </div>
    </div>

    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #64748b;
                border-radius:6px; padding:1.2rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#64748b;
                  letter-spacing:0.08em; margin-bottom:0.5rem;">SOURCES</div>
      <div style="font-size:0.75rem; color:#64748b; line-height:1.7;">
        Danopoulos et al. 2020<br>
        Frontiers Marine Science 2023<br>
        Black Sea study 2023<br>
        Iberian Peninsula study 2023
      </div>
    </div>
    """, unsafe_allow_html=True)