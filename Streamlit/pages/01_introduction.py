import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from components.shared import apply_global_css, page_header

st.set_page_config(page_title="Introduction", page_icon="🌊", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("Source to Sea", logo_svg)

# ── Intro ──────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'DM Sans',sans-serif; font-size:1rem; color:#64748b;
            max-width:900px; line-height:1.8; margin-bottom:2rem;">
  Every year, <strong style="color:#e2e8f0;">1,001,000 tonnes</strong> of plastic
  enters the world's oceans — not in one catastrophic event, but bottle by bottle,
  bag by bag, through rivers and coastlines across the globe.
  <br><br>
  <strong style="color:#e2e8f0;">Source to Sea</strong> is an ocean plastic analysis
  dashboard built to trace that journey: from the rivers that carry plastic into the sea,
  through the gyres where it accumulates, to the marine animals and ultimately the humans
  who are affected — and the organisations working to stop it.
</div>
""", unsafe_allow_html=True)

# ── Hero images ────────────────────────────────────────────────
col1, col2, col3 = st.columns(3, gap="medium")
with col1:
    st.image("assets/garbage_patch.jpg", use_container_width=True)
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#64748b;
                text-align:center; margin-top:0.4rem;">
    A plastic garbage patch in the ocean
    </div>""", unsafe_allow_html=True)
with col2:
    st.image("assets/turtle1.jpg", use_container_width=True)
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#64748b;
                text-align:center; margin-top:0.4rem;">
    Sea turtle ingesting a plastic bag
    </div>""", unsafe_allow_html=True)
with col3:
    st.image("assets/inceptors.jpg", use_container_width=True)
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#64748b;
                text-align:center; margin-top:0.4rem;">
    The Ocean Cleanup Interceptor concept
    </div>""", unsafe_allow_html=True)

# ── What this dashboard covers ────────────────────────────────
st.markdown("""
<div style="font-family:'Space Mono',monospace; font-size:1rem; color:#00d4aa;
            letter-spacing:0.15em; margin-bottom:1.5rem;">WHAT THIS DASHBOARD COVERS</div>
""", unsafe_allow_html=True)

pages = [
    ("🌊", "Global Overview",
     "Key numbers, a world map of plastic input by country, ocean gyre accumulation and interceptor deployment status.",
     "#00d4aa"),
    ("🗺️", "Explore by Country",
     "Drill down into any country's river plastic emissions, top emission points and interceptor coverage.",
     "#00d4aa"),
    ("🐋", "Animal Impact",
     "How plastic kills — sea turtles, whales, seals, seahorses and fish. The species, the mechanisms, the scale.",
     "#ff3b5c"),
    ("🐢", "Marine Impact",
     "Data-driven analysis of plastic ingestion and entanglement rates across species groups, with a fish-to-human chain.",
     "#ff3b5c"),
    ("🧹", "Cleanup Information",
     "Three ways to stop plastic: land cleanups, beach cleanups and river interceptors — how they work and why they matter.",
     "#f59e0b"),
    ("📊", "Cleanup Progress",
     "Year-by-year removal data from The Ocean Cleanup and Ocean Conservancy — how much has been recovered and how fast the sector is growing.",
     "#f59e0b"),
    ("🎯", "Where to Act",
     "The top 500 emission river mouths mapped globally, continent breakdown and interceptor deployment gaps.",
     "#f59e0b"),
    ("💡", "What If?",
     "A scenario modeller: slide to change the number of interceptors and their efficiency to see how much of the annual input could be offset.",
     "#00d4aa"),
    ("💪", "Take Action",
     "Cleanup events, donation links and initiatives worldwide — from Barcelona to Vietnam, Guatemala to Ghana.",
     "#00d4aa"),
]

# Row 1: cards 0,1,2 with → between, then ↓ on right
# Row 2: cards 3,4,5 with ← between (reverse direction), then ↓ on left  
# Row 3: cards 6,7,8 with → between

