import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import math
from components.shared import (
    ANNUAL_INPUT_T, BEST_CLEANUP_T, GUATEMALA_T_PER_YEAR,
    INTERCEPTORS_DEPLOYED, INTERCEPTORS_NEEDED, INTERCEPTORS_GAP,
    TOP_101_PCT, COLORS, load_cleanup,
    apply_global_css, page_header
)

st.set_page_config(page_title="What If?", page_icon="💡", layout="wide")
apply_global_css()

with open("assets/logo_icon.svg", "r") as f:
    logo_svg = f.read()

page_header("What If?", logo_svg)

st.markdown("""
<div style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:#64748b;
            max-width:720px; line-height:1.7; margin-bottom:1.5rem;">
  The Guatemala interceptor captures ~<strong style="color:#e2e8f0;">10,000 t/yr</strong> —
  the best single-unit benchmark available. Use the sliders to model how many
  interceptors, at what efficiency, would be needed to close the gap against
  <strong style="color:#e2e8f0;">1,001,000 t/yr</strong> of ocean-bound plastic.
</div>
""", unsafe_allow_html=True)

# ── Sliders ────────────────────────────────────────────────────
col_sliders, col_gap = st.columns([2, 3], gap="large")

with col_sliders:
    n_interceptors = st.slider(
        "Number of interceptors",
        min_value=1, max_value=200,
        value=INTERCEPTORS_DEPLOYED,
        step=1,
        help="Total interceptors deployed globally"
    )
    efficiency_pct = st.slider(
        "Efficiency vs Guatemala benchmark",
        min_value=10, max_value=100,
        value=100,
        step=5,
        format="%d%%",
        help="100% = each unit captures 10,000 t/yr like Rio Las Vacas"
    )

# ── Core calculation ───────────────────────────────────────────
CAGR              = 0.40
CURRENT_GAP_T     = ANNUAL_INPUT_T - BEST_CLEANUP_T
efficiency_factor = efficiency_pct / 100
offset_t          = n_interceptors * efficiency_factor * GUATEMALA_T_PER_YEAR
pct_of_input      = offset_t / ANNUAL_INPUT_T * 100
gap_closed_pct    = offset_t / CURRENT_GAP_T * 100

# Years to parity — only meaningful when scenario exceeds current deployment
interceptors_needed_to_offset = math.ceil(
    ANNUAL_INPUT_T / (efficiency_factor * GUATEMALA_T_PER_YEAR)
)

if n_interceptors <= INTERCEPTORS_DEPLOYED:
    years_to_parity = None
else:
    target_t = offset_t
    if target_t <= BEST_CLEANUP_T:
        years_to_parity = 0.0
    else:
        years_to_parity = math.log(target_t / BEST_CLEANUP_T) / math.log(1 + CAGR)

# ── Result cards ───────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

def result_card(label, value, sub=None, color="#00d4aa", border_color="#00d4aa"):
    sub_html = (
        f'<div style="color:#64748b; font-size:0.78rem; margin-top:0.3rem;">{sub}</div>'
        if sub else ""
    )
    return f"""
    <div style="background:#111827; border:1px solid #1f2d40;
                border-left:3px solid {border_color}; border-radius:6px;
                padding:1.2rem 1.4rem; margin-bottom:1rem;">
      <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#64748b;
                  letter-spacing:0.08em; margin-bottom:0.5rem;">{label}</div>
      <div style="font-size:1.8rem; font-weight:700; color:{color};
                  font-family:'Orbitron',sans-serif;">{value}</div>
      {sub_html}
    </div>"""

r1, r2, r3, r4 = st.columns(4)

with r1:
    st.markdown(result_card(
        "TONNES OFFSET / YR",
        f"{offset_t:,.0f} t",
        sub=f"{n_interceptors} × {efficiency_pct}% × 10,000 t",
        color="#00d4aa", border_color="#00d4aa",
    ), unsafe_allow_html=True)

