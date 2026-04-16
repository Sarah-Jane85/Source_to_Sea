import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from components.shared import apply_global_css, page_header

st.set_page_config(page_title="Cleanup Information", page_icon="🌊", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("Ways Action is being taken", logo_svg)

st.markdown("""
<div style="font-family:'DM Sans',sans-serif; font-size:1rem; color:#ccc7c7;
            max-width:800px; line-height:1; margin-bottom:2rem;">
  Plastic reaches the ocean in stages — from land to waterway to sea.
  That means we can intercept it at every stage.
  Here are the three most impactful ways to stop plastic before it becomes an ocean problem.
</div>
""", unsafe_allow_html=True)

# ── Section 1 — Land Cleanup ──────────────────────────────────
col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.markdown('<div style="padding-top:3rem;">', unsafe_allow_html=True)
    st.image("assets/park_cleanup.jpg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="padding-top:1rem;">
      <div style="font-family:'Space Mono',monospace; font-size:1rem; color:#00d4aa;
                  letter-spacing:0.15em; margin-bottom:0.5rem;">STEP 01 — STOP IT AT THE SOURCE</div>
      <h2 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; margin-bottom:1rem;
                 font-size:1.6rem;">Community Land Cleanups</h2>
      <div style="font-family:'DM Sans',sans-serif; font-size:1.2rem; color:#ccc7c7;
                  line-height:1;">
        The most effective intervention is the simplest — picking up plastic before
        it ever reaches a waterway. Litter left on land gets carried by rain and wind
        into drains, rivers and ultimately the ocean.
        <br><br>
        <strong style="color:#e2e8f0;">Community cleanup events</strong> target parks,
        roadsides and urban areas — the last line of defence before plastic enters
        the water system. Globally, Ocean Conservancy's International Coastal Cleanup
        alone mobilises over <strong style="color:#00d4aa;">500,000 volunteers</strong>
        per year across 100+ countries.
        <br><br>
        Even small local actions matter: studies show that
        <strong style="color:#00d4aa;">80% of ocean plastic</strong> originates from
        land-based sources, meaning every bag of litter collected on land is plastic
        that will never reach the sea.
      </div>
      <div style="margin-top:1.5rem;">
        <a href="https://oceanconservancy.org/trash-free-seas/international-coastal-cleanup/"
           target="_blank"
           style="background:#00856b; color:#e2e8f0; padding:0.5rem 1.2rem;
                  border-radius:4px; font-family:'Space Mono',monospace;
                  font-size:0.72rem; text-decoration:none; letter-spacing:0.08em;">
          FIND A CLEANUP EVENT →
        </a>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Section 2 — Beach Cleanup ─────────────────────────────────
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown("""
    <div style="padding-top:1rem;">
      <div style="font-family:'Space Mono',monospace; font-size:1rem; color:#f59e0b;
                  letter-spacing:0.15em; margin-bottom:0.5rem;">STEP 02 — CATCH IT AT THE COAST</div>
      <h2 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; margin-bottom:1rem;
                 font-size:1.6rem;">Beach Cleanups</h2>
      <div style="font-family:'DM Sans',sans-serif; font-size:1.2rem; color:#ccc7c7;
                  line-height:1;">
        Beaches are the last checkpoint before plastic enters open water — but they're
        also where ocean plastic washes back ashore, giving us a second chance to
        remove it from the cycle.
        <br><br>
        <strong style="color:#e2e8f0;">Beach cleanup events</strong> serve a dual purpose:
        they remove newly arrived land-based litter before the next tide takes it out,
        and they recover marine plastic that has already been in the ocean and washed back.
        <br><br>
        The scale of the problem is visible here — the image shows a large-scale cleanup
        in the Philippines, one of the world's
        <strong style="color:#f59e0b;">top plastic-emitting countries</strong>
        with over 350,000 t/yr entering waterways. Regular beach cleanups in high-emission
        coastal cities can make a measurable difference.
      </div>
      <div style="margin-top:1.5rem;">
        <a href="https://www.coastalcleanupday.org/"
           target="_blank"
           style="background:#a66800; color:#e2e8f0; padding:0.5rem 1.2rem;
                  border-radius:4px; font-family:'Space Mono',monospace;
                  font-size:0.72rem; text-decoration:none; letter-spacing:0.08em;">
          JOIN A BEACH CLEANUP →
        </a>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div style="padding-top:3rem;">', unsafe_allow_html=True)
    st.image("assets/beach_cleanup.jpg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Section 3 — Interceptors ──────────────────────────────────
st.markdown("""
<div style="margin-bottom:1.5rem;">
  <div style="font-family:'Space Mono',monospace; font-size:1rem; color:#ff3b5c;
              letter-spacing:0.15em; margin-bottom:0.5rem;">STEP 03 — STOP IT IN THE RIVER</div>
  <h2 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; margin-bottom:1rem;
             font-size:1.6rem;">River Interceptors</h2>
  <div style="font-family:'DM Sans',sans-serif; font-size:1.2rem; color:#ccc7c7;
              line-height:1; max-width:900px;">
    Rivers are the main highway for plastic travelling from land to ocean —
    <strong style="color:#e2e8f0;">1,000 rivers account for 80%</strong> of all
    river-borne plastic entering the sea. Interceptors are autonomous, solar-powered
    machines deployed directly in rivers to catch floating debris before it reaches
    the ocean.
    <br><br>
    Developed by <strong style="color:#e2e8f0;">The Ocean Cleanup</strong>, interceptors
    use the river's natural current to funnel plastic onto a conveyor belt, which
    deposits it into collection bins. When full, local operators empty the bins and
    send waste to local waste management facilities — no fuel, no pollution, fully
    automated. The best-performing unit, <strong style="color:#ff3b5c;">Interceptor 006
    in Guatemala</strong>, captures ~10,000 tonnes of plastic per year.
  </div>
</div>
""", unsafe_allow_html=True)

# Three interceptor images
img1, img2, img3 = st.columns(3, gap="medium")

with img1:
    st.image("assets/barricade.jpg", use_container_width=True)
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#64748b;
                text-align:center; margin-top:0.5rem; line-height:1.5;">
      <strong style="color:#e2e8f0;">Interceptor 006 — Guatemala</strong><br>
      The barricade design catches plastic<br>across the full river width
    </div>
    """, unsafe_allow_html=True)

with img2:
    st.image("assets/interceptor.jpg", use_container_width=True)
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#64748b;
                text-align:center; margin-top:0.5rem; line-height:1.5;">
      <strong style="color:#e2e8f0;">Interceptor 007 — Los Angeles</strong><br>
      Aerial view showing scale of plastic<br>accumulation at river mouth
    </div>
    """, unsafe_allow_html=True)

with img3:
    st.image("assets/inside_interceptor.jpg", use_container_width=True)
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#64748b;
                text-align:center; margin-top:0.5rem; line-height:1.5;">
      <strong style="color:#e2e8f0;">Inside the Interceptor</strong><br>
      The conveyor belt lifts debris from<br>the water into collection bins
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Stats row
s1, s2, s3, s4 = st.columns(4)

with s1:
    st.markdown("""
    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #ff3b5c;
                border-radius:6px; padding:1rem 1.2rem; text-align:center;">
      <div style="color:#ff3b5c; font-family:'Orbitron',sans-serif;
                  font-size:1.4rem; font-weight:700;">19</div>
      <div style="color:#64748b; font-size:0.8rem; margin-top:0.3rem;">interceptors deployed</div>
    </div>
    """, unsafe_allow_html=True)

with s2:
    st.markdown("""
    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #f59e0b;
                border-radius:6px; padding:1rem 1.2rem; text-align:center;">
      <div style="color:#f59e0b; font-family:'Orbitron',sans-serif;
                  font-size:1.4rem; font-weight:700;">10,000 t</div>
      <div style="color:#64748b; font-size:0.8rem; margin-top:0.3rem;">removed by 1 interceptor in 2024</div>
    </div>
    """, unsafe_allow_html=True)

with s3:
    st.markdown("""
    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #00d4aa;
                border-radius:6px; padding:1rem 1.2rem; text-align:center;">
      <div style="color:#00d4aa; font-family:'Orbitron',sans-serif;
                  font-size:1.4rem; font-weight:700;">1,000</div>
      <div style="color:#64748b; font-size:0.8rem; margin-top:0.3rem;">rivers targeted</div>
    </div>
    """, unsafe_allow_html=True)

with s4:
    st.markdown("""
    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid #00d4aa;
                border-radius:6px; padding:1rem 1.2rem; text-align:center;">
      <div style="color:#00d4aa; font-family:'Orbitron',sans-serif;
                  font-size:1.4rem; font-weight:700;">100%</div>
      <div style="color:#64748b; font-size:0.8rem; margin-top:0.3rem;">solar powered</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="background:#111827; border:1px solid #1f2d40; border-radius:6px;
            padding:1rem 1.4rem; font-size:0.82rem; color:#64748b; line-height:1.7;">
  <strong style="color:#e2e8f0;">Want to support interceptor deployment?</strong>
  Visit
  <a href="https://theoceancleanup.com" target="_blank"
     style="color:#00d4aa;">theoceancleanup.com</a>
  to learn more about The Ocean Cleanup's river programme and the
  <strong style="color:#e2e8f0;">30 Cities initiative</strong> — their plan to
  cut ocean plastic from rivers by one third by 2030.
</div>
""", unsafe_allow_html=True)