import streamlit as st
import os
st.set_page_config(
    page_title="Source to Sea",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&family=Space+Mono&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #014654 !important;
    color: #e2e8f0 !important;
    font-family:'Orbitron',sans-serif;
}
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding-top: 0rem !important;
}
[data-testid="stSidebar"] {
    background-color: #111827 !important;
    border-right: 1px solid #1f2d40 !important;
}
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: #e2e8f0 !important;
}
[data-testid="metric-container"] {
    background: #111827 !important;
    border: 1px solid #1f2d40 !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}
[data-testid="stMetricValue"] {
    color: #00d4aa !important;
    font-family: 'Syne', sans-serif !important;
}
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Landing page ──────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    img_path = os.path.join(os.path.dirname(__file__), "assets", "logo.svg")
    st.image(img_path, width=1500, use_container_width=False)

st.markdown("""
<div style="display:flex; flex-direction:column; align-items:center;
            text-align:center; gap:0.5rem; margin-top:-11rem;">
  <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:4.5rem;
              color:#e2e8f0; letter-spacing:-0.03em;">
    Source to Sea
  </div>
  <div style="font-family:'Space Mono',monospace; font-size:1.5rem;
              color:#00d4aa; letter-spacing:0.15em;">
    OCEAN PLASTIC ANALYSIS<br> built to inform — and to call to action!
  </div>
  <div style="color:#ccc7c7; max-width:480px; line-height:1.6; font-size:1.2rem; margin-top:0.5rem;">
    Tracking <strong style="color:#e2e8f0;">1,006,000 t/yr</strong> of ocean-bound
    plastic from river source to marine impact.
  </div>
  <div style="font-family:'Space Mono',monospace; font-size:0.85rem;
              color:#64748b; margin-top:0.5rem;">
    ← Select a page from the sidebar
  </div>
</div>
""", unsafe_allow_html=True)

# ── Navigation ──────────────────────────────────────────────
PAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")

pg = st.navigation([
    st.Page(os.path.join(PAGES_DIR, "01_Introduction.py"), title="Introduction"),
    st.Page(os.path.join(PAGES_DIR, "02_State_of_the_World.py"), title="State of the World"),
    st.Page(os.path.join(PAGES_DIR, "03_Check_your_country.py"), title="Check your country"),
    st.Page(os.path.join(PAGES_DIR, "04_Animal_impact.py"), title="Animal impact"),
    st.Page(os.path.join(PAGES_DIR, "05_Marine_impact.py"), title="Marine impact"),
    st.Page(os.path.join(PAGES_DIR, "06_Cleanup_information.py"), title="Cleanup information"),
    st.Page(os.path.join(PAGES_DIR, "07_Cleanup_progress.py"), title="Cleanup progress"),
    st.Page(os.path.join(PAGES_DIR, "08_Where_to_act.py"), title="Where to act"),
    st.Page(os.path.join(PAGES_DIR, "09_What_if.py"), title="What if"),
    st.Page(os.path.join(PAGES_DIR, "10_TAKE_ACTION.py"), title="TAKE ACTION"),
])
pg.run()