def card_html(icon, title, desc, color):
    return f"""
    <div style="background:#111827; border:1px solid #1f2d40;
                border-left:3px solid {color}; border-radius:8px;
                padding:1.2rem 1.4rem; height:160px;">
      <div style="font-size:1.2rem; margin-bottom:0.4rem;">{icon}</div>
      <div style="font-family:'Orbitron',sans-serif; font-size:0.8rem;
                  color:#e2e8f0; margin-bottom:0.5rem;">{title}</div>
      <div style="font-family:'DM Sans',sans-serif; font-size:0.77rem;
                  color:#64748b; line-height:1.5;">{desc}</div>
    </div>"""

def arrow_h(direction="→"):
    return f"""<div style="display:flex; align-items:center; justify-content:center;
                height:160px; color:#00d4aa; font-size:1.8rem;">{direction}</div>"""

def arrow_v(direction="↓"):
    return f"""<div style="text-align:{'right' if direction == '↓r' else 'left'};
                color:#00d4aa; font-size:1.8rem; padding: 0.2rem 1rem;">{direction}</div>"""

# ── Row 1 — left to right ──────────────────────────────────────
c1, a1, c2, a2, c3 = st.columns([5, 1, 5, 1, 5], gap="small")
with c1: st.markdown(card_html(*pages[0]), unsafe_allow_html=True)
with a1: st.markdown(arrow_h("→"), unsafe_allow_html=True)
with c2: st.markdown(card_html(*pages[1]), unsafe_allow_html=True)
with a2: st.markdown(arrow_h("→"), unsafe_allow_html=True)
with c3: st.markdown(card_html(*pages[2]), unsafe_allow_html=True)

# Down arrow on the right
_, _, _, _, a_down1 = st.columns([5, 1, 5, 1, 5], gap="small")
with a_down1: st.markdown(arrow_v("↓"), unsafe_allow_html=True)

# ── Row 2 — right to left ─────────────────────────────────────
c4, a3, c5, a4, c6 = st.columns([5, 1, 5, 1, 5], gap="small")
with c4: st.markdown(card_html(*pages[5]), unsafe_allow_html=True)
with a3: st.markdown(arrow_h("←"), unsafe_allow_html=True)
with c5: st.markdown(card_html(*pages[4]), unsafe_allow_html=True)
with a4: st.markdown(arrow_h("←"), unsafe_allow_html=True)
with c6: st.markdown(card_html(*pages[3]), unsafe_allow_html=True)

# Down arrow on the left
a_down2, _, _, _, _ = st.columns([5, 1, 5, 1, 5], gap="small")
with a_down2: st.markdown(arrow_v("↓"), unsafe_allow_html=True)

# ── Row 3 — left to right ─────────────────────────────────────
c7, a5, c8, a6, c9 = st.columns([5, 1, 5, 1, 5], gap="small")
with c7: st.markdown(card_html(*pages[6]), unsafe_allow_html=True)
with a5: st.markdown(arrow_h("→"), unsafe_allow_html=True)
with c8: st.markdown(card_html(*pages[7]), unsafe_allow_html=True)
with a6: st.markdown(arrow_h("→"), unsafe_allow_html=True)
with c9: st.markdown(card_html(*pages[8]), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)


# ── Datasets ───────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Space Mono',monospace; font-size:1rem; color:#00d4aa;
            letter-spacing:0.15em; margin-bottom:1.5rem;">DATA SOURCES</div>
