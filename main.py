"""
main.py  —  HR Attrition Dashboard (COMPLETE - ALL 10 QUESTIONS)
Kayfa AI & Data Analytics Internship · Week 1

FEATURES:
  ✓ All 10 questions fully answered (Q1-Q10)
  ✓ Logo from GitHub with fallback
  ✓ width='stretch' parameter (Streamlit latest)
  ✓ Professional CSS/HTML
  ✓ Dark/light theme support
  ✓ All insights + CTAs
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
BLUE_SEQ  = [KB_LIGHT, "#BDD0FF", "#7FA8FF", "#4C84FF", KB, KB_DARK, "#0D31A3", "#081F7A"]
ATTRITION_MAP = {"Stayed": KB_LIGHT, "Left": KB}

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

section[data-testid="stSidebar"] {
    background: #1A5AFF !important;
    width: 300px !important;
}

section[data-testid="stSidebar"] > div:first-child {
    width: 300px !important;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.25) !important;
    margin: 0.8rem 0 !important;
}

.sidebar-logo-fixed {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #1A5AFF;
    padding: 1.2rem 0.8rem;
    border-bottom: 2px solid rgba(255,255,255,0.2);
    text-align: center;
}

.sidebar-logo-fixed img {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
}

section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background: #1245CC !important;
    color: white !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.15) !important;
    border-color: rgba(255,255,255,0.3) !important;
    color: white !important;
}

section[data-testid="stSidebar"] .stRadio > label {
    color: white !important;
}

section[data-testid="stSidebar"] .stSlider > label {
    color: white !important;
}

section[data-testid="stSidebar"] .stSlider > div {
    color: white !important;
}

.main {
    max-width: 100% !important;
}

[data-testid="stMainBlockContainer"] {
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

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

.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    border-bottom: 2px solid rgba(26,90,255,0.2);
    padding-bottom: 0.5rem;
    margin: 1.4rem 0 0.9rem 0;
}

.hero-title {
    font-size: 1.9rem;
    font-weight: 800;
    line-height: 1.2;
    margin: 0;
}

.hero-sub {
    font-size: 0.88rem;
    opacity: 0.7;
    margin-top: 0.3rem;
}

.kpi-card {
    background: rgba(26,90,255,0.06);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 1rem 1.2rem;
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

.metric-card {
    background: rgba(26,90,255,0.03);
    border: 1px solid rgba(26,90,255,0.15);
    border-radius: 6px;
    padding: 1rem;
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

.rec-box {
    background: rgba(26,90,255,0.05);
    border: 1px solid rgba(26,90,255,0.2);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}

footer {
    visibility: hidden;
}

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
# LOGO LOADER (GitHub + Local Fallback)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_logo():
    """Load logo from GitHub or fallback to local file."""
    try:
        # Try to load from local first
        logo = Image.open("company_logo2.png")
        return logo
    except FileNotFoundError:
        try:
            # Fallback: Try to load from GitHub (replace with your actual GitHub URL)
            # Example: https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/company_logo2.png
            url = "https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/company_logo2.png"
            response = requests.get(url)
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
    fig.add_hline(y=y_val, line_dash="dash", line_color=AMBER, line_width=2)
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines",
        line=dict(dash="dash", color=AMBER, width=2),
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
    st.markdown("<div class='sidebar-logo-fixed'>", unsafe_allow_html=True)
    if logo is not None:
        st.image(logo, width=150)
    else:
        st.markdown(
            "<h3 style='margin:0;color:white;font-size:2rem;'>كيف</h3>"
            "<p style='margin:0.3rem 0 0 0;font-size:0.8rem;opacity:0.9;'>Kayfa AI</p>",
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
            f"<div style='font-size:0.75rem;opacity:0.6;'>filtered group</div></div>",
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
# PAGE 1: OVERVIEW (Q1 - The Headline)
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
                "<div style='text-align:center;font-size:2.2rem;font-weight:900;'>"
                "<span style='color:#1A5AFF;'>كيف</span></div>",
                unsafe_allow_html=True,
            )
    
    st.markdown("---")
    _kpi_row()
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q1: THE HEADLINE
    # ════════════════════════════════════════════════════════════════════════
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
                role_data, x="Attrition Rate (%)", y="Job Role", orientation="h",
                title="Attrition Rate by Job Role",
                color="Attrition Rate (%)", color_continuous_scale=BLUE_SEQ,
                text="Attrition Rate (%)",
            )
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis_title="", xaxis_title="Attrition Rate (%)")
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
            
            top_role = role_data.iloc[-1]
            pp = top_role['Attrition Rate (%)'] - overall_rate
            _insight(
                f"<b>{top_role['Job Role']}</b> leads at <b>{top_role['Attrition Rate (%)']:.1f}%</b> — "
                f"{pp:+.1f}pp vs {overall_rate:.1f}% average. The <b>spread is narrow (~2pp)</b> — "
                f"this is <b>company-wide</b>, not role-specific."
            )
            _cta(
                "<b>🎯 Action:</b> Don't target one department. "
                "Company-wide policy response (remote expansion, promotion pathways, overtime audit) "
                "will move the needle more than role-by-role fixes."
            )
    
    with c2:
        stayed = int((dff["attrition"] == 0).sum())
        left = int((dff["attrition"] == 1).sum())
        total = stayed + left
        
        fig = go.Figure(go.Pie(
            labels=["Stayed", "Left"], values=[stayed, left], hole=0.62,
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
        st.plotly_chart(_theme(fig), width='stretch')
        _insight(
            f"<b>{left:,}</b> employees left · <b>{stayed:,}</b> retained · "
            f"Retention rate: <b>{_safe_pct(stayed, total):.1f}%</b>"
        )
    
    st.markdown("---")
    _section("Executive Summary")
    
    income_left = dff[dff["attrition"]==1]["monthly_income"].mean()
    income_stayed = dff[dff["attrition"]==0]["monthly_income"].mean()
    income_gap = _safe_pct(income_left - income_stayed, income_stayed)
    
    avg_age_left = dff[dff["attrition"]==1]["age"].mean()
    avg_age_stayed = dff[dff["attrition"]==0]["age"].mean()
    
    s1, s2 = st.columns(2)
    with s1:
        st.markdown("##### 🔍 Key Findings")
        severity = "🔴 **HIGH RISK**" if kpis["rate"] > overall_rate + 5 else "🟢 **BELOW AVERAGE**" if kpis["rate"] < overall_rate - 5 else "🟡 **NEAR AVERAGE**"
        st.error(f"{severity} — {kpis['rate']:.1f}% vs {overall_rate:.1f}% company average")
        st.warning(f"💰 Salary gap: **{abs(income_gap):.1f}%** — money is **NOT** the primary driver")
        st.info(f"👥 Leavers avg **{avg_age_left:.0f} yrs** vs **{avg_age_stayed:.0f} yrs** stayers — younger employees at higher risk")
    
    with s2:
        st.markdown("##### 💡 Top Recommendations (by Impact)")
        st.success("🏠 **#1: Expand remote work** — 28pp attrition gap")
        st.success("🚀 **#2: Build promotion pathways** — 26pp effect size")
        st.success("⚖️ **#3: Audit overtime exposure** — 6pp direct effect")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2: WORKLOAD & FLEXIBILITY (Q2, Q3)
# ═════════════════════════════════════════════════════════════════════════════
def page_workload():
    st.markdown("## ⏰ Workload & Flexibility")
    _kpi_row()
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q2: OVERTIME
    # ════════════════════════════════════════════════════════════════════════
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
            ot, x="Overtime", y="Attrition Rate (%)",
            title="Overtime vs Attrition Rate",
            color="Overtime",
            color_discrete_map={"Yes": KB, "No": KB_LIGHT},
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(xaxis_title="Works Overtime", yaxis_title="Attrition Rate (%)", showlegend=False)
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), width='stretch')
    
    with c2:
        ot_yes = _safe_first(ot[ot["Overtime"]=="Yes"]["Attrition Rate (%)"])
        ot_no = _safe_first(ot[ot["Overtime"]=="No"]["Attrition Rate (%)"])
        gap = ot_yes - ot_no
        st.markdown("<br>", unsafe_allow_html=True)
        _insight(
            f"Employees working overtime leave at <b>{ot_yes:.1f}%</b> vs <b>{ot_no:.1f}%</b> for those who don't — "
            f"a <b>{gap:.1f}pp gap</b>. At 74,498 employees, every pp = ~745 people. "
            f"This {gap:.1f}pp gap means ~{int(74500*gap/100):,} additional departures directly attributable to overtime burnout."
        )
        _cta(
            "<b>🎯 HR Action:</b> Conduct department-level overtime audit. "
            "Identify teams with chronic >10% overtime exposure and redistribute workload before attrition compounds. "
            "<b>Target:</b> Reduce overtime headcount by 20% within 2 quarters."
        )
    
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q3: REMOTE WORK
    # ════════════════════════════════════════════════════════════════════════
    _qbadge("Q3 · Remote Work Policy")
    _section("Does Offering Remote Work Keep People?")
    
    remote = (
        dff.groupby("remote_work", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)", "remote_work": "Work Location"})
    )
    remote["Work Location"] = remote["Work Location"].map({"Yes": "Remote", "No": "On-site"})
    
    pct_remote = _safe_pct((dff["remote_work"]=="Yes").sum(), len(dff))
    
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
        fig.update_layout(xaxis_title="", yaxis_title="Attrition Rate (%)", showlegend=False)
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), width='stretch')
    
    with c2:
        r_remote = _safe_first(remote[remote["Work Location"]=="Remote"]["Attrition Rate (%)"])
        r_onsite = _safe_first(remote[remote["Work Location"]=="On-site"]["Attrition Rate (%)"])
        gap = r_onsite - r_remote
        st.markdown("<br>", unsafe_allow_html=True)
        _insight(
            f"Remote workers leave at <b>{r_remote:.1f}%</b> — <b>{gap:.1f}pp lower</b> than on-site employees at <b>{r_onsite:.1f}%</b>. "
            f"This is the <b>second largest effect size</b> in the entire dataset. "
            f"<b>BUT:</b> Only <b>{pct_remote:.1f}%</b> of workforce is currently remote. "
            f"The effect is real, but reflects selection bias: remote-eligible roles may attract more committed employees."
        )
        _cta(
            "<b>🎯 HR Action:</b> Run 90-day remote work pilot for on-site roles with attrition >50%. "
            f"Even shifting 10% of on-site headcount to remote could prevent ~{int(dff.shape[0]*0.10*gap/100):,} departures. "
            "Track attrition before/after to confirm causation vs selection bias."
        )

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3: PAY & JOB LEVEL (Q4)
# ═════════════════════════════════════════════════════════════════════════════
def page_pay():
    st.markdown("## 💰 Pay & Job Level")
    _kpi_row()
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q4: PAY FAIRNESS
    # ════════════════════════════════════════════════════════════════════════
    _qbadge("Q4 · Pay Fairness Within Job Levels")
    _section("Within the Same Job Level, Do Lower-Paid Employees Leave More Often?")
    
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
        st.plotly_chart(_theme(fig), width='stretch')
        
        entry = _safe_first(jl[jl["Job Level"]=="Entry"]["Attrition Rate (%)"])
        senior = _safe_first(jl[jl["Job Level"]=="Senior"]["Attrition Rate (%)"])
        _insight(
            f"Entry-level employees leave at <b>{entry:.1f}%</b>, Senior employees at <b>{senior:.1f}%</b> — "
            f"a <b>{entry-senior:.0f}pp gap</b>. <b>Job Level is the single strongest driver in the dataset (43pp effect).</b>"
        )
    
    with c2:
        pay_data = q.get("pay_by_level_quartile", pd.DataFrame())
        if not pay_data.empty:
            fig = px.bar(
                pay_data, x="income_quartile", y="Attrition Rate (%)",
                color="job_level", barmode="group",
                title="Attrition by Pay Quartile Within Each Job Level",
                color_discrete_sequence=[KB_LIGHT, "#7FA8FF", KB],
                labels={"income_quartile": "Pay Quartile", "job_level": "Job Level"},
            )
            fig.update_layout(
                xaxis_title="Pay Quartile (within Job Level)",
                yaxis_title="Attrition Rate (%)",
                legend_title="Job Level",
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
    
    _insight(
        "Within the same job level, moving from bottom pay quartile to top reduces attrition by only <b>~2pp</b> "
        "(e.g., Entry: 64.5% → 62.5%). <b>Pay raises within a band are largely ineffective.</b> "
        "The <b>level itself</b> is what matters — Entry employees leave at 63% regardless of what you pay them."
    )
    _cta(
        "<b>🎯 HR Action — Reframe the Pay Debate:</b> "
        "Don't give Entry-level staff a 10% raise. Invest that budget in structured <b>promotion pathways to Mid-level</b>. "
        "Every employee promoted from Entry to Mid eliminates an ~18pp attrition risk. "
        "<b>Set target:</b> Reduce time-to-first-promotion by 6 months."
    )
    
    st.markdown("---")
    _section("Income Distribution — Stayed vs. Left")
    
    fig = px.box(
        dff, x=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        y="monthly_income",
        title="Monthly Income Distribution by Attrition Status",
        color=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        color_discrete_map=ATTRITION_MAP,
        points=False,
        labels={"x": "Status", "monthly_income": "Monthly Income ($)"},
    )
    fig.update_layout(xaxis_title="", yaxis_title="Monthly Income ($)", showlegend=False)
    st.plotly_chart(_theme(fig), width='stretch')
    
    _insight(
        "The income distributions for leavers and stayers are nearly identical (median gap < 1%). "
        "<b>This confirms: Compensation is NOT the primary driver.</b> "
        "Leadership must resist the instinct to solve an attrition crisis with blanket raises."
    )

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 4: ENGAGEMENT & LIFE STAGE (Q5, Q6, Q7)
# ═════════════════════════════════════════════════════════════════════════════
def page_engagement():
    st.markdown("## 🧠 Engagement & Life Stage")
    _kpi_row()
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q5: RETENTION TIMELINE
    # ════════════════════════════════════════════════════════════════════════
    _qbadge("Q5 · The Retention Timeline")
    _section("At What Stage of Employment Is Attrition Highest?")
    
    tenure_data = q.get("attrition_by_tenure", pd.DataFrame())
    if not tenure_data.empty:
        fig = px.bar(
            tenure_data, x="tenure_band", y="Attrition Rate (%)",
            title="Attrition Rate by Company Tenure",
            color="Attrition Rate (%)",
            color_continuous_scale=BLUE_SEQ,
            text="Attrition Rate (%)",
            labels={"tenure_band": "Tenure Band"},
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Years at Company", yaxis_title="Attrition Rate (%)")
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), width='stretch')
        
        peak_band = tenure_data.loc[tenure_data["Attrition Rate (%)"].idxmax()]
        low_band = tenure_data.loc[tenure_data["Attrition Rate (%)"].idxmin()]
        
        _insight(
            f"Attrition peaks at the <b>{peak_band['tenure_band']}</b> stage (<b>{peak_band['Attrition Rate (%)']:.1f}%</b>) "
            f"and remains elevated through the first 10 years. Long-tenure employees (20+ yrs) show the lowest risk at "
            f"<b>{low_band['Attrition Rate (%)']:.1f}%</b>. <b>The data shows no 'honeymoon cliff'</b> — attrition is high from day one."
        )
        _cta(
            "<b>🎯 Action — Target the First 5 Years:</b> "
            "Redesign onboarding programme for 0–2yr window. Introduce structured career check-in at 18 months — "
            "the point where mid-career drift becomes visible. Long-tenure employees are most stable; protect them "
            "through recognition and leadership pathways."
        )
    
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q6: ENGAGEMENT WARNING SIGNS
    # ════════════════════════════════════════════════════════════════════════
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
            hovertemplate="WLB: %{y}<br>Satisfaction: %{x}<br>Attrition: %{z:.1f}%<extra></extra>",
            colorbar=dict(title="Attrition %"),
        ))
        fig.update_layout(
            title="Attrition Rate: Work-Life Balance × Job Satisfaction",
            xaxis_title="Job Satisfaction",
            yaxis_title="Work-Life Balance",
            height=400,
        )
        st.plotly_chart(_theme(fig), width='stretch')
        
        _insight(
            "The danger zone is <b>top-left</b> of heatmap: <b>Poor WLB + Low Satisfaction = 67.0%</b> attrition — "
            "nearly 1.5× the company average. Crucially, even <b>Very High satisfaction doesn't protect</b> "
            "employees with Poor WLB (64.9%). <b>WLB is the dominant variable</b> — satisfaction is secondary."
        )
        _cta(
            "<b>🎯 Manager Early-Warning Signals to Watch:</b> "
            "An employee who says they love their work but reports poor balance is at just as high risk as one who is dissatisfied. "
            "Build a quarterly pulse check flagging any employee with Poor/Fair WLB — regardless of satisfaction score."
        )
    
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q7: LIFE STAGE
    # ════════════════════════════════════════════════════════════════════════
    _qbadge("Q7 · Life Stage Factors")
    _section("Do Age, Marital Status, and Dependents Change Who Leaves?")
    
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
            st.plotly_chart(_theme(fig), width='stretch')
    
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
            st.plotly_chart(_theme(fig), width='stretch')
    
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
            st.plotly_chart(_theme(fig), width='stretch')
    
    _insight(
        "The highest-risk life-stage group is <b>young, single employees (18–25)</b> — attrition of <b>53.1%</b> "
        "combined with <b>66.8%</b> for single marital status. Employees with 4+ dependents leave significantly less "
        "(35–37%) — <b>family responsibility correlates with stability.</b> "
        "This is not about age — it's about rootedness."
    )
    _cta(
        "<b>🎯 Action — Target Single, Young Employees Specifically:</b> "
        "Build community and belonging programmes (mentorship cohorts, team social budgets, structured peer networks) "
        "that create organisational roots. These are low-cost and directly address the psychological driver "
        "behind this life-stage risk."
    )

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 5: CAREER GROWTH (Q8)
# ═════════════════════════════════════════════════════════════════════════════
def page_career():
    st.markdown("## 🚀 Career Growth")
    _kpi_row()
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q8: CAREER STAGNATION
    # ════════════════════════════════════════════════════════════════════════
    _qbadge("Q8 · Career Stagnation")
    _section("Does Feeling Stuck Drive Attrition?")
    
    c1, c2 = st.columns(2)
    
    with c1:
        promo_data = q.get("attrition_by_promotions", pd.DataFrame())
        if not promo_data.empty:
            fig = px.line(
                promo_data, x="Number of Promotions", y="Attrition Rate (%)",
                title="Attrition Rate vs Number of Promotions",
                markers=True, line_shape="spline",
            )
            fig.update_traces(line_color=KB, marker_color=KB, marker_size=9)
            _add_avg_line(fig, overall_rate)
            fig.update_layout(
                xaxis_title="Number of Promotions Received",
                yaxis_title="Attrition Rate (%)",
            )
            st.plotly_chart(_theme(fig), width='stretch')
            
            p0 = _safe_first(promo_data[promo_data["Number of Promotions"]==0]["Attrition Rate (%)"])
            p4 = _safe_first(promo_data[promo_data["Number of Promotions"]==4]["Attrition Rate (%)"])
            _insight(
                f"<b>0 promotions → {p0:.1f}% attrition.</b> <b>4 promotions → {p4:.1f}% attrition.</b> "
                f"The <b>attrition rate is cut in half</b> by promotion alone. Crucially, the drop is non-linear: "
                f"0–2 promotions show ~49% (near baseline), but reaching 3 promotions triggers a sharp drop to ~25%. "
                f"<b>There is a promotion threshold effect.</b>"
            )
    
    with c2:
        for col_key, label, color_map in [
            ("attrition_by_leadership_opportunities", "Leadership Opportunities", {"Yes": KB, "No": KB_LIGHT}),
            ("attrition_by_innovation_opportunities", "Innovation Opportunities", {"Yes": KB, "No": KB_LIGHT}),
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
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(xaxis_title=label, yaxis_title="Attrition Rate (%)", showlegend=False)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig), width='stretch')
    
    st.markdown("---")
    _section("The 'Fully Stuck' Employee Profile")
    
    stuck_n = q.get("stuck_n", 0)
    stuck_rate = q.get("stuck_rate", 0.0)
    delta_stuck = stuck_rate - overall_rate
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"<div class='metric-card'><div class='metric-value'>{stuck_n:,}</div>"
            f"<div class='metric-label'>Fully Stuck Employees</div>"
            f"<div style='font-size:0.7rem;margin-top:0.3rem;opacity:0.6;'>"
            f"0 promotions + no leadership + no innovation</div></div>",
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"<div class='metric-card'><div class='metric-value'>{stuck_rate:.1f}%</div>"
            f"<div class='metric-label'>Their Attrition Rate</div></div>",
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"<div class='metric-card'><div class='metric-value' style='color:{RED};'>{delta_stuck:+.1f}pp</div>"
            f"<div class='metric-label'>vs Company Average</div></div>",
            unsafe_allow_html=True
        )
    
    _risk(
        f"<b>{stuck_n:,} employees</b> (0 promotions, no leadership, no innovation) show <b>{stuck_rate:.1f}%</b> attrition — "
        f"{delta_stuck:+.1f}pp above the {overall_rate:.1f}% average. This is not a fringe group — "
        f"it is nearly 40% of the workforce. <b>Career stagnation is systemic.</b>"
    )
    _cta(
        "<b>🎯 Growth & Mobility Recommendation:</b> "
        "Establish a 'minimum viable growth' standard: every employee should have "
        "at least one growth dimension — a promotion track, a leadership project, or an innovation initiative — "
        f"within 18 months. Identify the {stuck_n:,} employees in this profile and assign each "
        "a 90-day development plan. <b>Target:</b> Move 30% out of the 'fully stuck' category within 2 quarters."
    )

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 6: RISK & STRATEGY (Q9, Q10)
# ═════════════════════════════════════════════════════════════════════════════
def page_risk():
    st.markdown("## 🎯 Risk & Strategy")
    _kpi_row()
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q9: HIGHEST-RISK PROFILE
    # ════════════════════════════════════════════════════════════════════════
    _qbadge("Q9 · Highest-Risk Employee Profile")
    _section("Who Is Most Likely to Leave — and How Many Are There?")
    
    risk_n = q.get("risk_profile_n", 0)
    risk_rate = q.get("risk_profile_rate", 0.0)
    risk_lift = risk_rate - overall_rate
    
    _risk(
        f"<b>Profile: Poor Work-Life Balance + Overtime + 0 Promotions + No Leadership Opportunities</b><br><br>"
        f"Attrition rate: <b>{risk_rate:.1f}%</b> &nbsp;·&nbsp; "
        f"<b>{risk_lift:+.1f}pp above</b> the {overall_rate:.1f}% company average &nbsp;·&nbsp; "
        f"<b>{risk_n:,} employees</b> match this profile today"
    )
    
    c1, c2 = st.columns(2)
    
    with c1:
        factors = pd.DataFrame({
            "Factor": ["Poor Work-Life Balance", "Works Overtime", "Zero Promotions", "No Leadership Access"],
            "Attrition Rate (%)": [60.2, 51.5, 49.3, 47.6],
        })
        fig = px.bar(
            factors.sort_values("Attrition Rate (%)"),
            x="Attrition Rate (%)", y="Factor", orientation="h",
            title="Standalone Attrition Rate of Each Risk Factor",
            color="Attrition Rate (%)",
            color_continuous_scale=BLUE_SEQ,
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_coloraxes(showscale=False)
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), width='stretch')
    
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
        st.plotly_chart(_theme(fig), width='stretch')
    
    _insight(
        f"This profile shows <b>{risk_rate:.1f}%</b> attrition — nearly <b>1.4× the company average</b>. "
        f"With <b>{risk_n:,} employees</b> matching it today, this is large enough to act on. "
        f"If even half leave this year, that is ~{int(risk_n * risk_rate/100):,} departures from this "
        f"one identifiable cohort. The 4 factors are individually manageable — together they compound into departure near-certainty."
    )
    _cta(
        f"<b>🎯 Immediate Action:</b> Export the list of {risk_n:,} employees matching this profile and assign each "
        f"an HR business partner touchpoint within 30 days. Target: eliminate at least 2 of the 4 risk factors per employee "
        f"(e.g., approve remote work + assign to a leadership project). A 20% success rate prevents ~{int(risk_n * risk_rate/100 * 0.2):,} departures."
    )
    
    st.markdown("---")
    
    # ════════════════════════════════════════════════════════════════════════
    # Q10: WHAT MOVES THE NEEDLE
    # ════════════════════════════════════════════════════════════════════════
    _qbadge("Q10 · What Moves the Needle")
    _section("If HR Could Fix One Thing Next Quarter — What Does Data Say It Should Be?")
    
    drivers = q.get("driver_ranking", pd.DataFrame())
    if not drivers.empty:
        fig = px.bar(
            drivers, x="Effect (pp)", y="Driver", orientation="h",
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
        st.plotly_chart(_theme(fig), width='stretch')
    
    st.markdown("### 🏆 Ranked Recommendations")
    r1, r2, r3 = st.columns(3)
    
    with r1:
        st.markdown(
            "<div class='risk-card'><b>#1 · Expand Remote Work</b><br><br>"
            "Effect size: <b>28.1pp</b><br>"
            "On-site: 52.8% → Remote: 24.7%<br><br>"
            "Only 19.1% of workforce is remote. Fastest policy lever available. "
            f"A 10% shift in headcount to remote = ~{int(dff.shape[0]*0.10*28.1/100):,} retained employees.</div>",
            unsafe_allow_html=True,
        )
    
    with r2:
        st.markdown(
            "<div class='rec-box'><b>#2 · Build Promotion Pathways</b><br><br>"
            "Effect size: <b>26.0pp</b><br>"
            "0 promos: 49.3% → 4 promos: 23.3%<br><br>"
            "Non-linear effect — the jump happens at 3 promotions. "
            "Accelerate time-to-third-promotion for at-risk cohorts.</div>",
            unsafe_allow_html=True,
        )
    
    with r3:
        st.markdown(
            "<div class='rec-box'><b>#3 · Fix Work-Life Balance</b><br><br>"
            "Effect size: <b>24.5pp</b><br>"
            "Poor: 60.2% → Excellent: 35.7%<br><br>"
            "WLB is the dominant engagement variable — it overrides job satisfaction. "
            "Start with overtime reduction and flexible scheduling.</div>",
            unsafe_allow_html=True,
        )
    
    _insight(
        "<b>The #1 pick is Remote Work expansion.</b> Here's why it beats career growth as the single next-quarter action: "
        "it is a <b><i>policy change</i>, not a structural one.</b> Promoting people takes 12–18 months. "
        "Approving remote work takes 2 weeks. The effect size is real (28.1pp), the mechanism is plausible, "
        "and the cost of a pilot is near-zero. "
        f"Rough impact estimate: shifting 5% of on-site workforce (~{int(dff.shape[0]*0.05):,} employees) "
        f"to remote at the same retention improvement rate would prevent ~{int(dff.shape[0]*0.05*28.1/100):,} "
        f"additional departures per annual cohort."
    )
    
    st.markdown("---")
    st.markdown("### 📅 90-Day Action Roadmap")
    
    roadmap_html = f"""
    <table style='width:100%;border-collapse:collapse;'>
    <tr style='background:rgba(26,90,255,0.1);'>
        <td style='padding:0.8rem;border:1px solid rgba(26,90,255,0.2);'><b>Priority</b></td>
        <td style='padding:0.8rem;border:1px solid rgba(26,90,255,0.2);'><b>Action</b></td>
        <td style='padding:0.8rem;border:1px solid rgba(26,90,255,0.2);'><b>Owner</b></td>
        <td style='padding:0.8rem;border:1px solid rgba(26,90,255,0.2);'><b>Timeline</b></td>
        <td style='padding:0.8rem;border:1px solid rgba(26,90,255,0.2);'><b>Expected Impact</b></td>
    </tr>
    <tr>
        <td style='padding:0.8rem;border:1px solid rgba(26,90,255,0.2);'>🔴 Critical</td>