with r2:
    color2 = "#00d4aa" if pct_of_input >= 50 else "#f59e0b"
    st.markdown(result_card(
        "% OF ANNUAL INPUT",
        f"{pct_of_input:.1f}%",
        sub=f"of {ANNUAL_INPUT_T:,} t/yr",
        color=color2, border_color=color2,
    ), unsafe_allow_html=True)

with r3:
    color3 = "#00d4aa" if gap_closed_pct >= 100 else "#ff3b5c"
    st.markdown(result_card(
        "GAP CLOSED",
        f"{min(gap_closed_pct, 100):.1f}%",
        sub=f"of {CURRENT_GAP_T:,.0f} t remaining gap",
        color=color3, border_color=color3,
    ), unsafe_allow_html=True)

with r4:
    if years_to_parity is None:
        ytp_val   = "You are here"
        ytp_sub   = "increase interceptors to model future growth"
        ytp_color = "#00d4aa"
    elif years_to_parity == 0.0:
        ytp_val   = "Already there"
        ytp_sub   = "cleanup sector already matches this scenario"
        ytp_color = "#00d4aa"
    else:
        ytp_val   = f"{years_to_parity:.1f} yrs"
        ytp_sub   = f"till the sector matches this scenario at {int(CAGR*100)}% annual growth"
        ytp_color = "#f59e0b"
    st.markdown(result_card(
        "YRS AT CURRENT GROWTH RATE",
        ytp_val,
        sub=ytp_sub,
        color=ytp_color, border_color=ytp_color,
    ), unsafe_allow_html=True)

