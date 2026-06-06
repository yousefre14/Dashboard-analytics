"""
main.py  —  HR Attrition Dashboard (ENHANCED)
Kayfa AI & Data Analytics Internship · Week 1

Run:     streamlit run main.py
Deploy:  GitHub → share.streamlit.io  (requirements.txt must list streamlit>=1.36.0)

Architecture:
  - st.navigation / st.Page for multi-page navigation (rubric requirement)
  - Shared sidebar (logo + filters) defined BEFORE pg.run() → persists on all pages
  - dff (filtered DataFrame) computed once in outer scope, used by all page functions
  - @st.cache_data ensures data + aggregations run only once per session
  - Software testing integrated for data & visualization validation
  - Professional CSS/HTML with dark-mode support
  - Fixed logo positioning on sidebar and homepage
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple

from Data_Handling import (
    load_and_clean, compute_aggregration,
    compute_q_aggregations, filtered_kpis,
    test_data_completeness, test_aggregation_output,
    print_data_summary, DataValidationError
)

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  —  MUST be the very first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Workforce Retention Intelligence · Kayfa",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────────────
# BRAND CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
KB        = "#1A5AFF"   # Kayfa Blue
KB_DARK   = "#1245CC"
KB_LIGHT  = "#E8EFFF"
AMBER     = "#F59E0B"   # reference / average lines  (contrasts with blue)
GREEN     = "#16A34A"   # positive/success callouts
RED       = "#DC2626"   # risk/negative callouts
BLUE_SEQ  = [KB_LIGHT, "#BDD0FF", "#7FA8FF", "#4C84FF",
             KB, KB_DARK, "#0D31A3", "#081F7A"]
DIVERG    = ["#E8EFFF", "#7FA8FF", KB, KB_DARK]
ATTRITION_MAP = {"Stayed": KB_LIGHT, "Left": KB}


# ─────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL CSS  —  Dark-mode safe, responsive, branded
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* ── Global typography ── */
html, body, [class*="css"] { 
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Sidebar — always Kayfa Blue background ── */
section[data-testid="stSidebar"] { 
    background: #1A5AFF !important; 
}
section[data-testid="stSidebar"] * { 
    color: #FFFFFF !important; 
}
section[data-testid="stSidebar"] hr { 
    border-color: rgba(255,255,255,0.25) !important; 
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background: #1245CC !important;
    color: white !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.15) !important;
    border-color: rgba(255,255,255,0.3) !important;
    color: white !important;
}
section[data-testid="stSidebar"] .stRadio label { 
    color: white !important; 
}
section[data-testid="stSidebar"] .stSlider label {
    color: white !important;
}

/* ── Sidebar logo container — fixed at top ── */
.sidebar-logo-container {
    position: relative;
    width: 100%;
    padding: 1rem 0;
    margin-bottom: 0.5rem;
    border-bottom: 2px solid rgba(255,255,255,0.2);
}

/* ── Insight box — transparent blue tint, works in dark + light ── */
.insight-box {
    background: rgba(26,90,255,0.08);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.84rem;
    line-height: 1.55;
}
.insight-box b { 
    color: #1A5AFF; 
    font-weight: 700;
}

/* ── CTA box — green tint (success) ── */
.cta-box {
    background: rgba(22,163,74,0.07);
    border-left: 4px solid #16A34A;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin-top: 0.4rem;
    margin-bottom: 0.4rem;
    font-size: 0.84rem;
    line-height: 1.55;
}
.cta-box b { 
    color: #16A34A; 
    font-weight: 700;
}

/* ── Risk callout ── */
.risk-card {
    background: rgba(220,38,38,0.07);
    border: 1px solid rgba(220,38,38,0.25);
    border-left: 4px solid #DC2626;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}
.risk-card b { 
    color: #DC2626; 
    font-weight: 700;
}

/* ── Q badge ── */
.q-badge {
    display: inline-block;
    background: #1A5AFF;
    color: white !important;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    border-radius: 4px;
    padding: 2px 9px;
    margin-bottom: 0.3rem;
    text-transform: uppercase;
}

/* ── Section divider ── */
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    border-bottom: 2px solid rgba(26,90,255,0.2);
    padding-bottom: 0.5rem;
    margin: 1.4rem 0 0.9rem 0;
}

/* ── Hero section ── */
.hero-title {
    font-size: 1.9rem;
    font-weight: 800;
    line-height: 1.2;
    margin: 0;
}
.hero-sub {
    font-size: 0.88rem;
    opacity: 0.65;
    margin-top: 0.3rem;
}

/* ── KPI cards ── */
.kpi-num { 
    font-size: 2rem; 
    font-weight: 800; 
    color: #1A5AFF; 
    line-height: 1; 
}
.kpi-lbl { 
    font-size: 0.72rem; 
    font-weight: 600; 
    opacity: 0.6;
    text-transform: uppercase; 
    letter-spacing: 0.07em; 
    margin-bottom: 0.2rem; 
}
.kpi-card { 
    background: rgba(26,90,255,0.06); 
    border-left: 4px solid #1A5AFF;
    border-radius: 8px; 
    padding: 1rem 1.2rem; 
}

/* ── Metric cards (secondary) ── */
.metric-card {
    background: rgba(26,90,255,0.03);
    border: 1px solid rgba(26,90,255,0.15);
    border-radius: 6px;
    padding: 0.8rem;
    text-align: center;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #1A5AFF;
}
.metric-label {
    font-size: 0.75rem;
    opacity: 0.6;
    margin-top: 0.25rem;
}

/* ── Recommendation boxes ── */
.rec-box {
    background: rgba(26,90,255,0.05);
    border: 1px solid rgba(26,90,255,0.2);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}
.rec-box-title {
    font-weight: 700;
    color: #1A5AFF;
    margin-bottom: 0.4rem;
}

/* ── Hide footer ── */
footer { 
    visibility: hidden; 
}

/* ── Responsive layout ── */
@media (max-width: 768px) {
    .hero-title {
        font-size: 1.4rem;
    }
    .kpi-num {
        font-size: 1.5rem;
    }
}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY HELPERS  —  Theme & style utilities
# ─────────────────────────────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",   # transparent → adapts to light/dark
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", size=11),
    margin=dict(t=44, b=28, l=8, r=8),
    legend=dict(bgcolor="rgba(0,0,0,0)", x=0, y=1),
    hovermode="x unified",
)


def _theme(fig: go.Figure) -> go.Figure:
    """Apply Kayfa theme to any Plotly figure. Transparent background = dark-mode safe."""
    fig.update_layout(**_LAYOUT)
    fig.update_xaxes(
        gridcolor="rgba(26,90,255,0.1)",
        linecolor="rgba(26,90,255,0.2)", 
        tickfont_size=10,
        showgrid=True,
    )
    fig.update_yaxes(
        gridcolor="rgba(26,90,255,0.1)",
        linecolor="rgba(26,90,255,0.2)", 
        tickfont_size=10,
        showgrid=True,
    )
    return fig


def _add_avg_line(fig: go.Figure, y_val: float,
                  label: str = "Company Average") -> go.Figure:
    """
    Add a named dashed reference line WITH a legend entry.
    Rubric: 'Any reference line must be named and shown in the legend.'
    """
    fig.add_hline(y=y_val, line_dash="dash",
                  line_color=AMBER, line_width=2)
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines",
        line=dict(dash="dash", color=AMBER, width=2),
        name=label, showlegend=True,
    ))
    return fig


def _insight(text: str):
    """Render an insight box."""
    st.markdown(f"<div class='insight-box'>{text}</div>",
                unsafe_allow_html=True)


def _cta(text: str):
    """Render a call-to-action (green) box."""
    st.markdown(f"<div class='cta-box'>{text}</div>",
                unsafe_allow_html=True)


def _risk(text: str):
    """Render a risk (red) box."""
    st.markdown(f"<div class='risk-card'>{text}</div>",
                unsafe_allow_html=True)


def _qbadge(label: str):
    """Render a Q-number badge."""
    st.markdown(f"<span class='q-badge'>{label}</span>",
                unsafe_allow_html=True)


def _section(title: str):
    """Render a section title."""
    st.markdown(f"<div class='section-title'>{title}</div>",
                unsafe_allow_html=True)


def _logo_block():
    """Logo with Arabic fallback (right-aligned on homepage)."""
    try:
        st.image("company_logo2.png", width=120)
    except Exception:
        st.markdown(
            "<div style='font-size:2.2rem;font-weight:900;"
            "color:#1A5AFF;letter-spacing:-1px;text-align:center;'>كيف</div>",
            unsafe_allow_html=True,
        )


def _safe_pct(num: float, denom: float, fallback: float = 0.0) -> float:
    """Division-by-zero guard for percentage calculations."""
    return (num / denom * 100) if denom > 0 else fallback


def _safe_first(series: pd.Series, fallback: float = 0.0) -> float:
    """Guard against .values[0] on empty Series."""
    return float(series.values[0]) if len(series) > 0 else fallback


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING & VALIDATION  —  cached, runs once per session
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="🔄 Loading & validating data…")
def get_data():
    """
    Load, clean, and validate all data and aggregations.
    Caches results to avoid recomputation on interaction.
    """
    try:
        # Load and clean
        df = load_and_clean("train.csv", "test.csv")
        
        # Run validation suite
        test_data_completeness(df)
        
        # Compute aggregations
        aggs = compute_aggregration(df)
        q = compute_q_aggregations(df)
        
        # Validate aggregations
        overall_rate = aggs["overall_rate"]
        test_aggregation_output(aggs, q, overall_rate)
        
        return df, aggs, q
    except Exception as e:
        st.error(f"❌ **Data Loading Failed**: {str(e)}")
        st.info("Please check that train.csv and test.csv are in the working directory.")
        st.stop()


df, aggs, q = get_data()
overall_rate = aggs["overall_rate"] * 100   # scalar % (0–100)


# ─────────────────────────────────────────────────────────────────────────────
# INJECT CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED SIDEBAR  (defined before pg.run() → appears on EVERY page)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo — fixed at top of sidebar
    st.markdown("<div class='sidebar-logo-container'>", unsafe_allow_html=True)
    try:
        st.image("company_logo2.png", use_container_width=True)
    except Exception:
        st.markdown(
            "<div style='font-size:1.8rem;font-weight:900;text-align:center;"
            "letter-spacing:-1px;padding:0.4rem 0;color:white;'>كيف</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔍 **Filters**")

    # ── Filter controls ───────────────────────────────────────────────────
    all_roles   = sorted(df["job_role"].unique().tolist())
    all_genders = sorted(df["gender"].unique().tolist())
    all_levels  = df["job_level"].cat.categories.tolist()   # preserve ordinal order
    all_sizes   = df["company_size"].cat.categories.tolist()

    sel_roles   = st.multiselect("🏢 Job Role",    all_roles,   default=all_roles, key="sel_roles")
    sel_genders = st.multiselect("👥 Gender",       all_genders, default=all_genders, key="sel_genders")
    sel_levels  = st.multiselect("📊 Job Level",    all_levels,  default=all_levels, key="sel_levels")
    sel_sizes   = st.multiselect("🏭 Company Size", all_sizes,   default=all_sizes, key="sel_sizes")

    age_min, age_max = int(df["age"].min()), int(df["age"].max())
    sel_age = st.slider("👤 Age Range", age_min, age_max, (age_min, age_max), key="sel_age")

    sel_remote = st.radio("🏠 Work Location",
                          ["All", "Remote Only", "On-site Only"], index=0, key="sel_remote")
    sel_ot     = st.radio("⏰ Overtime",
                          ["All", "With Overtime", "No Overtime"], index=0, key="sel_ot")

    st.markdown("---")
    st.caption("Kayfa · Week 1 · Data Analytics Track")


# ─────────────────────────────────────────────────────────────────────────────
# FILTER MASK  —  single O(n) boolean pass
# ─────────────────────────────────────────────────────────────────────────────
mask = (
    df["job_role"].isin(sel_roles)
    & df["gender"].isin(sel_genders)
    & df["job_level"].isin(sel_levels)
    & df["company_size"].isin(sel_sizes)
    & df["age"].between(sel_age[0], sel_age[1])
)
if sel_remote == "Remote Only":
    mask &= df["remote_work"] == "Yes"
elif sel_remote == "On-site Only":
    mask &= df["remote_work"] == "No"
if sel_ot == "With Overtime":
    mask &= df["overtime"] == "Yes"
elif sel_ot == "No Overtime":
    mask &= df["overtime"] == "No"

dff = df[mask]

# ── Empty-filter guard ────────────────────────────────────────────────────
if len(dff) == 0:
    st.warning("⚠️ **No employees match the current filters.** Adjust the sidebar to view results.")
    st.stop()

kpis = filtered_kpis(dff)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED KPI ROW  (displayed at top of every page)
# ─────────────────────────────────────────────────────────────────────────────
def _kpi_row():
    """Display 4-column KPI summary at top of each page."""
    delta = kpis["rate"] - overall_rate
    sign  = "▲" if delta > 0 else "▼"
    clr   = RED if delta > 0 else GREEN
    delta_html = (f"<span style='font-size:0.78rem;color:{clr};font-weight:600;'>"
                  f"{sign} {abs(delta):.1f}pp vs avg</span>")

    k1, k2, k3, k4 = st.columns(4)
    for col, lbl, val, sub in [
        (k1, "Total Employees",     f"{kpis['total']:,}",
         f"of {aggs['total_employee']:,}"),
        (k2, "Attrition Rate",      f"{kpis['rate']:.1f}%",    
         delta_html),
        (k3, "Avg Monthly Income",  f"${kpis['avg_income']:,.0f}", 
         "filtered group"),
        (k4, "Avg Tenure",          f"{kpis['avg_tenure']:.1f} yrs", 
         "at company"),
    ]:
        with col:
            sub_html = (f"<span style='font-size:0.78rem;opacity:0.6;'>{sub}</span>"
                        if isinstance(sub, str) and "$" not in sub and "▲" not in sub
                        else f"<span style='font-size:0.78rem;'>{sub}</span>")
            st.markdown(
                f"<div class='kpi-card'>"
                f"<div class='kpi-lbl'>{lbl}</div>"
                f"<div class='kpi-num'>{val}</div>"
                f"{sub_html}</div>",
                unsafe_allow_html=True,
            )


# ═════════════════════════════════════════════════════════════════════════════
#  PAGE FUNCTIONS  —  Closes over df, dff, aggs, q, overall_rate, kpis
# ═════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1  ·  OVERVIEW  (Q1 + Executive Summary)
# ─────────────────────────────────────────────────────────────────────────────
def page_overview():
    """
    Q1: The Headline
    What share of employees left overall, and which job role is losing the most people?
    """
    # ── Hero header ──────────────────────────────────────────────────────────
    col_title, _, col_logo = st.columns([6, 1, 2])
    with col_title:
        st.markdown(
            "<p class='hero-sub'>Week #1 Task:</p>"
            "<h1 class='hero-title'>Workforce Retention Intelligence</h1>"
            "<p class='hero-sub'>HR Analytics · Kayfa AI & Data Analytics Internship"
            " · 74,498 synthetic records</p>",
            unsafe_allow_html=True,
        )
    with col_logo:
        _logo_block()

    st.markdown("---")
    _kpi_row()
    st.markdown("---")

    # ── Q1 ───────────────────────────────────────────────────────────────────
    _qbadge("Q1 · The Headline")
    _section("Who Is Leaving — and Where to Look First")

    c1, c2 = st.columns([3, 2])

    with c1:
        # Attrition by role — horizontal bar
        role_data = (
            dff.groupby("job_role", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "job_role": "Job Role"})
            .sort_values("Attrition Rate (%)", ascending=True)
        )
        
        if len(role_data) > 0:
            fig = px.bar(
                role_data, x="Attrition Rate (%)", y="Job Role",
                orientation="h",
                title="Attrition Rate by Job Role",
                color="Attrition Rate (%)",
                color_continuous_scale=BLUE_SEQ,
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{text:.1f}%",
                textposition="outside",
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis_title="", xaxis_title="Attrition Rate (%)")
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), use_container_width=True)

            top_role = role_data.iloc[-1]
            pp_above = top_role['Attrition Rate (%)'] - overall_rate
            _insight(
                f"<b>{top_role['Job Role']}</b> leads at "
                f"<b>{top_role['Attrition Rate (%)']:.1f}%</b> — "
                f"{pp_above:+.1f}pp vs the {overall_rate:.1f}% company average. "
                f"The <b>spread is narrow (~2pp)</b>, meaning this is a "
                f"<b>company-wide condition</b>, not a role-specific problem."
            )
            _cta(
                "<b>🎯 Action:</b> Don't target one department in isolation. "
                "A company-wide policy response — remote work expansion, structured "
                "promotion pathways, overtime audit — will move the needle more than "
                "role-by-role band-aids."
            )

    with c2:
        # Donut: stayed vs left
        stayed = int((dff["attrition"] == 0).sum())
        left   = int((dff["attrition"] == 1).sum())
        total  = stayed + left
        retention_rate = _safe_pct(stayed, total)

        fig = go.Figure(go.Pie(
            labels=["Stayed", "Left"],
            values=[stayed, left],
            hole=0.62,
            marker_colors=[KB_LIGHT, KB],
            textinfo="percent+label",
            hovertemplate="%{label}: %{value:,}<br>%{percent}<extra></extra>",
        ))
        fig.update_layout(
            title="Workforce Split",
            annotations=[dict(
                text=f"<b>{_safe_pct(left, total):.1f}%</b><br>Left",
                x=0.5, y=0.5, font_size=15, font_color=KB, showarrow=False,
            )],
        )
        st.plotly_chart(_theme(fig), use_container_width=True)
        _insight(
            f"<b>{left:,}</b> left · <b>{stayed:,}</b> retained · "
            f"Retention: <b>{retention_rate:.1f}%</b>"
        )

    # ── Executive summary ─────────────────────────────────────────────────────
    st.markdown("---")
    _section("Executive Summary")

    income_left   = dff[dff["attrition"]==1]["monthly_income"].mean()
    income_stayed = dff[dff["attrition"]==0]["monthly_income"].mean()
    income_gap    = _safe_pct(income_left - income_stayed, income_stayed)

    avg_age_left   = dff[dff["attrition"]==1]["age"].mean()
    avg_age_stayed = dff[dff["attrition"]==0]["age"].mean()

    s1, s2 = st.columns(2)
    with s1:
        st.markdown("##### 🔍 Key Findings")
        severity = ("🔴 **HIGH RISK**" if kpis["rate"] > overall_rate + 5
                    else "🟢 **BELOW AVERAGE**" if kpis["rate"] < overall_rate - 5
                    else "🟡 **NEAR AVERAGE**")
        delta_dir = ("above" if kpis["rate"] >= overall_rate else "below")
        st.error(f"{severity} — {kpis['rate']:.1f}% attrition is "
                f"{abs(kpis['rate']-overall_rate):.1f}pp {delta_dir} "
                f"the {overall_rate:.1f}% average")
        st.warning(f"💰 Salary gap: **{abs(income_gap):.1f}%** — "
                f"money is **NOT** the primary driver")
        st.info(f"👥 Leavers average **{avg_age_left:.0f} yrs** vs "
                f"**{avg_age_stayed:.0f} yrs** stayers — "
                f"**younger employees at higher risk**")
    with s2:
        st.markdown("##### 💡 Top Recommendations (Ranked by Impact)")
        st.success("🏠 **Expand remote work** — 28pp attrition gap")
        st.success("🚀 **Build promotion pathways** — 26pp effect size")
        st.success("⚖️ **Audit overtime** — 6pp direct effect, compounds other factors")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2  ·  WORKLOAD & FLEXIBILITY  (Q2, Q3)
# ─────────────────────────────────────────────────────────────────────────────
def page_workload():
    """Q2: Overtime | Q3: Remote Work"""
    st.markdown("## ⏰ Workload & Flexibility")
    _kpi_row()
    st.markdown("---")

    # ── Q2: OVERTIME ──────────────────────────────────────────────────────────
    _qbadge("Q2 · Overtime Burden")
    _section("Does Overtime Predict Attrition?")

    if "overtime" not in dff.columns:
        st.warning("⚠️ Overtime column not available.")
    else:
        ot = (
            dff.groupby("overtime", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "overtime": "Overtime"})
        )
        c1, c2 = st.columns([2, 3])
        with c1:
            fig = px.bar(
                ot, x="Overtime", y="Attrition Rate (%)",
                title="Overtime vs Attrition Rate",
                color="Overtime",
                color_discrete_map={"Yes": KB, "No": KB_LIGHT},
                text="Attrition Rate (%)",
            )
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(
                xaxis_title="Works Overtime",
                yaxis_title="Attrition Rate (%)",
                showlegend=False,
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), use_container_width=True)

        with c2:
            ot_yes = _safe_first(ot[ot["Overtime"]=="Yes"]["Attrition Rate (%)"])
            ot_no  = _safe_first(ot[ot["Overtime"]=="No"]["Attrition Rate (%)"])
            gap    = ot_yes - ot_no

            st.markdown("<br>", unsafe_allow_html=True)
            _insight(
                f"Overtime workers leave at <b>{ot_yes:.1f}%</b> vs "
                f"<b>{ot_no:.1f}%</b> for those who don't — <b>{gap:.1f}pp gap</b>. "
                f"At 74.5k employees, {gap:.1f}pp = ~{int(74500*gap/100):,} additional departures "
                f"directly attributable to overtime burnout."
            )
            _cta(
                "<b>🎯 HR Action:</b> Conduct department-level overtime audit. "
                "Identify teams with chronic >10% exposure and redistribute workload. "
                "<b>Target:</b> Reduce overtime headcount 20% within 2 quarters."
            )

    st.markdown("---")

    # ── Q3: REMOTE WORK ───────────────────────────────────────────────────────
    _qbadge("Q3 · Remote Work")
    _section("Does Remote Work Keep People?")

    if "remote_work" not in dff.columns:
        st.warning("⚠️ Remote work column not available.")
    else:
        remote = (
            dff.groupby("remote_work", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)",
                              "remote_work": "Work Location"})
        )
        remote["Work Location"] = remote["Work Location"].map(
            {"Yes": "Remote", "No": "On-site"})

        pct_remote = _safe_pct(
            (dff["remote_work"]=="Yes").sum(), len(dff))

        c1, c2 = st.columns([2, 3])
        with c1:
            fig = px.bar(
                remote, x="Work Location", y="Attrition Rate (%)",
                title="Remote vs On-site Attrition",
                color="Work Location",
                color_discrete_map={"Remote": KB, "On-site": KB_LIGHT},
                text="Attrition Rate (%)",
            )
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Attrition Rate (%)",
                showlegend=False,
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), use_container_width=True)

        with c2:
            r_remote  = _safe_first(
                remote[remote["Work Location"]=="Remote"]["Attrition Rate (%)"])
            r_onsite  = _safe_first(
                remote[remote["Work Location"]=="On-site"]["Attrition Rate (%)"])
            gap = r_onsite - r_remote

            st.markdown("<br>", unsafe_allow_html=True)
            _insight(
                f"Remote workers leave at <b>{r_remote:.1f}%</b> — "
                f"<b>{gap:.1f}pp lower</b> than on-site at {r_onsite:.1f}%. "
                f"This is the <b>2nd largest effect size</b> in the dataset. "
                f"<b>BUT:</b> only {pct_remote:.1f}% work remote — "
                f"effect is real but reflects selection bias (remote-eligible roles "
                f"may attract more committed staff)."
            )
            _cta(
                "<b>🎯 HR Action:</b> Run 90-day remote pilot for on-site roles "
                "with >50% attrition. Even shifting 10% to remote could prevent "
                f"~{int(dff.shape[0]*0.10*gap/100):,} departures. "
                "Track pre/post attrition to confirm causation."
            )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3  ·  PAY & JOB LEVEL  (Q4)
# ─────────────────────────────────────────────────────────────────────────────
def page_pay_level():
    """Q4: Pay Fairness — Within-level income quartiles"""
    st.markdown("## 💰 Pay & Job Level")
    _kpi_row()
    st.markdown("---")

    _qbadge("Q4 · Pay Fairness Within Levels")
    _section("Does Higher Pay Within a Job Level Reduce Attrition?")

    jl = (
        dff.groupby("job_level", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)", "job_level": "Job Level"})
    )

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            jl, x="Job Level", y="Attrition Rate (%)",
            title="Attrition Rate by Job Level",
            color="Attrition Rate (%)",
            color_continuous_scale=BLUE_SEQ,
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Job Level", yaxis_title="Attrition Rate (%)")
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), use_container_width=True)

        entry = _safe_first(jl[jl["Job Level"]=="Entry"]["Attrition Rate (%)"])
        senior = _safe_first(jl[jl["Job Level"]=="Senior"]["Attrition Rate (%)"])
        _insight(
            f"Entry-level at <b>{entry:.1f}%</b>, Senior at <b>{senior:.1f}%</b> — "
            f"<b>{entry-senior:.0f}pp gap</b>. "
            f"Job Level is the **single strongest driver** (43pp effect)."
        )

    with c2:
        pay_data = q.get("pay_by_level_quartile", pd.DataFrame())
        if not pay_data.empty:
            fig = px.bar(
                pay_data,
                x="income_quartile", y="Attrition Rate (%)",
                color="job_level",
                barmode="group",
                title="Attrition by Pay Quartile Within Job Level",
                color_discrete_sequence=[KB_LIGHT, "#7FA8FF", KB],
                labels={"income_quartile": "Pay Quartile",
                        "job_level": "Job Level",
                        "Attrition Rate (%)": "Attrition Rate (%)"},
            )
            fig.update_layout(
                xaxis_title="Pay Quartile (within Job Level)",
                yaxis_title="Attrition Rate (%)",
                legend_title="Job Level",
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), use_container_width=True)

    _insight(
        "Within the same job level, bottom → top pay quartile reduces attrition by only "
        "<b>~2pp</b> (e.g., Entry: 64.5% → 62.5%). "
        "Pay raises within a band are largely ineffective. "
        "<b>The level itself is what matters</b> — "
        "Entry employees leave at 63% regardless of compensation."
    )
    _cta(
        "<b>🎯 Reframe the pay debate:</b> Don't give Entry-level staff a 10% raise. "
        "Invest that budget in structured **promotion pathways** to Mid-level. "
        "Every promotion eliminates ~18pp attrition risk. "
        "<b>Target:</b> Reduce time-to-first-promotion by 6 months."
    )

    st.markdown("---")
    _section("Income Distribution — Stayed vs. Left")

    fig = px.box(
        dff,
        x=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        y="monthly_income",
        title="Monthly Income Distribution by Attrition Status",
        color=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        color_discrete_map=ATTRITION_MAP,
        points=False,
        labels={"x": "Status", "monthly_income": "Monthly Income ($)"},
    )
    fig.update_layout(xaxis_title="", yaxis_title="Monthly Income ($)",
                      showlegend=False)
    st.plotly_chart(_theme(fig), use_container_width=True)
    _insight(
        "Leavers and stayers have nearly identical income distributions "
        "(median gap < 1%). <b>Compensation is NOT the primary driver.</b> "
        "Leadership must resist the instinct to solve attrition with blanket raises."
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4  ·  ENGAGEMENT & LIFE STAGE  (Q5, Q6, Q7)
# ─────────────────────────────────────────────────────────────────────────────
def page_engagement():
    """Q5: Tenure timeline | Q6: WLB × Satisfaction | Q7: Life stage"""
    st.markdown("## 🧠 Engagement & Life Stage")
    _kpi_row()
    st.markdown("---")

    # ── Q5: RETENTION TIMELINE ────────────────────────────────────────────────
    _qbadge("Q5 · The Retention Timeline")
    _section("When Are Employees Most Likely to Leave?")

    tenure_data = q.get("attrition_by_tenure", pd.DataFrame())
    if not tenure_data.empty:
        fig = px.bar(
            tenure_data,
            x="tenure_band", y="Attrition Rate (%)",
            title="Attrition Rate by Company Tenure",
            color="Attrition Rate (%)",
            color_continuous_scale=BLUE_SEQ,
            text="Attrition Rate (%)",
            labels={"tenure_band": "Tenure Band"},
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Years at Company",
                          yaxis_title="Attrition Rate (%)")
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), use_container_width=True)

        peak_band = tenure_data.loc[tenure_data["Attrition Rate (%)"].idxmax()]
        low_band  = tenure_data.loc[tenure_data["Attrition Rate (%)"].idxmin()]
        _insight(
            f"Attrition peaks at <b>{peak_band['tenure_band']}</b> "
            f"(<b>{peak_band['Attrition Rate (%)']:.1f}%</b>) and stays elevated "
            f"through year 10. Long-tenure (20+ yrs) drops to <b>{low_band['Attrition Rate (%)']:.1f}%</b>. "
            f"<b>No 'honeymoon cliff'</b> — attrition is high from day one."
        )
        _cta(
            "<b>🎯 Target the first 5 years:</b> Redesign onboarding for 0–2yr window. "
            "Introduce career check-in at 18 months — where mid-career drift becomes visible. "
            "Long-tenure employees are stable; protect them through leadership pathways."
        )

    st.markdown("---")

    # ── Q6: WLB × SATISFACTION HEATMAP ─────────────────────────────────────
    _qbadge("Q6 · Engagement Warning Signs")
    _section("Which WLB + Satisfaction Combination Is the Danger Zone?")

    cross_data = q.get("wlb_x_satisfaction", pd.DataFrame())
    if not cross_data.empty:
        pivot = cross_data.pivot(
            index="Work-Life Balance",
            columns="Job Satisfaction",
            values="Attrition Rate (%)",
        )
        wlb_order = ["Poor", "Fair", "Good", "Excellent"]
        sat_order = ["Low", "Medium", "High", "Very High"]
        pivot = pivot.reindex(index=[x for x in wlb_order if x in pivot.index],
                              columns=[x for x in sat_order if x in pivot.columns])

        fig = go.Figure(go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[[0, KB_LIGHT], [0.5, KB], [1, KB_DARK]],
            zmin=25, zmax=75,
            text=pivot.values,
            texttemplate="%{text:.1f}%",
            hovertemplate="WLB: %{y}<br>Satisfaction: %{x}<br>"
                          "Attrition: %{z:.1f}%<extra></extra>",
            colorbar=dict(title="Attrition %"),
        ))
        fig.update_layout(
            title="Attrition Rate: Work-Life Balance × Job Satisfaction",
            xaxis_title="Job Satisfaction",
            yaxis_title="Work-Life Balance",
            height=400,
        )
        st.plotly_chart(_theme(fig), use_container_width=True)

        _insight(
            "Danger zone: <b>Poor WLB + Low Satisfaction = 67.0%</b> attrition. "
            "But even <b>Very High satisfaction doesn't protect</b> those with Poor WLB (64.9%). "
            "<b>WLB is dominant</b> — satisfaction is secondary."
        )
        _cta(
            "<b>🎯 Manager early-warning signals:</b> An employee who loves their work "
            "but reports poor balance is at just as high risk as one who is dissatisfied. "
            "Flag any employee with Poor/Fair WLB in quarterly pulse checks."
        )

    st.markdown("---")

    # ── Q7: LIFE STAGE ────────────────────────────────────────────────────────
    _qbadge("Q7 · Life Stage")
    _section("Does Life Stage Change Who Leaves?")

    c1, c2, c3 = st.columns(3)

    with c1:
        age_data = q.get("attrition_by_age_group", pd.DataFrame())
        if not age_data.empty:
            fig = px.bar(
                age_data, x="Age Group", y="Attrition Rate (%)",
                title="Attrition by Age Group",
                color="Attrition Rate (%)",
                color_continuous_scale=BLUE_SEQ,
                text="Attrition Rate (%)",
            )
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_coloraxes(showscale=False)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), use_container_width=True)

    with c2:
        marital_data = q.get("attrition_by_marital", pd.DataFrame())
        if not marital_data.empty:
            fig = px.bar(
                marital_data, x="Marital Status", y="Attrition Rate (%)",
                title="Attrition by Marital Status",
                color="Marital Status",
                color_discrete_sequence=[KB, "#7FA8FF", KB_LIGHT],
                text="Attrition Rate (%)",
            )
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(showlegend=False)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), use_container_width=True)

    with c3:
        dep_data = q.get("attrition_by_dependents", pd.DataFrame())
        if not dep_data.empty:
            fig = px.line(
                dep_data, x="Number of Dependents", y="Attrition Rate (%)",
                title="Attrition by Number of Dependents",
                markers=True, line_shape="spline",
            )
            fig.update_traces(line_color=KB, marker_color=KB, marker_size=8)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), use_container_width=True)

    _insight(
        "Highest-risk: <b>young, single employees (18–25)</b> — 53.1% (age) × 66.8% (marital). "
        "Employees with 4+ dependents leave less (35–37%) — "
        "<b>family responsibility = stability.</b> "
        "This is not age — it's rootedness."
    )
    _cta(
        "<b>🎯 Target single, young employees specifically:</b> "
        "Build community & belonging programmes (mentorship, peer networks, team budgets). "
        "These create organisational roots and directly address the psychological driver."
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5  ·  CAREER GROWTH  (Q8)
# ─────────────────────────────────────────────────────────────────────────────
def page_career():
    """Q8: Career Stagnation — Promotions, leadership, innovation"""
    st.markdown("## 🚀 Career Growth")
    _kpi_row()
    st.markdown("---")

    _qbadge("Q8 · Career Stagnation")
    _section("Does Feeling Stuck Drive Attrition?")

    c1, c2 = st.columns(2)

    with c1:
        promo_data = q.get("attrition_by_promotions", pd.DataFrame())
        if not promo_data.empty:
            fig = px.line(
                promo_data,
                x="Number of Promotions", y="Attrition Rate (%)",
                title="Attrition Rate vs Number of Promotions",
                markers=True, line_shape="spline",
            )
            fig.update_traces(line_color=KB, marker_color=KB, marker_size=9)
            _add_avg_line(fig, overall_rate)
            fig.update_layout(
                xaxis_title="Number of Promotions Received",
                yaxis_title="Attrition Rate (%)",
            )
            st.plotly_chart(_theme(fig), use_container_width=True)

            p0 = _safe_first(
                promo_data[promo_data["Number of Promotions"]==0]["Attrition Rate (%)"])
            p4 = _safe_first(
                promo_data[promo_data["Number of Promotions"]==4]["Attrition Rate (%)"])
            _insight(
                f"<b>0 promotions → {p0:.1f}%</b> attrition. "
                f"<b>4 promotions → {p4:.1f}%</b> attrition. "
                f"<b>Attrition cut in half</b> by promotion. "
                f"Non-linear: 0–2 promos ~49%, but reaching 3 drops sharply to ~25%. "
                f"<b>Promotion threshold effect.</b>"
            )

    with c2:
        for col_key, label, color_map in [
            ("attrition_by_leadership_opportunities", "Leadership Opportunities", 
             {"Yes": KB, "No": KB_LIGHT}),
            ("attrition_by_innovation_opportunities", "Innovation Opportunities",
             {"Yes": KB, "No": KB_LIGHT}),
        ]:
            opp_data = q.get(col_key, pd.DataFrame())
            if not opp_data.empty and len(opp_data.columns) >= 2:
                x_col = opp_data.columns[0]
                fig = px.bar(
                    opp_data, x=x_col, y="Attrition Rate (%)",
                    title=f"Attrition by {label}",
                    color=x_col,
                    color_discrete_map=color_map,
                    text="Attrition Rate (%)",
                )
                fig.update_traces(texttemplate="%{text:.1f}%",
                                  textposition="outside")
                fig.update_layout(xaxis_title=label,
                                  yaxis_title="Attrition Rate (%)",
                                  showlegend=False)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig), use_container_width=True)

    st.markdown("---")
    _section("The 'Fully Stuck' Profile")

    stuck_n    = q.get("stuck_n", 0)
    stuck_rate = q.get("stuck_rate", 0.0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{stuck_n:,}</div>"
            f"<div class='metric-label'>Fully Stuck Employees</div>"
            f"<div style='font-size:0.7rem;margin-top:0.3rem;opacity:0.6;'>"
            f"0 promos + no leadership + no innovation</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{stuck_rate:.1f}%</div>"
            f"<div class='metric-label'>Their Attrition Rate</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    with col3:
        delta_stuck = stuck_rate - overall_rate
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value' style='color:{RED};'>{delta_stuck:+.1f}pp</div>"
            f"<div class='metric-label'>vs Company Average</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    _risk(
        f"<b>{stuck_n:,} employees</b> (0 promotions, no leadership, no innovation) "
        f"show <b>{stuck_rate:.1f}%</b> attrition — {delta_stuck:+.1f}pp above average. "
        f"<b>This is not fringe — it's ~40% of the workforce.</b> "
        f"Career stagnation is systemic."
    )
    _cta(
        f"<b>🎯 Growth & Mobility:</b> Establish 'minimum viable growth' — "
        f"every employee needs at least one growth dimension (promotion track, "
        f"leadership project, innovation initiative) within 18 months. "
        f"<b>Action:</b> Identify the {stuck_n:,} and assign each a 90-day "
        f"development plan. Target: move 30% out within 2 quarters."
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 6  ·  RISK & STRATEGY  (Q9, Q10)
# ─────────────────────────────────────────────────────────────────────────────
def page_risk():
    """Q9: Highest-risk profile | Q10: Driver ranking"""
    st.markdown("## 🎯 Risk & Strategy")
    _kpi_row()
    st.markdown("---")

    # ── Q9: HIGHEST-RISK PROFILE ──────────────────────────────────────────────
    _qbadge("Q9 · Highest-Risk Employee Profile")
    _section("Who Is Most Likely to Leave — and How Many?")

    risk_n    = q.get("risk_profile_n", 0)
    risk_rate = q.get("risk_profile_rate", 0.0)
    risk_lift = risk_rate - overall_rate

    _risk(
        f"<b>Profile:</b> Poor WLB + Overtime + 0 Promotions + No Leadership<br><br>"
        f"<b>Attrition: {risk_rate:.1f}%</b> ({risk_lift:+.1f}pp vs avg) · "
        f"<b>{risk_n:,} employees</b> match today"
    )

    c1, c2 = st.columns(2)

    with c1:
        factors = pd.DataFrame({
            "Factor": ["Poor WLB", "Works Overtime",
                       "Zero Promotions", "No Leadership"],
            "Attrition Rate (%)": [60.2, 51.5, 49.3, 47.6],
        })
        fig = px.bar(
            factors.sort_values("Attrition Rate (%)"),
            x="Attrition Rate (%)", y="Factor", orientation="h",
            title="Standalone Attrition of Each Risk Factor",
            color="Attrition Rate (%)",
            color_continuous_scale=BLUE_SEQ,
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_coloraxes(showscale=False)
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), use_container_width=True)

    with c2:
        comparison = pd.DataFrame({
            "Group": ["Company Average", "Risk Profile"],
            "Attrition Rate (%)": [overall_rate, risk_rate],
        })
        fig = px.bar(
            comparison, x="Group", y="Attrition Rate (%)",
            title="Risk Profile vs Company Average",
            color="Group",
            color_discrete_map={"Company Average": KB_LIGHT, "Risk Profile": KB},
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(showlegend=False, xaxis_title="")
        st.plotly_chart(_theme(fig), use_container_width=True)

    _insight(
        f"This profile shows <b>{risk_rate:.1f}%</b> attrition — "
        f"<b>1.4× the company average</b>. "
        f"With {risk_n:,} employees matching it, this is actionable. "
        f"If half leave: ~{int(risk_n * risk_rate/100):,} departures from one cohort. "
        f"The 4 factors are individually manageable — together they compound."
    )
    _cta(
        f"<b>🎯 Immediate Action:</b> Export list of {risk_n:,} and assign HR partner "
        f"touchpoint within 30 days. Target: eliminate ≥2 of 4 risk factors per employee "
        f"(e.g., approve remote + assign leadership project). "
        f"20% success = prevent ~{int(risk_n * risk_rate/100 * 0.2):,} departures."
    )

    st.markdown("---")

    # ── Q10: WHAT MOVES THE NEEDLE ───────────────────────────────────────────
    _qbadge("Q10 · What Moves the Needle")
    _section("If HR Could Fix One Thing Next Quarter — What Does Data Say?")

    drivers = q.get("driver_ranking", pd.DataFrame())
    if not drivers.empty:
        fig = px.bar(
            drivers,
            x="Effect (pp)", y="Driver",
            orientation="h",
            title="Top Attrition Drivers — Effect Size (Best vs Worst Group)",
            color="Effect (pp)",
            color_continuous_scale=BLUE_SEQ,
            text="Effect (pp)",
        )
        fig.update_traces(texttemplate="%{text:.1f}pp", textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(
            xaxis_title="Attrition Rate Difference (percentage points)",
            yaxis_title="",
        )
        st.plotly_chart(_theme(fig), use_container_width=True)

    st.markdown("### 🏆 Ranked Recommendations")
    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown(
            "<div class='risk-card'><b>#1 · Expand Remote Work</b><br><br>"
            "Effect: <b>28.1pp</b><br>"
            "On-site: 52.8% → Remote: 24.7%<br><br>"
            "Only 19.1% currently remote. Fastest policy lever. "
            "10% headcount shift = ~2,000 retained.</div>",
            unsafe_allow_html=True,
        )

    with r2:
        st.markdown(
            "<div class='rec-box'><b>#2 · Build Promotion Pathways</b><br><br>"
            "Effect: <b>26.0pp</b><br>"
            "0 promos: 49.3% → 4 promos: 23.3%<br><br>"
            "Non-linear — jump at 3 promotions. "
            "Accelerate time-to-3rd for at-risk cohorts.</div>",
            unsafe_allow_html=True,
        )

    with r3:
        st.markdown(
            "<div class='rec-box'><b>#3 · Fix Work-Life Balance</b><br><br>"
            "Effect: <b>24.5pp</b><br>"
            "Poor: 60.2% → Excellent: 35.7%<br><br>"
            "WLB overrides job satisfaction. Start with overtime "
            "reduction & flexible scheduling.</div>",
            unsafe_allow_html=True,
        )

    _insight(
        "<b>Why #1 wins:</b> "
        "Remote expansion is a **2-week policy change**; promotion takes 12–18 months. "
        "Effect size is real (28.1pp), mechanism is plausible, cost is near-zero. "
        "Shifting 5% of on-site workforce (~2,850 people) to remote at same improvement "
        f"would prevent ~{int(2850 * 0.281):,} departures per annual cohort."
    )

    st.markdown("---")
    st.markdown("### 📅 90-Day Action Roadmap")
    
    roadmap = pd.DataFrame({
        "Priority": ["🔴", "🔴", "🟠", "🟠", "🟡", "🟡"],
        "Action": [
            "Launch remote work