""", unsafe_allow_html=True)

datasets = [
    (
        "rivers_with_countries.parquet",
        "Meijer et al. 2021 — PNAS",
        "31,819 river mouth emission points with lat/lon coordinates and estimated plastic output in tonnes/year. The most comprehensive global river plastic dataset available.",
        "https://figshare.com/articles/dataset/Supplementary_data_for_More_than_1000_rivers_account_for_80_of_global_riverine_plastic_emissions_into_the_ocean_/14515590",
        "#f59e0b",
    ),
    (
        "marine_microplastics.parquet",
        "NOAA National Centers for Environmental Information",
        "13,000+ net-tow and water sample measurements of floating microplastic concentration (pieces/m³) from ocean expeditions worldwide, spanning 1972–present.",
        "https://www.ncei.noaa.gov/products/microplastics",
        "#00d4aa",
    ),
    (
        "ocean_plastic.parquet",
        "Our World in Data — Plastic Waste Accumulated in Oceans",
        "Country-level estimates of cumulative plastic waste accumulated in the ocean over time, derived from mismanaged waste and coastal population data.",
        "https://ourworldindata.org/grapher/plastic-waste-accumulated-in-oceans",
        "#00d4aa",
    ),
    (
        "plastic_generation.parquet + plastic_vs_pollution.parquet",
        "Our World in Data — Plastic Pollution",
        "Annual plastic generation by country (tonnes) and plastic waste vs pollution metrics including mismanaged waste rates and income group breakdowns.",
        "https://ourworldindata.org/plastic-pollution",
        "#00d4aa",
    ),
    (
        "species.parquet",
        "Wilcox et al. 2015 — Science (aaz5803)",
        "10,412 marine animal records across species groups with plastic ingestion, entanglement and plastic type data. Used for the Marine Impact analysis.",
        "https://www.science.org/doi/10.1126/science.aaz5803",
        "#ff3b5c",
    ),
    (
        "ocean_cleanup_efforts.parquet",
        "The Ocean Cleanup + Ocean Conservancy (ICC)",
        "Manually compiled annual cleanup removal data (kg) for The Ocean Cleanup and International Coastal Cleanup (ICC/Ocean Conservancy), sourced from published annual reports and website data.",
        "https://theoceancleanup.com",
        "#ff3b5c",
    ),
    (
        "interceptors.parquet",
        "The Ocean Cleanup — manually curated",
        "22 interceptor deployments with location, river, city, country, year deployed, type and operational status. Built from The Ocean Cleanup's published deployment data and media gallery.",
        "https://theoceancleanup.com/rivers/",
        "#ff3b5c",
    ),
    (
        "fish_to_human.parquet",
        "Danopoulos et al. 2020 + 3 regional studies",
        "Manually curated dataset of microplastic particles per individual for 10 commercially consumed fish species. Sources: Danopoulos et al. 2020, Frontiers Marine Science 2023, Black Sea study 2023, Iberian Peninsula study 2023.",
        "https://www.sciencedirect.com/science/article/pii/S0160412020319698",
        "#f59e0b",
    ),
    (
        "top50_rivers_ranked.parquet",
        "Derived — Meijer et al. 2021",
        "Top 50 river emission points ranked by plastic output, derived from rivers_with_countries. Used for the Where to Act priority analysis.",
        "https://figshare.com/articles/dataset/Supplementary_data_for_More_than_1000_rivers_account_for_80_of_global_riverine_plastic_emissions_into_the_ocean_/14515590",
        "#f59e0b",
    ),
]

for name, source, desc, url, color in datasets:
    st.markdown(f"""
    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid {color};
                border-radius:8px; padding:1.1rem 1.4rem; margin-bottom:0.75rem;
                display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
      <div style="flex:1;">
        <div style="display:flex; align-items:baseline; gap:0.75rem; margin-bottom:0.3rem;">
          <span style="font-family:'Space Mono',monospace; font-size:0.75rem;
                       color:{color}; font-weight:700;">{name}</span>
        </div>
        <div style="font-family:'Orbitron',sans-serif; font-size:0.72rem;
                    color:#e2e8f0; margin-bottom:0.4rem;">{source}</div>
        <div style="font-family:'DM Sans',sans-serif; font-size:0.8rem;
                    color:#64748b; line-height:1.6;">{desc}</div>
      </div>
      <div style="flex-shrink:0; padding-top:0.2rem;">
        <a href="{url}" target="_blank"
           style="background:{color}22; border:1px solid {color}; color:{color};
                  padding:0.3rem 0.7rem; border-radius:4px; font-family:'Space Mono',monospace;
                  font-size:0.62rem; text-decoration:none; white-space:nowrap;">SOURCE →</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="font-size:0.75rem; color:#1f2d40; text-align:center; font-family:'Space Mono',monospace;">
  Built with Python · Streamlit · Plotly · Pandas · Source to Sea · 2025
</div>
""", unsafe_allow_html=True)
