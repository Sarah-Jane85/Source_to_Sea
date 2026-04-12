import streamlit as st

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
    background-color: #0a0e17 !important;
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
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.image("assets/logo.svg", width=800, use_container_width=False)

st.markdown("""
<div style="display:flex; flex-direction:column; align-items:center;
            text-align:center; gap:0.5rem; margin-top:-2rem;">
  <div style="font-family:'Syne',sans-serif; font-weight:800; font-size:2.8rem;
              color:#e2e8f0; letter-spacing:-0.03em;">
    Source to Sea
  </div>
  <div style="font-family:'Space Mono',monospace; font-size:0.75rem;
              color:#00d4aa; letter-spacing:0.15em;">
    OCEAN PLASTIC ANALYSIS
  </div>
  <div style="color:#64748b; max-width:480px; line-height:1.6; margin-top:0.5rem;">
    Tracking <strong style="color:#e2e8f0;">1,001,000 t/yr</strong> of ocean-bound
    plastic from river source to marine impact.
  </div>
  <div style="font-family:'Space Mono',monospace; font-size:0.7rem;
              color:#1f2d40; margin-top:0.5rem;">
    ← Select a page from the sidebar
  </div>
</div>
""", unsafe_allow_html=True)