# ── Context note ───────────────────────────────────────────────
st.markdown(f"""
<div style="background:#111827; border:1px solid #1f2d40; border-radius:6px;
            padding:1rem 1.4rem; font-size:0.82rem; color:#64748b; line-height:1.8;">
  <strong style="color:#e2e8f0;">To fully offset annual input</strong> at
  {efficiency_pct}% efficiency you need
  <strong style="color:#f59e0b;">{interceptors_needed_to_offset} interceptors</strong>.<br>
  Currently {INTERCEPTORS_DEPLOYED} are deployed —
  <strong style="color:#ff3b5c;">
    {max(0, interceptors_needed_to_offset - INTERCEPTORS_DEPLOYED)} more needed
  </strong>.<br>
  Best recorded cleanup year: <strong style="color:#e2e8f0;">{BEST_CLEANUP_T:,} t</strong>
  ({BEST_CLEANUP_T / ANNUAL_INPUT_T * 100:.1f}% of annual input).
  <br><br>
  <span style="color:#a66800;">⚠ Benchmark note</span> —
  100% efficiency is calibrated to the
  <strong style="color:#e2e8f0;">Guatemala interceptor (Rio Las Vacas)</strong>,
  the best-performing unit on record at ~10,000 t/yr.<br>
  The Ocean Cleanup themselves estimate that real-world fleet average performance
  is roughly <strong style="color:#f59e0b;<br>">30–50% of their best unit</strong>,
  so a realistic scenario sits between those two markers on the slider.
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Offset curve ───────────────────────────────────────────────
st.markdown("### Offset curve — interceptors vs annual input")

sweep        = list(range(1, 201))
pct_sweep    = [n * efficiency_factor * GUATEMALA_T_PER_YEAR / ANNUAL_INPUT_T * 100 for n in sweep]
pct_sweep_30 = [n * 0.30 * GUATEMALA_T_PER_YEAR / ANNUAL_INPUT_T * 100 for n in sweep]
pct_sweep_50 = [n * 0.50 * GUATEMALA_T_PER_YEAR / ANNUAL_INPUT_T * 100 for n in sweep]

fig = go.Figure()

# ── Realistic band (30–50%) — rendered first so teal line sits on top ──
fig.add_trace(go.Scatter(
    x=sweep, y=pct_sweep_30,
    mode="lines",
    line=dict(color="rgba(245,158,11,0)", width=0),
    showlegend=False,
    hoverinfo="skip",
))
fig.add_trace(go.Scatter(
    x=sweep, y=pct_sweep_50,
    mode="lines",
    line=dict(color="rgba(245,158,11,0.5)", width=1, dash="dot"),
    name="Realistic range (30–50% efficiency)",
    hoverinfo="skip",
))

# ── Your scenario line — no fill so it doesn't darken the band ─
fig.add_trace(go.Scatter(
    x=sweep, y=pct_sweep,
    mode="lines",
    line=dict(color="#00d4aa", width=2.5),
    name=f"Your scenario ({efficiency_pct}% efficiency)",
    hovertemplate="<b>%{x} interceptors</b><br>%{y:.1f}% of input offset<extra></extra>",
))

# ── Reference lines ────────────────────────────────────────────
fig.add_hline(
    y=100,
    line=dict(color="#ff3b5c", width=1.5, dash="dot"),
    annotation_text="100% parity",
    annotation_font=dict(color="#ff3b5c", size=11),
)
fig.add_vline(
    x=INTERCEPTORS_DEPLOYED,
    line=dict(color="#f59e0b", width=1.5, dash="dash"),
    annotation_text=f"Today: {INTERCEPTORS_DEPLOYED}",
    annotation_font=dict(color="#f59e0b", size=11),
    annotation_position="bottom right",
)
fig.add_vline(
    x=n_interceptors,
    line=dict(color="#00d4aa", width=1, dash="dot"),
    annotation_text=f"Scenario: {n_interceptors}",
    annotation_font=dict(color="#00d4aa", size=10),
    annotation_position="top left",
)

fig.update_layout(
    paper_bgcolor="#0a0e17",
    plot_bgcolor="#111827",
    font=dict(color="#e2e8f0"),
    height=380,
    xaxis=dict(title="Number of interceptors", gridcolor="#1f2d40", range=[0, 200]),
    yaxis=dict(title="% of annual input offset", gridcolor="#1f2d40",
               ticksuffix="%", range=[0, 115]),
    margin=dict(l=48, r=24, t=24, b=48),
    legend=dict(
        bgcolor="#111827",
        bordercolor="#1f2d40",
        borderwidth=1,
        x=0.98,
        y=0.02,
        xanchor="right",
        yanchor="bottom",
    ),
)
st.plotly_chart(fig, use_container_width=True)

# ── Sensitivity table ──────────────────────────────────────────
st.markdown("### Sensitivity — % of annual input offset")

eff_levels  = [50, 60, 70, 80, 90, 100]
scenario_ns = [20, 50, 101, 150, 200]

eff_headers = "".join([
    f'<th style="text-align:right; padding:0.5rem 0.9rem; color:#64748b; '
    f'font-weight:400; border-bottom:1px solid #1f2d40;">{e}%</th>'
    for e in eff_levels
])

table_rows = ""
for n in scenario_ns:
    highlight = "background:#0d1f2d;" if n == n_interceptors else ""
    cells = "".join([
        f'<td style="text-align:right; padding:0.45rem 0.9rem; color:#e2e8f0; {highlight}">'
        f'{n * (e/100) * GUATEMALA_T_PER_YEAR / ANNUAL_INPUT_T * 100:.1f}%</td>'
        for e in eff_levels
    ])
    table_rows += (
        f'<tr style="{highlight}">'
        f'<td style="padding:0.45rem 0.9rem; color:#f59e0b; font-weight:700;">{n}</td>'
        f'{cells}</tr>'
    )

st.markdown(f"""
<div style="overflow-x:auto;">
<table style="width:100%; border-collapse:collapse; background:#111827;
              border:1px solid #1f2d40; border-radius:6px; font-size:0.82rem;
              font-family:'Space Mono',monospace;">
  <thead>
    <tr>
      <th style="text-align:left; padding:0.5rem 0.9rem; color:#64748b;
                 font-weight:400; border-bottom:1px solid #1f2d40;">
        interceptors ↓ &nbsp;&nbsp; efficiency →
      </th>
      {eff_headers}
    </tr>
  </thead>
  <tbody>{table_rows}</tbody>
</table>
<div style="font-size:0.72rem; color:#64748b; margin-top:0.5rem;">
  Values = % of {ANNUAL_INPUT_T:,} t/yr annual input offset at each efficiency level
</div>
</div>
""", unsafe_allow_html=True)