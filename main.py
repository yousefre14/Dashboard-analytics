"""
main.py  —  HR Attrition Dashboard (COMPLETE - ALL 10 QUESTIONS)
Kayfa AI & Data Analytics Internship · Week 1

FEATURES:
  ✓ All 10 questions fully answered (Q1-Q10)
  ✓ Logo visibility fixed (white background)
  ✓ Improved sidebar colors with UX principles
  ✓ Enhanced attrition chart with better styling
  ✓ Homepage tabs for each question
  ✓ width='stretch' parameter (Streamlit latest)
  ✓ Professional CSS/HTML
  ✓ Dark/light theme support
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict
from PIL import Image
from io import BytesIO
import requests

from Data_Handling import (
    load_and_clean, compute_aggregration,
    compute_q_aggregations, filtered_kpis,
    test_data_completeness, test_aggregation_output,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
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
KB        = "#1A5AFF"
KB_DARK   = "#1245CC"
KB_LIGHT  = "#E8EFFF"
AMBER     = "#F59E0B"
GREEN     = "#16A34A"
RED       = "#DC2626"
WHITE     = "#FFFFFF"
DARK_BG   = "#0F1419"
BLUE_SEQ  = [KB_LIGHT, "#BDD0FF", "#7FA8FF", "#4C84FF", KB, KB_DARK, "#0D31A3", "#081F7A"]
ATTRITION_MAP = {"Stayed": KB_LIGHT, "Left": KB}

# ─────────────────────────────────────────────────────────────────────────────
# ENHANCED CSS WITH BETTER UX
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── SIDEBAR STYLING (UX: High Contrast) ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #1A5AFF 0%, #1245CC 100%) !important;
    width: 300px !important;
    box-shadow: 2px 0 10px rgba(26, 90, 255, 0.2);
}

section[data-testid="stSidebar"] > div:first-child {
    width: 300px !important;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    font-weight: 700;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.3) !important;
    margin: 1rem 0 !important;
}

/* ── LOGO CONTAINER (White background for visibility) ── */
.sidebar-logo-fixed {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(10px);
    padding: 1.2rem 0.8rem;
    border-bottom: 3px solid #1A5AFF;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    text-align: center;
    box-shadow: 0 4px 12px rgba(26,90,255,0.15);
}

.sidebar-logo-fixed img {
    max-width: 140px;
    height: auto;
    border-radius: 6px;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

.sidebar-logo-text {
    font-size: 1.8rem;
    font-weight: 900;
    color: #1A5AFF;
    letter-spacing: -1px;
    margin: 0;
}

.sidebar-logo-subtitle {
    font-size: 0.75rem;
    color: #1245CC;
    margin-top: 0.25rem;
    font-weight: 600;
}

/* ── FILTERS SECTION (Better contrast) ── */
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background: rgba(255,255,255,0.2) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 4px !important;
    font-weight: 500;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.15) !important;
    border: 2px solid rgba(255,255,255,0.25) !important;
    border-radius: 6px !important;
    color: white !important;
    font-weight: 500;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div:hover {
    background: rgba(255,255,255,0.2) !important;
    border-color: rgba(255,255,255,0.4) !important;
}

section[data-testid="stSidebar"] .stRadio > label {
    color: white !important;
    font-weight: 500;
}

section[data-testid="stSidebar"] .stRadio > label:hover {
    color: #E8EFFF !important;
}

section[data-testid="stSidebar"] .stSlider > label {
    color: white !important;
    font-weight: 500;
}

section[data-testid="stSidebar"] .stSlider > div {
    color: white !important;
}

/* ── MAIN CONTENT ── */
.main {
    max-width: 100% !important;
}

[data-testid="stMainBlockContainer"] {
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* ── INSIGHT BOX ── */
.insight-box {
    background: rgba(26,90,255,0.08);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin: 0.5rem 0;
    font-size: 0.84rem;
    line-height: 1.55;
}

.insight-box b {
    color: #1A5AFF;
    font-weight: 700;
}

/* ── CTA BOX ── */
.cta-box {
    background: rgba(22,163,74,0.07);
    border-left: 4px solid #16A34A;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin: 0.5rem 0;
    font-size: 0.84rem;
    line-height: 1.55;
}

.cta-box b {
    color: #16A34A;
    font-weight: 700;
}

/* ── RISK BOX ── */
.risk-card {
    background: rgba(220,38,38,0.07);
    border: 1px solid rgba(220,38,38,0.25);
    border-left: 4px solid #DC2626;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
}

.risk-card b {
    color: #DC2626;
    font-weight: 700;
}

/* ── Q BADGE ── */
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
    box-shadow: 0 2px 4px rgba(26,90,255,0.2);
}

/* ── SECTION TITLE ── */
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    border-bottom: 3px solid #1A5AFF;
    padding-bottom: 0.5rem;
    margin: 1.4rem 0 0.9rem 0;
    color: #1245CC;
}

/* ── HERO ── */
.hero-title {
    font-size: 1.9rem;
    font-weight: 800;
    line-height: 1.2;
    margin: 0;
    color: #1245CC;
}

.hero-sub {
    font-size: 0.88rem;
    opacity: 0.7;
    margin-top: 0.3rem;
}

/* ── KPI CARD ── */
.kpi-card {
    background: linear-gradient(135deg, rgba(26,90,255,0.06) 0%, rgba(26,90,255,0.02) 100%);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 8px rgba(26,90,255,0.1);
    transition: all 0.3s ease;
}

.kpi-card:hover {
    box-shadow: 0 4px 12px rgba(26,90,255,0.15);
    transform: translateY(-2px);
}

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

/* ── METRIC CARD ── */
.metric-card {
    background: rgba(26,90,255,0.03);
    border: 1px solid rgba(26,90,255,0.15);
    border-radius: 6px;
    padding: 1rem;
    text-align: center;
    transition: all 0.3s ease;
}

.metric-card:hover {
    border-color: rgba(26,90,255,0.3);
    background: rgba(26,90,255,0.08);
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

/* ── REC BOX ── */
.rec-box {
    background: rgba(26,90,255,0.05);
    border: 1px solid rgba(26,90,255,0.2);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    transition: all 0.3s ease;
}

.rec-box:hover {
    background: rgba(26,90,255,0.1);
    border-color: rgba(26,90,255,0.4);
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background-color: rgba(26,90,255,0.05);
    padding: 0.5rem;
    border-radius: 8px;
    border-bottom: 2px solid rgba(26,90,255,0.1);
}

.stTabs [aria-selected="true"] {
    color: #1A5AFF !important;
    border-bottom: 3px solid #1A5AFF !important;
}

/* ── FOOTER ── */
footer {
    visibility: hidden;
}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        width: 250px !important;
    }
    .hero-title {
        font-size: 1.4rem;
    }
    .kpi-num {
        font-size: 1.5rem;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LOGO LOADER
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_logo():
    """Load logo from local file or GitHub."""
    try:
        logo = Image.open("company_logo2.png")
        return logo
    except FileNotFoundError:
        try:
            url = "https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/company_logo2.png"
            response = requests.get(url, timeout=5)
            logo = Image.open(BytesIO(response.content))
            return logo
        except Exception:
            return None

logo = load_logo()

# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", size=11),
    margin=dict(t=44, b=28, l=8, r=8),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    hovermode="x unified",
)

def _theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(**_LAYOUT)
    fig.update_xaxes(gridcolor="rgba(26,90,255,0.1)", linecolor="rgba(26,90,255,0.2)", tickfont_size=10)
    fig.update_yaxes(gridcolor="rgba(26,90,255,0.1)", linecolor="rgba(26,90,255,0.2)", tickfont_size=10)
    return fig

def _add_avg_line(fig: go.Figure, y_val: float, label: str = "Company Average") -> go.Figure:
    fig.add_hline(y=y_val, line_dash="dash", line_color=AMBER, line_width=2.5)
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines",
        line=dict(dash="dash", color=AMBER, width=2.5),
        name=label, showlegend=True,
    ))
    return fig

def _insight(text: str):
    st.markdown(f"<div class='insight-box'>{text}</div>", unsafe_allow_html=True)

def _cta(text: str):
    st.markdown(f"<div class='cta-box'>{text}</div>", unsafe_allow_html=True)

def _risk(text: str):
    st.markdown(f"<div class='risk-card'>{text}</div>", unsafe_allow_html=True)

def _qbadge(label: str):
    st.markdown(f"<span class='q-badge'>{label}</span>", unsafe_allow_html=True)

def _section(title: str):
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)

def _safe_pct(num: float, denom: float, fallback: float = 0.0) -> float:
    return (num / denom * 100) if denom > 0 else fallback

def _safe_first(series: pd.Series, fallback: float = 0.0) -> float:
    return float(series.values[0]) if len(series) > 0 else fallback

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="🔄 Loading & validating data…")
def get_data():
    try:
        df = load_and_clean("train.csv", "test.csv")
        test_data_completeness(df)
        aggs = compute_aggregration(df)
        q = compute_q_aggregations(df)
        overall_rate = aggs["overall_rate"]
        test_aggregation_output(aggs, q, overall_rate)
        return df, aggs, q
    except Exception as e:
        st.error(f"❌ **Data Loading Failed**: {str(e)}")
        st.stop()

df, aggs, q = get_data()
overall_rate = aggs["overall_rate"] * 100

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo with white background
    st.markdown("<div class='sidebar-logo-fixed'>", unsafe_allow_html=True)
    if logo is not None:
        st.image(logo, width=130)
    else:
        st.markdown(
            "<p class='sidebar-logo-text'>كيف</p>"
            "<p class='sidebar-logo-subtitle'>Kayfa AI</p>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("### 🔍 Filters", unsafe_allow_html=True)
    
    all_roles   = sorted(df["job_role"].unique().tolist())
    all_genders = sorted(df["gender"].unique().tolist())
    all_levels  = df["job_level"].cat.categories.tolist()
    all_sizes   = df["company_size"].cat.categories.tolist()
    
    sel_roles   = st.multiselect("🏢 Job Role", all_roles, default=all_roles)
    sel_genders = st.multiselect("👥 Gender", all_genders, default=all_genders)
    sel_levels  = st.multiselect("📊 Job Level", all_levels, default=all_levels)
    sel_sizes   = st.multiselect("🏭 Company Size", all_sizes, default=all_sizes)
    
    age_min, age_max = int(df["age"].min()), int(df["age"].max())
    sel_age = st.slider("👤 Age Range", age_min, age_max, (age_min, age_max))
    
    sel_remote = st.radio("🏠 Work Location", ["All", "Remote Only", "On-site Only"], index=0)
    sel_ot = st.radio("⏰ Overtime", ["All", "With Overtime", "No Overtime"], index=0)
    
    st.markdown("---")
    st.caption("Week 1 · Data Analytics Track")

# ─────────────────────────────────────────────────────────────────────────────
# FILTER MASK
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

if len(dff) == 0:
    st.warning("⚠️ No employees match current filters. Adjust sidebar.")
    st.stop()

kpis = filtered_kpis(dff)

# ─────────────────────────────────────────────────────────────────────────────
# SHARED KPI ROW
# ─────────────────────────────────────────────────────────────────────────────
def _kpi_row():
    delta = kpis["rate"] - overall_rate
    sign = "▲" if delta > 0 else "▼"
    clr = RED if delta > 0 else GREEN
    delta_html = f"<span style='color:{clr};font-weight:600;'>{sign} {abs(delta):.1f}pp</span>"
    
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-lbl'>Total Employees</div>"
            f"<div class='kpi-num'>{kpis['total']:,}</div>"
            f"<div style='font-size:0.75rem;opacity:0.6;'>of {aggs['total_employee']:,}</div></div>",
            unsafe_allow_html=True,
        )
    
    with k2:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-lbl'>Attrition Rate</div>"
            f"<div class='kpi-num'>{kpis['rate']:.1f}%</div>"
            f"<div style='font-size:0.75rem;'>{delta_html} vs avg</div></div>",
            unsafe_allow_html=True,
        )
    
    with k3:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-lbl'>Avg Income</div>"
            f"<div class='kpi-num'>${kpis['avg_income']:,.0f}</div>"
            f"<div style='font-size:0.75rem;opacity:0.6;'>filtered</div></div>",
            unsafe_allow_html=True,
        )
    
    with k4:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-lbl'>Avg Tenure</div>"
            f"<div class='kpi-num'>{kpis['avg_tenure']:.1f}</div>"
            f"<div style='font-size:0.75rem;opacity:0.6;'>years</div></div>",
            unsafe_allow_html=True,
        )

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 1: OVERVIEW WITH TABS (Q1-Q10)
# ═════════════════════════════════════════════════════════════════════════════
def page_overview():
    col_title, _, col_logo = st.columns([6, 1, 2])
    with col_title:
        st.markdown(
            "<p class='hero-sub'>Week #1 Task:</p>"
            "<h1 class='hero-title'>Workforce Retention Intelligence</h1>"
            "<p class='hero-sub'>HR Analytics · Kayfa · 74,498 records</p>",
            unsafe_allow_html=True,
        )
    with col_logo:
        if logo is not None:
            st.image(logo, width=120)
        else:
            st.markdown(
                "<div style='text-align:center;font-size:2.2rem;font-weight:900;color:#1A5AFF;'>"
                "كيف</div>",
                unsafe_allow_html=True,
            )
    
    st.markdown("---")
    _kpi_row()
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # TABBED QUESTIONS
    # ════════════════════════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "Q1: Headline",
        "Q2: Overtime",
        "Q3: Remote Work",
        "Q4: Pay Fairness",
        "Q5: Timeline",
        "Q6: Engagement",
        "Q7: Life Stage",
        "Q8: Stagnation",
        "Q9: Risk Profile",
        "Q10: Drivers"
    ])
    
    # ────────────────────────────────────────────────────────────────────────
    # Q1: THE HEADLINE
    # ────────────────────────────────────────────────────────────────────────
    with tab1:
        _qbadge("Q1 · The Headline")
        _section("Who Is Leaving — and Where to Look First")
        
        c1, c2 = st.columns([3, 2])
        
        with c1:
            role_data = (
                dff.groupby("job_role", observed=True)["attrition"]
                .mean().mul(100).round(1).reset_index()
                .rename(columns={"attrition": "Attrition Rate (%)", "job_role": "Job Role"})
                .sort_values("Attrition Rate (%)", ascending=True)
            )
            
            if len(role_data) > 0:
                fig = px.bar(
                    role_data, 
                    x="Attrition Rate (%)", 
                    y="Job Role", 
                    orientation="h",
                    title="Attrition Rate by Job Role",
                    color="Attrition Rate (%)", 
                    color_continuous_scale=BLUE_SEQ,
                    text="Attrition Rate (%)",
                    labels={"Attrition Rate (%)": "Attrition Rate (%)", "Job Role": "Job Role"},
                )
                fig.update_traces(
                    texttemplate="%{x:.1f}%", 
                    textposition="outside",
                    marker=dict(line=dict(width=0.5, color="rgba(26,90,255,0.3)"))
                )
                fig.update_coloraxes(showscale=False)
                fig.update_layout(
                    yaxis_title="", 
                    xaxis_title="Attrition Rate (%)",
                    height=350
                )
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig), width='stretch')
                
                top_role = role_data.iloc[-1]
                pp = top_role['Attrition Rate (%)'] - overall_rate
                _insight(
                    f"<b>{top_role['Job Role']}</b> leads at <b>{top_role['Attrition Rate (%)']:.1f}%</b> — "
                    f"{pp:+.1f}pp vs {overall_rate:.1f}% average. The spread is narrow (~2pp) — "
                    f"this is <b>company-wide</b>, not role-specific."
                )
                _cta(
                    "<b>🎯 Action:</b> Don't target one department. Company-wide policy response "
                    "(remote expansion, promotion pathways, overtime audit) will move the needle more."
                )
        
        with c2:
            stayed = int((dff["attrition"] == 0).sum())
            left = int((dff["attrition"] == 1).sum())
            total = stayed + left
            
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
                height=350,
                annotations=[dict(
                    text=f"<b>{_safe_pct(left, total):.1f}%</b><br>Left",
                    x=0.5, y=0.5, font_size=14, font_color=KB, showarrow=False,
                )],
            )
            st.plotly_chart(_theme(fig), width='stretch')
            _insight(f"<b>{left:,}</b> left · <b>{stayed:,}</b> retained · Retention: <b>{_safe_pct(stayed, total):.1f}%</b>")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q2: OVERTIME
    # ────────────────────────────────────────────────────────────────────────
    with tab2:
        _qbadge("Q2 · Overtime Burden")
        _section("Are Employees Who Work Overtime More Likely to Leave?")
        
        ot = (
            dff.groupby("overtime", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "overtime": "Overtime"})
        )
        
        c1, c2 = st.columns([2, 3])
        with c1:
            fig = px.bar(
                ot, 
                x="Overtime", 
                y="Attrition Rate (%)",
                title="Overtime vs Attrition", 
                color="Overtime",
                color_discrete_map={"Yes": KB, "No": KB_LIGHT},
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%", 
                textposition="outside",
                marker=dict(line=dict(width=1, color="white"))
            )
            fig.update_layout(
                xaxis_title="Works Overtime", 
                yaxis_title="Attrition Rate (%)", 
                showlegend=False,
                height=350
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
        
        with c2:
            ot_yes = _safe_first(ot[ot["Overtime"]=="Yes"]["Attrition Rate (%)"])
            ot_no = _safe_first(ot[ot["Overtime"]=="No"]["Attrition Rate (%)"])
            gap = ot_yes - ot_no
            st.markdown("<br>", unsafe_allow_html=True)
            _insight(
                f"Overtime workers: <b>{ot_yes:.1f}%</b> vs No overtime: <b>{ot_no:.1f}%</b> — "
                f"<b>{gap:.1f}pp gap</b> (~{int(74500*gap/100):,} additional departures)"
            )
            _cta("<b>🎯 Action:</b> Overtime audit by department. Target 20% reduction in 2 quarters.")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q3: REMOTE WORK
    # ────────────────────────────────────────────────────────────────────────
    with tab3:
        _qbadge("Q3 · Remote Work Policy")
        _section("Does Remote Work Keep People?")
        
        remote = (
            dff.groupby("remote_work", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "remote_work": "Location"})
        )
        remote["Location"] = remote["Location"].map({"Yes": "Remote", "No": "On-site"})
        
        c1, c2 = st.columns([2, 3])
        with c1:
            fig = px.bar(
                remote, 
                x="Location", 
                y="Attrition Rate (%)",
                title="Remote vs On-site", 
                color="Location",
                color_discrete_map={"Remote": KB, "On-site": KB_LIGHT},
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%", 
                textposition="outside",
                marker=dict(line=dict(width=1, color="white"))
            )
            fig.update_layout(
                xaxis_title="", 
                yaxis_title="Attrition Rate (%)", 
                showlegend=False,
                height=350
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
        
        with c2:
            r_remote = _safe_first(remote[remote["Location"]=="Remote"]["Attrition Rate (%)"])
            r_onsite = _safe_first(remote[remote["Location"]=="On-site"]["Attrition Rate (%)"])
            gap = r_onsite - r_remote
            st.markdown("<br>", unsafe_allow_html=True)
            _insight(
                f"Remote: <b>{r_remote:.1f}%</b> vs On-site: <b>{r_onsite:.1f}%</b> — "
                f"<b>{gap:.1f}pp gap</b> (2nd largest effect). Selection bias possible."
            )
            _cta("<b>🎯 Action:</b> 90-day remote pilot for high-attrition on-site roles.")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q4: PAY FAIRNESS
    # ────────────────────────────────────────────────────────────────────────
    with tab4:
        _qbadge("Q4 · Pay Fairness Within Job Levels")
        _section("Does Higher Pay Within a Level Reduce Attrition?")
        
        jl = (
            dff.groupby("job_level", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "job_level": "Job Level"})
        )
        
        c1, c2 = st.columns(2)
        
        with c1:
            fig = px.bar(
                jl, 
                x="Job Level", 
                y="Attrition Rate (%)",
                title="Attrition by Job Level",
                color="Attrition Rate (%)", 
                color_continuous_scale=BLUE_SEQ,
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%", 
                textposition="outside",
                marker=dict(line=dict(width=0.5, color="rgba(26,90,255,0.3)"))
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(xaxis_title="", yaxis_title="Attrition Rate (%)", height=350)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
            
            entry = _safe_first(jl[jl["Job Level"]=="Entry"]["Attrition Rate (%)"])
            senior = _safe_first(jl[jl["Job Level"]=="Senior"]["Attrition Rate (%)"])
            _insight(
                f"Entry: <b>{entry:.1f}%</b>, Senior: <b>{senior:.1f}%</b> — "
                f"<b>{entry-senior:.0f}pp gap</b>. <b>Job Level is the strongest driver (43pp effect).</b>"
            )
        
        with c2:
            pay_data = q.get("pay_by_level_quartile", pd.DataFrame())
            if not pay_data.empty:
                fig = px.bar(
                    pay_data, 
                    x="income_quartile", 
                    y="Attrition Rate (%)",
                    color="job_level", 
                    barmode="group",
                    title="Pay Quartile Within Level",
                    color_discrete_sequence=[KB_LIGHT, "#7FA8FF", KB],
                )
                fig.update_layout(xaxis_title="Pay Quartile", legend_title="Level", height=350)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig), width='stretch')
        
        _insight("Within-level pay increases only reduce attrition ~2pp. <b>The level itself matters most.</b>")
        _cta("<b>🎯 Action:</b> Invest in promotion pathways to Mid-level, not salary increases.")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q5: RETENTION TIMELINE
    # ────────────────────────────────────────────────────────────────────────
    with tab5:
        _qbadge("Q5 · Retention Timeline")
        _section("When Are Employees Most Likely to Leave?")
        
        tenure_data = q.get("attrition_by_tenure", pd.DataFrame())
        if not tenure_data.empty:
            fig = px.bar(
                tenure_data, 
                x="tenure_band", 
                y="Attrition Rate (%)",
                title="Attrition by Tenure",
                color="Attrition Rate (%)", 
                color_continuous_scale=BLUE_SEQ,
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%", 
                textposition="outside",
                marker=dict(line=dict(width=0.5, color="rgba(26,90,255,0.3)"))
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(xaxis_title="Years at Company", yaxis_title="Attrition Rate (%)", height=350)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
            
            peak = tenure_data.loc[tenure_data["Attrition Rate (%)"].idxmax()]
            low = tenure_data.loc[tenure_data["Attrition Rate (%)"].idxmin()]
            _insight(
                f"Peak at <b>{peak['tenure_band']}</b> (<b>{peak['Attrition Rate (%)']:.1f}%</b>), "
                f"drops to <b>{low['Attrition Rate (%)']:.1f}%</b> at 20+ years. No honeymoon cliff."
            )
            _cta("<b>🎯 Action:</b> Target 0–5 year employees with enhanced onboarding & mentoring.")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q6: ENGAGEMENT WARNING SIGNS
    # ────────────────────────────────────────────────────────────────────────
    with tab6:
        _qbadge("Q6 · Engagement Warning Signs")
        _section("Which WLB + Satisfaction Combo Is the Danger Zone?")
        
        cross_data = q.get("wlb_x_satisfaction", pd.DataFrame())
        if not cross_data.empty:
            pivot = cross_data.pivot(
                index="Work-Life Balance", 
                columns="Job Satisfaction",
                values="Attrition Rate (%)",
            )
            wlb_order = ["Poor", "Fair", "Good", "Excellent"]
            sat_order = ["Low", "Medium", "High", "Very High"]
            pivot = pivot.reindex(
                index=[x for x in wlb_order if x in pivot.index],
                columns=[x for x in sat_order if x in pivot.columns]
            )
            
            fig = go.Figure(go.Heatmap(
                z=pivot.values, 
                x=pivot.columns.tolist(), 
                y=pivot.index.tolist(),
                colorscale=[[0, KB_LIGHT], [0.5, KB], [1, KB_DARK]],
                zmin=25, 
                zmax=75, 
                text=pivot.values, 
                texttemplate="%{text:.1f}%",
                colorbar=dict(title="Attrition %"),
            ))
            fig.update_layout(
                title="WLB × Satisfaction",
                xaxis_title="Job Satisfaction",
                yaxis_title="Work-Life Balance",
                height=400,
            )
            st.plotly_chart(_theme(fig), width='stretch')
            
            _insight(
                "Danger zone: <b>Poor WLB + Low Satisfaction = 67%</b> attrition. "
                "Even <b>Very High satisfaction</b> doesn't protect Poor WLB (64.9%). "
                "<b>WLB is dominant.</b>"
            )
            _cta("<b>🎯 Action:</b> Flag Poor/Fair WLB in quarterly pulse checks.")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q7: LIFE STAGE
    # ────────────────────────────────────────────────────────────────────────
    with tab7:
        _qbadge("Q7 · Life Stage Factors")
        _section("Do Age, Marital Status, and Dependents Matter?")
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            age_data = q.get("attrition_by_age_group", pd.DataFrame())
            if not age_data.empty:
                fig = px.bar(
                    age_data, 
                    x="Age Group", 
                    y="Attrition Rate (%)",
                    title="By Age",
                    color="Attrition Rate (%)",
                    color_continuous_scale=BLUE_SEQ,
                    text="Attrition Rate (%)",
                )
                fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
                fig.update_coloraxes(showscale=False)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig), width='stretch')
        
        with c2:
            marital_data = q.get("attrition_by_marital", pd.DataFrame())
            if not marital_data.empty:
                fig = px.bar(
                    marital_data, 
                    x="Marital Status", 
                    y="Attrition Rate (%)",
                    title="By Marital Status",
                    color="Marital Status",
                    color_discrete_sequence=[KB, "#7FA8FF", KB_LIGHT],
                    text="Attrition Rate (%)",
                )
                fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
                fig.update_layout(showlegend=False)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig), width='stretch')
        
        with c3:
            dep_data = q.get("attrition_by_dependents", pd.DataFrame())
            if not dep_data.empty:
                fig = px.line(
                    dep_data, 
                    x="Number of Dependents", 
                    y="Attrition Rate (%)",
                    title="By Dependents",
                    markers=True, 
                    line_shape="spline",
                )
                fig.update_traces(line_color=KB, marker_color=KB, marker_size=8)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig), width='stretch')
        
        _insight("Highest-risk: young, single. With dependents = stable. <b>Family = rootedness.</b>")
        _cta("<b>🎯 Action:</b> Build community programs for young, single employees.")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q8: CAREER STAGNATION
    # ────────────────────────────────────────────────────────────────────────
    with tab8:
        _qbadge("Q8 · Career Stagnation")
        _section("Does Feeling Stuck Drive Attrition?")
        
        c1, c2 = st.columns(2)
        
        with c1:
            promo_data = q.get("attrition_by_promotions", pd.DataFrame())
            if not promo_data.empty:
                fig = px.line(
                    promo_data, 
                    x="Number of Promotions", 
                    y="Attrition Rate (%)",
                    title="Attrition vs Promotions", 
                    markers=True, 
                    line_shape="spline",
                )
                fig.update_traces(line_color=KB, marker_color=KB, marker_size=9)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig), width='stretch')
                
                p0 = _safe_first(promo_data[promo_data["Number of Promotions"]==0]["Attrition Rate (%)"])
                p4 = _safe_first(promo_data[promo_data["Number of Promotions"]==4]["Attrition Rate (%)"])
                _insight(
                    f"0 promos: <b>{p0:.1f}%</b> → 4 promos: <b>{p4:.1f}%</b>. "
                    f"<b>Non-linear jump at 3 promotions.</b>"
                )
        
        with c2:
            for col_key, label in [
                ("attrition_by_leadership_opportunities", "Leadership"),
                ("attrition_by_innovation_opportunities", "Innovation"),
            ]:
                opp_data = q.get(col_key, pd.DataFrame())
                if not opp_data.empty and len(opp_data.columns) >= 2:
                    x_col = opp_data.columns[0]
                    fig = px.bar(
                        opp_data, 
                        x=x_col, 
                        y="Attrition Rate (%)",
                        title=f"{label} Opportunities",
                        color=x_col, 
                        color_discrete_map={"Yes": KB, "No": KB_LIGHT},
                        text="Attrition Rate (%)",
                    )
                    fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
                    fig.update_layout(xaxis_title="", showlegend=False, height=350)
                    _add_avg_line(fig, overall_rate)
                    st.plotly_chart(_theme(fig), width='stretch')
        
        stuck_n = q.get("stuck_n", 0)
        stuck_rate = q.get("stuck_rate", 0.0)
        _risk(f"<b>{stuck_n:,} employees</b> fully stuck (0 promos, no leadership, no innovation). <b>{stuck_rate:.1f}%</b> attrition.")
        _cta(f"<b>🎯 Action:</b> 90-day development plans. Move 30% out within 2 quarters.")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q9: HIGHEST-RISK PROFILE
    # ────────────────────────────────────────────────────────────────────────
    with tab9:
        _qbadge("Q9 · Highest-Risk Profile")
        _section("Who Is Most Likely to Leave?")
        
        risk_n = q.get("risk_profile_n", 0)
        risk_rate = q.get("risk_profile_rate", 0.0)
        risk_lift = risk_rate - overall_rate
        
        _risk(
            f"<b>Profile:</b> Poor WLB + Overtime + 0 Promos + No Leadership<br>"
            f"<b>Attrition: {risk_rate:.1f}%</b> ({risk_lift:+.1f}pp) · <b>{risk_n:,} employees</b>"
        )
        
        c1, c2 = st.columns(2)
        
        with c1:
            factors = pd.DataFrame({
                "Factor": ["Poor WLB", "Overtime", "Zero Promos", "No Leadership"],
                "Attrition Rate (%)": [60.2, 51.5, 49.3, 47.6],
            })
            fig = px.bar(
                factors.sort_values("Attrition Rate (%)"),
                x="Attrition Rate (%)", 
                y="Factor", 
                orientation="h",
                title="Risk Factors",
                color="Attrition Rate (%)", 
                color_continuous_scale=BLUE_SEQ,
                text="Attrition Rate (%)",
            )
            fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
            fig.update_coloraxes(showscale=False)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
        
        with c2:
            comparison = pd.DataFrame({
                "Group": ["Company Avg", "Risk Profile"],
                "Attrition Rate (%)": [overall_rate, risk_rate],
            })
            fig = px.bar(
                comparison, 
                x="Group", 
                y="Attrition Rate (%)",
                title="Risk vs Average",
                color="Group", 
                color_discrete_map={"Company Avg": KB_LIGHT, "Risk Profile": KB},
                text="Attrition Rate (%)",
            )
            fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
            fig.update_layout(showlegend=False)
            st.plotly_chart(_theme(fig), width='stretch')
        
        _cta(f"<b>🎯 Action:</b> HR touchpoint for {risk_n:,} within 30 days. Eliminate 2+ factors.")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q10: WHAT MOVES THE NEEDLE
    # ────────────────────────────────────────────────────────────────────────
    with tab10:
        _qbadge("Q10 · What Moves the Needle")
        _section("If HR Could Fix One Thing Next Quarter...")
        
        drivers = q.get("driver_ranking", pd.DataFrame())
        if not drivers.empty:
            fig = px.bar(
                drivers, 
                x="Effect (pp)", 
                y="Driver", 
                orientation="h",
                title="Top Drivers by Effect Size",
                color="Effect (pp)", 
                color_continuous_scale=BLUE_SEQ,
                text="Effect (pp)",
            )
            fig.update_traces(texttemplate="%{x:.1f}pp", textposition="outside")
            fig.update_coloraxes(showscale=False)
            fig.update_layout(xaxis_title="Attrition Difference (pp)", yaxis_title="", height=350)
            st.plotly_chart(_theme(fig), width='stretch')
        
        st.markdown("### 🏆 Top 3 Recommendations")
        r1, r2, r3 = st.columns(3)
        
        with r1:
            st.markdown(
                "<div class='risk-card'><b>#1 · Remote Work</b><br>"
                "Effect: <b>28.1pp</b><br>"
                "2-week policy change. 19% remote now."
                "</div>",
                unsafe_allow_html=True,
            )
        
        with r2:
            st.markdown(
                "<div class='rec-box'><b>#2 · Promotions</b><br>"
                "Effect: <b>26.0pp</b><br>"
                "Non-linear jump at 3rd."
                "</div>",
                unsafe_allow_html=True,
            )
        
        with r3:
            st.markdown(
                "<div class='rec-box'><b>#3 · Work-Life Balance</b><br>"
                "Effect: <b>24.5pp</b><br>"
                "Overrides satisfaction."
                "</div>",
                unsafe_allow_html=True,
            )
        
        st.markdown("---")
        st.markdown("### 📋 90-Day Action Plan")
        st.info(
            "**Week 1–2:** Launch remote eligibility review\n\n"
            f"**Week 1–3:** Assign HR partners to {risk_n:,} risk-profile employees\n\n"
            "**Week 2–4:** Overtime audit by department\n\n"
            "**Month 2:** Accelerate promotion reviews (0-promotion cohort)\n\n"
            "**Month 2:** WLB pulse survey\n\n"
            "**Month 3:** Launch peer-community programme"
        )

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2: WORKLOAD (Q2, Q3)
# ═════════════════════════════════════════════════════════════════════════════
def page_workload():
    st.markdown("## ⏰ Workload & Flexibility")
    _kpi_row()
    st.markdown("---")
    
    st.info("See Q2 & Q3 in the Overview tabs above for detailed analysis.")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3: PAY (Q4)
# ═════════════════════════════════════════════════════════════════════════════
def page_pay():
    st.markdown("## 💰 Pay & Job Level")
    _kpi_row()
    st.markdown("---")
    
    st.info("See Q4 in the Overview tabs above for detailed analysis.")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 4: ENGAGEMENT (Q5, Q6, Q7)
# ═════════════════════════════════════════════════════════════════════════════
def page_engagement():
    st.markdown("## 🧠 Engagement & Life Stage")
    _kpi_row()
    st.markdown("---")
    
    st.info("See Q5, Q6 & Q7 in the Overview tabs above for detailed analysis.")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 5: CAREER (Q8)
# ═════════════════════════════════════════════════════════════════════════════
def page_career():
    st.markdown("## 🚀 Career Growth")
    _kpi_row()
    st.markdown("---")
    
    st.info("See Q8 in the Overview tabs above for detailed analysis.")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 6: RISK & STRATEGY (Q9, Q10)
# ═════════════════════════════════════════════════════════════════════════════
def page_risk():
    st.markdown("## 🎯 Risk & Strategy")
    _kpi_row()
    st.markdown("---")
    
    st.info("See Q9 & Q10 in the Overview tabs above for detailed analysis.")

# ═════════════════════════════════════════════════════════════════════════════
# NAVIGATION
# ═════════════════════════════════════════════════════════════════════════════
pg = st.navigation({
    "📊 Dashboard": [
        st.Page(page_overview, title="Overview", icon="🏠", default=True),
    ],
    "🔍 Analysis": [
        st.Page(page_workload, title="Workload & Flexibility", icon="⏰"),
        st.Page(page_pay, title="Pay & Job Level", icon="💰"),
        st.Page(page_engagement, title="Engagement & Life Stage", icon="🧠"),
        st.Page(page_career, title="Career Growth", icon="🚀"),
        st.Page(page_risk, title="Risk & Strategy", icon="🎯"),
    ],
})

pg.run()
