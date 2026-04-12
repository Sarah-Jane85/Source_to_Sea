import os
import pandas as pd
import streamlit as st

# ── Paths ─────────────────────────────────────────────────────
# shared.py lives in Streamlit/components/
# so we go up twice to reach the project root, then into Data/Clean
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLEAN_DIR = os.path.join(BASE_DIR, "Data", "Clean")

# ── Key numbers ───────────────────────────────────────────────
ANNUAL_INPUT_T        = 1_001_000
BEST_CLEANUP_T        = 28_629
BEST_CLEANUP_PCT      = 2.9
GUATEMALA_T_PER_YEAR  = 10_000
INTERCEPTORS_NEEDED   = 101
INTERCEPTORS_DEPLOYED = 19  # 17 in operation + 2 installed for testing
INTERCEPTORS_GAP      = 82
TOP_101_PCT           = 34.5
PHILIPPINES_TOP_T     = 62_592

# ── Colors ────────────────────────────────────────────────────
COLORS = {
    "teal":    "#00d4aa",
    "teal_dim":"#00856b",
    "red":     "#8b1a2d",
    "amber":   "#f59e0b",
    "bg":      "#0a0e17",
    "surface": "#111827",
    "border":  "#1f2d40",
    "text":    "#e2e8f0",
    "muted":   "#64748b",
}

# ── Data loaders ──────────────────────────────────────────────
@st.cache_data
def load_rivers():
    from shapely import wkb
    df = pd.read_parquet(os.path.join(CLEAN_DIR, "rivers_with_countries.parquet"))
    df["lon"] = df["geometry"].apply(lambda g: wkb.loads(g).x)
    df["lat"] = df["geometry"].apply(lambda g: wkb.loads(g).y)
    df = df.drop(columns=["geometry"])
    return df

@st.cache_data
def load_interceptors():
    return pd.read_parquet(os.path.join(CLEAN_DIR, "interceptors.parquet"))

@st.cache_data
def load_cleanup():
    return pd.read_parquet(os.path.join(CLEAN_DIR, "ocean_cleanup_efforts.parquet"))

@st.cache_data
def load_species():
    return pd.read_parquet(os.path.join(CLEAN_DIR, "species.parquet"))

@st.cache_data
def load_ocean_plastic():
    return pd.read_parquet(os.path.join(CLEAN_DIR, "ocean_plastic.parquet"))

@st.cache_data
def load_plastic_vs_pollution():
    return pd.read_parquet(os.path.join(CLEAN_DIR, "plastic_vs_pollution.parquet"))

def apply_global_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;800&family=DM+Sans:wght@300;400;500&family=Space+Mono&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0a0e17 !important;
        color: #e2e8f0 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    section[data-testid="stMain"] > div:first-child {
    padding-top: 0rem !important;
    }
    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1f2d40 !important;
    }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #e2e8f0 !important; line-height: 1.3 !important; }
    [data-testid="stMetricValue"] { color: #00d4aa !important; font-family: 'Syne', sans-serif !important; }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

def page_header(title, logo_svg):
    col1, col2 = st.columns([0.05, 0.95])
    with col1:
        st.markdown(f'<div style="margin-top:18px;">{logo_svg}</div>', unsafe_allow_html=True)
    with col2:
        st.title(title)
    st.markdown('<hr style="margin-top:-0.3rem; border-color:#1f2d40;">', unsafe_allow_html=True)