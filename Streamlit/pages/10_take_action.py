import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from components.shared import apply_global_css, page_header

st.set_page_config(page_title="Take Action", page_icon="💪", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("Take Action", logo_svg)

st.markdown("""
<div style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:#64748b;
            max-width:800px; line-height:1.7; margin-bottom:0.5rem;">
  The data tells the story — now here's what you can do about it.
  Every bottle collected, every event joined, every donation made moves the needle.
  <strong style="color:#e2e8f0;">Pick one action today.</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Helper function for link cards ────────────────────────────
def link_card(name, url, description, flag, color="#00d4aa", btn_label="VISIT →"):
    return f"""
    <div style="background:#111827; border:1px solid #1f2d40; border-left:3px solid {color};
                border-radius:8px; padding:1.2rem 1.4rem; margin-bottom:0.75rem;
                display:flex; flex-direction:column; gap:0.5rem;">
      <div style="display:flex; align-items:center; justify-content:space-between;">
        <div style="display:flex; align-items:center; gap:0.6rem;">
          <span style="font-size:1.1rem;">{flag}</span>
          <span style="font-family:'Orbitron',sans-serif; font-size:0.85rem;
                       color:#e2e8f0; font-weight:700;">{name}</span>
        </div>
        <a href="{url}" target="_blank"
           style="background:{color}; color:#0a0e17; padding:0.35rem 0.9rem;
                  border-radius:4px; font-family:'Space Mono',monospace;
                  font-size:0.65rem; text-decoration:none; letter-spacing:0.08em;
                  font-weight:700; white-space:nowrap;">{btn_label}</a>
      </div>
      <div style="font-family:'DM Sans',sans-serif; font-size:0.82rem;
                  color:#64748b; line-height:1.6;">{description}</div>
    </div>"""

# ── Section 1 — Cleanup Events ────────────────────────────────
st.markdown("""
<div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#00d4aa;
            letter-spacing:0.15em; margin-bottom:1rem;">🧤 JOIN A CLEANUP EVENT</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(link_card(
        "The Ocean Cleanup — Volunteer",
        "https://theoceancleanup.com/volunteer/",
        "Join The Ocean Cleanup's volunteer network. Help with beach and river cleanups organised by the same team behind the Interceptors — directly supporting the world's most ambitious plastic removal programme.",
        "🌊", "#00d4aa", "VOLUNTEER →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "Ocean Conservancy — ICC",
        "https://oceanconservancy.org/work/plastics/cleanups-icc/",
        "The International Coastal Cleanup is the world's largest volunteer effort for ocean health, mobilising over 500,000 volunteers across 100+ countries every year. Find a cleanup near you or register your own.",
        "🇺🇸", "#00d4aa", "FIND EVENT →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "World Cleanup Day",
        "https://dayspedia.com/pt/calendar/holiday/913/",
        "World Cleanup Day is the world's largest single-day civic action, with millions of volunteers in 180+ countries cleaning up land and coastal areas simultaneously every September. Find your country's event date and location here.",
        "🌍", "#00d4aa", "FIND DATE →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "Greenpeace Germany — Gemeinsam Aktiv",
        "https://www.greenpeace.de/engagieren/gemeinsam-aktiv",
        "Greenpeace Germany's volunteer action platform. Find local environmental actions, cleanups and campaigns across Germany — from city litter picks to river and coastal events.",
        "🇩🇪", "#00d4aa", "MITMACHEN →"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(link_card(
        "California Coastal Cleanup",
        "https://www.coastal.ca.gov/publiced/ccd/ccd.html",
        "California's annual Coastal Cleanup Day is one of the largest single-day cleanup events in the world. Organised by the California Coastal Commission, it covers beaches, lakes and waterways across the entire state.",
        "🇺🇸", "#00d4aa", "JOIN →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "Marine Conservation Philippines",
        "https://marineconservationphilippines.org/clean-up-calendar/",
        "The Philippines is one of the world's top plastic-emitting countries. MCP runs regular coastal and underwater cleanups across the Philippine islands — one of the highest-impact places to volunteer.",
        "🇵🇭", "#00d4aa", "CALENDAR →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "Clean Beach Initiative",
        "https://cleanbeachinitiative.org/",
        "Founded in Barcelona, Clean Beach Initiative runs weekly beach cleanups open to everyone — individuals, families, schools and companies. Their crew meets at Barceloneta every week and welcomes new volunteers, tracking and weighing every kilogram collected.",
        "🇪🇸", "#00d4aa", "JOIN IN BARCELONA →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "Mondo4Africa — Ghana Cleanups",
        "https://mondo4africa.com/cleanups-in-ghana/",
        "Ghana faces severe coastal plastic pollution. Mondo4Africa organises community-led cleanup events along Ghana's coastline, working directly with local communities to remove plastic before it reaches the Atlantic.",
        "🇬🇭", "#00d4aa", "GET INVOLVED →"
    ), unsafe_allow_html=True)

# ── Section 3 — Track you action ─────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)

st.markdown("""
<div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#00856b;
            letter-spacing:0.15em; margin:1rem 0;">📱 TRACK YOUR DAILY IMPACT</div>
""", unsafe_allow_html=True)

st.markdown(link_card(
    "ActNow — UN Sustainability App",
    "https://actnow.aworld.org/",
    "The official app of the United Nations ActNow campaign, built by AWorld. Track your daily sustainability actions, measure your carbon footprint, complete challenges and earn rewards — all gamified to make sustainable living accessible. Over 10 million actions logged globally.",
    "🇺🇳", "#00856b", "GET THE APP →"
), unsafe_allow_html=True)

st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)


# ── Section 2 — Donate / Support ─────────────────────────────
st.markdown("""
<div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#f59e0b;
            letter-spacing:0.15em; margin-bottom:1rem;">💛 SUPPORT THE ORGANISATIONS MAKING IT HAPPEN</div>
""", unsafe_allow_html=True)

col_d1, col_d2 = st.columns(2, gap="large")

with col_d1:
    st.markdown(link_card(
        "The Ocean Cleanup — Donate",
        "https://theoceancleanup.com/donate/",
        "The Ocean Cleanup is the organisation behind the river Interceptors featured throughout this dashboard. Donations directly fund deployment of new Interceptors and the 30 Cities Programme — their plan to cut river plastic by one third by 2030.",
        "🌊", "#f59e0b", "DONATE →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "4ocean Foundation — Donate",
        "https://4oceanfoundation.org/",
        "4ocean Foundation runs full-time professional cleanup crews 7 days a week in Florida, Bali, Java and Guatemala — removing plastic from rivers, coastlines and the open ocean daily. Founded in 2017, they have removed over 40 million pounds of waste. Donations fund crew operations and vessel maintenance directly.",
        "🌊", "#f59e0b", "DONATE →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "Plastic Pollution Coalition",
        "https://www.plasticpollutioncoalition.org/",
        "A global alliance of 1,200+ organizations, businesses and individuals working to end plastic pollution through advocacy, policy change and communications. Founded in 2009, PPC campaigns against single-use plastics, holds corporations accountable, and connects activists across 75 countries.",
        "✊", "#f59e0b", "JOIN THE COALITION →"
    ), unsafe_allow_html=True)

with col_d2:
    st.markdown(link_card(
        "Plastic Bank — Monthly Contribution",
        "https://plasticbank.com/individuals/#monthly",
        "Plastic Bank builds ethical recycling ecosystems in coastal communities across the Philippines, Indonesia, Brazil, Egypt and Ghana. A monthly contribution funds collectors who exchange plastic waste for income, school tuition and healthcare — stopping ocean plastic while lifting people out of poverty.",
        "♻️", "#f59e0b", "DONATE MONTHLY →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "Plastic Bank — One-time Contribution",
        "https://plasticbank.com/individuals/#onetime",
        "Make a one-time donation to fund plastic collection in coastal communities. Every kilogram collected is tracked via blockchain — you can see exactly where your contribution went and how much plastic was stopped from reaching the ocean.",
        "♻️", "#f59e0b", "DONATE ONCE →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "Sea Shepherd — Support",
        "https://seashepherd.org/",
        "Sea Shepherd has been defending the oceans through direct action since 1977 — confronting illegal fishing, removing ghost nets, and running Operation Clean Waves to tackle plastic pollution in remote island nations. Their crews operate year-round on 12 vessels across the world's oceans.",
        "⚓", "#f59e0b", "SUPPORT →"
    ), unsafe_allow_html=True)

# ── Interseting sites ─────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:#1f2d40;">', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
<div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#457B9D;
            letter-spacing:0.15em; margin-bottom:1rem;">🔭 INTERESTING INITIATIVES TO EXPLORE</div>
""", unsafe_allow_html=True)

col_i1, col_i2 = st.columns(2, gap="large")

with col_i1:
    st.markdown(link_card(
        "Alliance to End Plastic Waste",
        "https://www.endplasticwaste.org/",
        "A global not-for-profit alliance of companies across the plastics value chain, investing hundreds of millions of dollars to develop and scale solutions that reduce plastic waste. With 80+ projects in 30+ countries, they focus on waste infrastructure, recycling innovation and circular economy models — working at a systems level where individual action alone can't reach.",
        "🏭", "#457B9D", "EXPLORE →"
    ), unsafe_allow_html=True)

with col_i2:
    st.markdown(link_card(
        "CAPWs — Community Action Against Plastic Waste",
        "https://www.capws.org/",
        "A UNEP-accredited grassroots NGO headquartered in Nigeria, operating across 71 communities in 21 countries in Africa, Asia-Pacific and Latin America. Their #RestorationX10000 programme empowers 10,000 youth and women to lead plastic collection and recycling initiatives while creating green jobs in some of the world's most vulnerable coastal communities.",
        "🌍", "#457B9D", "EXPLORE →"
    ), unsafe_allow_html=True)

    st.markdown(link_card(
        "SaiGon Xanh — Green Saigon",
        "https://saigonxanh.org/",
        "A Vietnamese community platform for environmental action in Ho Chi Minh City — one of the world's highest plastic-emitting urban areas. Volunteers earn points for joining cleanups, exchanging recyclable waste and buying recycled products. Site is in Vietnamese, but the app is available internationally. A grassroots example of digital tools driving local cleanup action.<br><span style='color:#e2e8f0;'>🎬 Follow their work in English on <a href='https://www.youtube.com/@saigonxanhgroup' target='_blank' style='color:#00d4aa;'>YouTube →</a></span>",
        "🇻🇳", "#457B9D", "EXPLORE →"
    ), unsafe_allow_html=True)

# ── Closing call to action ─────────────────────────────────────
st.markdown("""
<div style="background:#111827; border:1px solid #1f2d40; border-radius:8px;
            padding:1.6rem 2rem; text-align:center;">
  <div style="font-family:'Orbitron',sans-serif; font-size:1.1rem; color:#e2e8f0;
              margin-bottom:0.75rem;">Every Bottle Counts</div>
  <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#64748b;
              max-width:600px; margin:0 auto; line-height:1.8;">
    The <strong style="color:#e2e8f0;">1,001,000 tonnes</strong> entering the ocean each year
    didn't get there in one go — it got there one bottle, one bag, one piece at a time.
    The solution works the same way.<br><br>
    <strong style="color:#00d4aa;">Pick up one piece of plastic today.</strong>
  </div>
</div>
""", unsafe_allow_html=True)
