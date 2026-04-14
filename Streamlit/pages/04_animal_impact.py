import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from components.shared import apply_global_css, page_header

st.set_page_config(page_title="Animal Impact", page_icon="🐢", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("The Cost to Ocean Life", logo_svg)

st.markdown("""
<div style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:#64748b;
            max-width:800px; line-height:1.7; margin-bottom:2rem;">
  Plastic doesn't just float. It wraps, chokes, starves and poisons.
  For marine animals, every piece of plastic that enters the ocean is a potential
  death sentence — through entanglement, ingestion, or the slow accumulation
  of toxic microplastics in their tissues.
  <strong style="color:#e2e8f0;">Over 800 species</strong> are affected.
</div>
""", unsafe_allow_html=True)

# ── Helper ─────────────────────────────────────────────────────
def stat_pill(value, label, color="#ff3b5c"):
    return f"""<div style="display:inline-block; background:{color}22;
                border:1px solid {color}; border-radius:4px;
                padding:0.3rem 0.8rem; margin-bottom:1rem;">
      <span style="color:{color}; font-family:'Orbitron',sans-serif;
                   font-size:0.9rem; font-weight:700;">{value}</span>
      <span style="color:#94a3b8; font-size:0.8rem; margin-left:0.4rem;">{label}</span>
    </div>"""

# ── Section 1 — Sea Turtles ────────────────────────────────────
col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.markdown('<div style="padding-top:8rem;">', unsafe_allow_html=True)
    st.image("assets/turtle_plastic.jpg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="padding-top:0.5rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#f59e0b;
                  letter-spacing:0.15em; margin-bottom:0.5rem;">SEA TURTLES</div>
      <h2 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; font-size:1.5rem;
                 margin-bottom:1rem;">Mistaken for Jellyfish</h2>
      {stat_pill("52%", "of sea turtles have ingested plastic", "#f59e0b")}
      <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#94a3b8;
                  line-height:1.8;">
        Plastic bags floating in the ocean look almost identical to jellyfish —
        a sea turtle's favourite food. Once ingested, plastic cannot be digested
        and accumulates in the gut, causing blockages, internal injuries and starvation.
        <br><br>
        But ingestion is only half the story. Discarded plastic rings, netting and
        packaging physically trap turtles at a young age. As the animal grows,
        the plastic does not — cutting into flesh, deforming shells and restricting
        movement until the animal can no longer swim, feed or breathe.
        <br><br>
        <strong style="color:#e2e8f0;">All 7 species of sea turtle are classified
        as endangered or vulnerable.</strong> Plastic pollution is listed as one
        of the primary threats to their survival.
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Section 2 — Whales ────────────────────────────────────────
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown(f"""
    <div style="padding-top:0.5rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#ff3b5c;
                  letter-spacing:0.15em; margin-bottom:0.5rem;">WHALES & LARGE MARINE MAMMALS</div>
      <h2 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; font-size:1.5rem;
                 margin-bottom:1rem;">Ghost Nets — The Silent Killers</h2>
      {stat_pill("640,000 t", "of ghost gear abandoned in oceans every year", "#ff3b5c")}
      <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#94a3b8;
                  line-height:1.8;">
        Abandoned, lost or discarded fishing gear — known as <strong style="color:#e2e8f0;">
        ghost nets</strong> — is considered the deadliest form of plastic pollution
        for large marine animals. These nets continue fishing indefinitely after
        being discarded, drifting for years and trapping everything in their path.
        <br><br>
        Humpback whales, sperm whales and dolphins become entangled and drown,
        unable to surface for air. Those that survive carry the nets for months
        or years, the lines cutting deeper into their bodies with every movement.
        <br><br>
        Whales also ingest plastic directly — in 2019 a sperm whale was found
        dead in the Philippines with
        <strong style="color:#ff3b5c;">40 kg of plastic bags</strong>
        in its stomach. Post-mortems of stranded whales regularly reveal
        plastic waste as a contributing cause of death.
      </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div style="padding-top:10rem;">', unsafe_allow_html=True)
    st.image("assets/whale_entangled.jpg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Section 3 — Seals ─────────────────────────────────────────
col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.markdown('<div style="padding-top:8rem;">', unsafe_allow_html=True)
    st.image("assets/seal_entangled.jpg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="padding-top:0.5rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#ff3b5c;
                  letter-spacing:0.15em; margin-bottom:0.5rem;">SEALS & SEA LIONS</div>
      <h2 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; font-size:1.5rem;
                 margin-bottom:1rem;">Trapped from Birth</h2>
      {stat_pill("100,000+", "marine mammals die from plastic entanglement each year", "#ff3b5c")}
      <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#94a3b8;
                  line-height:1.8;">
        Seals and sea lions are among the most vulnerable to entanglement — their
        natural curiosity leads them to investigate floating debris, and their
        streamlined bodies make it easy for netting and packaging rings to
        slide over their heads and become trapped around their necks.
        <br><br>
        Young seals are particularly at risk. A piece of netting that fits loosely
        around a pup's neck will tighten as the animal grows, eventually
        cutting through flesh, restricting breathing and causing a slow,
        painful death by strangulation or infection.
        <br><br>
        <strong style="color:#e2e8f0;">70% of marine wildlife entanglements
        involve abandoned plastic fishing nets</strong> — the same ghost gear
        that threatens whales, dolphins and turtles across every ocean.
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Section 4 — Seahorse ──────────────────────────────────────
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown(f"""
    <div style="padding-top:0.5rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#00d4aa;
                  letter-spacing:0.15em; margin-bottom:0.5rem;">SMALL SPECIES</div>
      <h2 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; font-size:1.5rem;
                 margin-bottom:1rem;">No Animal Is Too Small</h2>
      {stat_pill("800+", "marine species affected by plastic pollution", "#00d4aa")}
      <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#94a3b8;
                  line-height:1.8;">
        This photograph — a seahorse clinging to a cotton swab in the Sargasso Sea —
        became one of the most shared environmental images in history. Taken by
        photographer Justin Hofman, it captures something the statistics alone
        cannot: <strong style="color:#e2e8f0;">there is nowhere left in the ocean
        untouched by plastic.</strong>
        <br><br>
        Seahorses use their tails to anchor to coral, seagrass and floating debris.
        As natural anchors disappear due to coral bleaching and habitat loss,
        they are increasingly found clinging to plastic waste instead —
        cotton buds, bottle caps, straws and microplastic fragments.
        <br><br>
        Small species like seahorses, plankton and larval fish ingest
        microplastics at rates that accumulate up the food chain —
        reaching larger predators, seabirds, and ultimately
        <strong style="color:#00d4aa;">the fish on your plate.</strong>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div style="padding-top:10rem;">', unsafe_allow_html=True)
    st.image("assets/sea_horse1.jpg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Section 5 — Fish & Ocean ──────────────────────────────────
col1, col2 = st.columns([2, 3], gap="large")

with col1:
    st.markdown('<div style="padding-top:6rem;">', unsafe_allow_html=True)
    st.image("assets/plastic_ocean.jpg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="padding-top:0.5rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#f59e0b;
                  letter-spacing:0.15em; margin-bottom:0.5rem;">FISH & THE REEF ECOSYSTEM</div>
      <h2 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; font-size:1.5rem;
                 margin-bottom:1rem;">An Ocean Choked at Every Level</h2>
      {stat_pill("1 in 3", "fish caught for human consumption contain plastic", "#f59e0b")}
      <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#94a3b8;
                  line-height:1.8;">
        Coral reefs — home to 25% of all marine species — are being smothered
        by plastic waste. Bags and sheeting block sunlight from reaching coral,
        while sharp debris physically damages reef structures that took
        centuries to build.
        <br><br>
        Fish mistake microplastic fragments for food. The particles are the same
        size as their natural prey — fish eggs, plankton and krill. Once ingested,
        microplastics carry absorbed chemical pollutants directly into the
        animal's tissue, bioaccumulating up the food chain with every predator
        that eats them.
        <br><br>
        <strong style="color:#e2e8f0;">By 2050, there could be more plastic in
        the ocean by weight than fish</strong> — a projection from the
        World Economic Forum that underlines just how urgent the crisis has become.
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Section 6 — Dead fish ─────────────────────────────────────
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown(f"""
    <div style="padding-top:0.5rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#ff3b5c;
                  letter-spacing:0.15em; margin-bottom:0.5rem;">THE FINAL TOLL</div>
      <h2 style="font-family:'Orbitron',sans-serif; color:#e2e8f0; font-size:1.5rem;
                 margin-bottom:1rem;">Washing Up on Every Shore</h2>
      {stat_pill("1M+", "seabirds and 100,000 marine mammals die from plastic each year", "#ff3b5c")}
      <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#94a3b8;
                  line-height:1.8;">
        Dead fish washing ashore with plastic debris surrounding them has
        become a familiar sight on coastlines worldwide. The image is not
        coincidental — plastic pollution disrupts every level of marine life,
        from the plankton that oxygenate our oceans to the apex predators
        at the top of the food chain.
        <br><br>
        Chemical pollutants absorbed by plastic in seawater — including
        pesticides, flame retardants and industrial chemicals — are transferred
        directly to animals that ingest plastic fragments. These toxins cause
        hormonal disruption, reproductive failure and immune suppression,
        quietly reducing populations across hundreds of species.
        <br><br>
        <strong style="color:#e2e8f0;">The ocean produces 50% of the world's
        oxygen and regulates our climate.</strong> When we poison it,
        we don't just lose the animals — we undermine the systems
        that keep our planet habitable.
      </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div style="padding-top:10rem;">', unsafe_allow_html=True)
    st.image("assets/dead_fish.jpg", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
# ── Closing stat bar ───────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

s1, s2, s3, s4 = st.columns(4)

stats = [
    ("800+", "species affected", "#ff3b5c"),
    ("1M+", "seabirds die/year", "#f59e0b"),
    ("52%", "turtles ingested plastic", "#f59e0b"),
    ("2050", "more plastic than fish", "#ff3b5c"),
]

for col, (val, label, color) in zip([s1, s2, s3, s4], stats):
    with col:
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #1f2d40;
                    border-left:3px solid {color}; border-radius:6px;
                    padding:1rem 1.2rem; text-align:center;">
          <div style="color:{color}; font-family:'Orbitron',sans-serif;
                      font-size:1.3rem; font-weight:700;">{val}</div>
          <div style="color:#64748b; font-size:0.78rem; margin-top:0.3rem;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="background:#111827; border:1px solid #1f2d40; border-radius:8px;
            padding:1.4rem 2rem; text-align:center;">
  <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#64748b;
              max-width:700px; margin:0 auto; line-height:1.8;">
    The data on the following pages shows where this plastic comes from,
    how it accumulates, and — crucially —
    <strong style="color:#00d4aa;">what we can do to stop it.</strong>
  </div>
</div>
""", unsafe_allow_html=True)