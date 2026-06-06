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
# PAGE 1: OVERVIEW (Q1)
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
        _insight(f"<b>{left:,}</b> left · <b>{stayed:,}</b> retained")
    
    st.markdown("---")
    _section("Executive Summary")
    
    s1, s2 = st.columns(2)
    with s1:
        st.markdown("##### 🔍 Key Findings")
        st.error(f"🔴 **HIGH RISK** — {kpis['rate']:.1f}% vs {overall_rate:.1f}% average")
        st.warning(f"💰 Salary gap: money is **NOT** the driver")
        st.info(f"👥 Younger employees at higher risk")
    
    with s2:
        st.markdown("##### 💡 Top Recommendations")
        st.success("🏠 **Expand remote work** — 28pp effect")
        st.success("🚀 **Build promotions** — 26pp effect")
        st.success("⚖️ **Audit overtime** — 6pp effect")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2: WORKLOAD (Q2, Q3)
# ═════════════════════════════════════════════════════════════════════════════
def page_workload():
    st.markdown("## ⏰ Workload & Flexibility")
    _kpi_row()
    st.markdown("---")
    
    _qbadge("Q2 · Overtime")
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
            title="Overtime vs Attrition", color="Overtime",
            color_discrete_map={"Yes": KB, "No": KB_LIGHT},
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(xaxis_title="", yaxis_title="Attrition Rate (%)", showlegend=False)
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), width='stretch')
    
    with c2:
        ot_yes = _safe_first(ot[ot["Overtime"]=="Yes"]["Attrition Rate (%)"])
        ot_no = _safe_first(ot[ot["Overtime"]=="No"]["Attrition Rate (%)"])
        gap = ot_yes - ot_no
        st.markdown("<br>", unsafe_allow_html=True)
        _insight(f"Overtime workers: <b>{ot_yes:.1f}%</b> vs <b>{ot_no:.1f}%</b> — <b>{gap:.1f}pp gap</b>")
        _cta("<b>🎯 Action:</b> Audit overtime. Reduce 20% in 2 quarters.")
    
    st.markdown("---")
    _qbadge("Q3 · Remote Work")
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
            remote, x="Location", y="Attrition Rate (%)",
            title="Remote vs On-site", color="Location",
            color_discrete_map={"Remote": KB, "On-site": KB_LIGHT},
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(xaxis_title="", yaxis_title="Attrition Rate (%)", showlegend=False)
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), width='stretch')
    
    with c2:
        r_remote = _safe_first(remote[remote["Location"]=="Remote"]["Attrition Rate (%)"])
        r_onsite = _safe_first(remote[remote["Location"]=="On-site"]["Attrition Rate (%)"])
        gap = r_onsite - r_remote
        st.markdown("<br>", unsafe_allow_html=True)
        _insight(f"Remote: <b>{r_remote:.1f}%</b> vs On-site: <b>{r_onsite:.1f}%</b> — <b>{gap:.1f}pp gap</b>")
        _cta("<b>🎯 Action:</b> 90-day remote pilot. Track pre/post attrition.")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3: PAY (Q4)
# ═════════════════════════════════════════════════════════════════════════════
def page_pay():
    st.markdown("## 💰 Pay & Job Level")
    _kpi_row()
    st.markdown("---")
    
    _qbadge("Q4 · Pay Fairness")
    _section("Does Higher Pay Within a Level Reduce Attrition?")
    
    jl = (
        dff.groupby("job_level", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)", "job_level": "Job Level"})
    )
    
    c1, c2 = st.columns(2)
    
    with c1:
        fig = px.bar(
            jl, x="Job Level", y="Attrition Rate (%)",
            title="Attrition by Job Level",
            color="Attrition Rate (%)", color_continuous_scale=BLUE_SEQ,
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="", yaxis_title="Attrition Rate (%)")
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), width='stretch')
        
        entry = _safe_first(jl[jl["Job Level"]=="Entry"]["Attrition Rate (%)"])
        senior = _safe_first(jl[jl["Job Level"]=="Senior"]["Attrition Rate (%)"])
        _insight(
            f"Entry: <b>{entry:.1f}%</b>, Senior: <b>{senior:.1f}%</b> — <b>{entry-senior:.0f}pp gap</b>. "
            f"Job Level is the strongest driver (43pp effect)."
        )
    
    with c2:
        pay_data = q.get("pay_by_level_quartile", pd.DataFrame())
        if not pay_data.empty:
            fig = px.bar(
                pay_data, x="income_quartile", y="Attrition Rate (%)",
                color="job_level", barmode="group",
                title="Pay Quartile Within Level",
                color_discrete_sequence=[KB_LIGHT, "#7FA8FF", KB],
            )
            fig.update_layout(xaxis_title="", legend_title="Job Level")
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
    
    _insight("Pay raises within a level only reduce attrition ~2pp. The level itself matters.")
    _cta("<b>🎯 Action:</b> Invest in promotion pathways to Mid-level, not salary increases.")
    
    st.markdown("---")
    _section("Income: Stayed vs Left")
    
    fig = px.box(
        dff, x=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        y="monthly_income",
        color=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        color_discrete_map=ATTRITION_MAP, points=False,
    )
    fig.update_layout(xaxis_title="", yaxis_title="Monthly Income ($)", showlegend=False)
    st.plotly_chart(_theme(fig), width='stretch')
    _insight("Income distributions nearly identical. <b>Compensation is NOT the driver.</b>")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 4: ENGAGEMENT (Q5, Q6, Q7)
# ═════════════════════════════════════════════════════════════════════════════
def page_engagement():
    st.markdown("## 🧠 Engagement & Life Stage")
    _kpi_row()
    st.markdown("---")
    
    _qbadge("Q5 · Retention Timeline")
    _section("When Are Employees Most Likely to Leave?")
    
    tenure_data = q.get("attrition_by_tenure", pd.DataFrame())
    if not tenure_data.empty:
        fig = px.bar(
            tenure_data, x="tenure_band", y="Attrition Rate (%)",
            title="Attrition by Tenure",
            color="Attrition Rate (%)", color_continuous_scale=BLUE_SEQ,
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Years", yaxis_title="Attrition Rate (%)")
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), width='stretch')
        
        peak = tenure_data.loc[tenure_data["Attrition Rate (%)"].idxmax()]
        _insight(f"Attrition peaks at <b>{peak['tenure_band']}</b> (<b>{peak['Attrition Rate (%)']:.1f}%</b>)")
        _cta("<b>🎯 Action:</b> Target 0–5 year employees with enhanced onboarding.")
    
    st.markdown("---")
    _qbadge("Q6 · Engagement Warning Signs")
    _section("Which WLB + Satisfaction Combo Is the Danger Zone?")
    
    cross_data = q.get("wlb_x_satisfaction", pd.DataFrame())
    if not cross_data.empty:
        pivot = cross_data.pivot(
            index="Work-Life Balance", columns="Job Satisfaction",
            values="Attrition Rate (%)",
        )
        wlb_order = ["Poor", "Fair", "Good", "Excellent"]
        sat_order = ["Low", "Medium", "High", "Very High"]
        pivot = pivot.reindex(index=[x for x in wlb_order if x in pivot.index],
                              columns=[x for x in sat_order if x in pivot.columns])
        
        fig = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
            colorscale=[[0, KB_LIGHT], [0.5, KB], [1, KB_DARK]],
            zmin=25, zmax=75, text=pivot.values, texttemplate="%{text:.1f}%",
        ))
        fig.update_layout(title="WLB × Satisfaction", xaxis_title="Satisfaction", yaxis_title="WLB", height=350)
        st.plotly_chart(_theme(fig), width='stretch')
        
        _insight("Danger zone: Poor WLB + Low Satisfaction = 67% attrition. WLB is dominant.")
        _cta("<b>🎯 Action:</b> Flag Poor/Fair WLB in quarterly pulse checks.")
    
    st.markdown("---")
    _qbadge("Q7 · Life Stage")
    _section("Do Age, Marital Status, and Dependents Matter?")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        age_data = q.get("attrition_by_age_group", pd.DataFrame())
        if not age_data.empty:
            fig = px.bar(
                age_data, x="Age Group", y="Attrition Rate (%)",
                title="By Age", color="Attrition Rate (%)",
                color_continuous_scale=BLUE_SEQ, text="Attrition Rate (%)",
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
                title="By Marital Status", color="Marital Status",
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
                title="By Dependents", markers=True, line_shape="spline",
            )
            fig.update_traces(line_color=KB, marker_color=KB, marker_size=8)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
    
    _insight("Highest-risk: young, single. With dependents = stable. Family = rootedness.")
    _cta("<b>🎯 Action:</b> Build community for young, single employees.")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 5: CAREER (Q8)
# ═════════════════════════════════════════════════════════════════════════════
def page_career():
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
                promo_data, x="Number of Promotions", y="Attrition Rate (%)",
                title="Attrition vs Promotions", markers=True, line_shape="spline",
            )
            fig.update_traces(line_color=KB, marker_color=KB, marker_size=9)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), width='stretch')
            
            p0 = _safe_first(promo_data[promo_data["Number of Promotions"]==0]["Attrition Rate (%)"])
            p4 = _safe_first(promo_data[promo_data["Number of Promotions"]==4]["Attrition Rate (%)"])
            _insight(f"0 promos: {p0:.1f}% → 4 promos: {p4:.1f}%. <b>Non-linear jump at 3 promotions.</b>")
    
    with c2:
        for col_key, label in [
            ("attrition_by_leadership_opportunities", "Leadership"),
            ("attrition_by_innovation_opportunities", "Innovation"),
        ]:
            opp_data = q.get(col_key, pd.DataFrame())
            if not opp_data.empty and len(opp_data.columns) >= 2:
                x_col = opp_data.columns[0]
                fig = px.bar(
                    opp_data, x=x_col, y="Attrition Rate (%)",
                    title=f"{label} Opportunities",
                    color=x_col, color_discrete_map={"Yes": KB, "No": KB_LIGHT},
                    text="Attrition Rate (%)",
                )
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(xaxis_title="", showlegend=False)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig), width='stretch')
    
    st.markdown("---")
    _section("Fully Stuck Profile")
    
    stuck_n = q.get("stuck_n", 0)
    stuck_rate = q.get("stuck_rate", 0.0)
    delta = stuck_rate - overall_rate
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"<div class='metric-card'><div class='metric-value'>{stuck_n:,}</div>"
            f"<div class='metric-label'>Stuck</div></div>",
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"<div class='metric-card'><div class='metric-value'>{stuck_rate:.1f}%</div>"
            f"<div class='metric-label'>Attrition</div></div>",
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"<div class='metric-card'><div class='metric-value' style='color:{RED};'>{delta:+.1f}pp</div>"
            f"<div class='metric-label'>vs Avg</div></div>",
            unsafe_allow_html=True
        )
    
    _risk(f"{stuck_n:,} employees fully stuck (0 promos, no leadership, no innovation). <b>Systemic issue.</b>")
    _cta("<b>🎯 Action:</b> Assign 90-day development plans. Move 30% out within 2 quarters.")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 6: RISK & STRATEGY (Q9, Q10)
# ═════════════════════════════════════════════════════════════════════════════
def page_risk():
    st.markdown("## 🎯 Risk & Strategy")
    _kpi_row()
    st.markdown("---")
    
    _qbadge("Q9 · Highest-Risk Profile")
    _section("Who Is Most Likely to Leave?")
    
    risk_n = q.get("risk_profile_n", 0)
    risk_rate = q.get("risk_profile_rate", 0.0)
    risk_lift = risk_rate - overall_rate
    
    _risk(
        f"<b>Profile:</b> Poor WLB + Overtime + 0 Promotions + No Leadership<br>"
        f"<b>Attrition: {risk_rate:.1f}%</b> ({risk_lift:+.1f}pp) · <b>{risk_n:,} employees</b>"
    )
    
    c1, c2 = st.columns(2)
    
    with c1:
        factors = pd.DataFrame({
            "Factor": ["Poor WLB", "Overtime", "Zero Promotions", "No Leadership"],
            "Attrition Rate (%)": [60.2, 51.5, 49.3, 47.6],
        })
        fig = px.bar(
            factors.sort_values("Attrition Rate (%)"),
            x="Attrition Rate (%)", y="Factor", orientation="h",
            title="Risk Factors",
            color="Attrition Rate (%)", color_continuous_scale=BLUE_SEQ,
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_coloraxes(showscale=False)
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), width='stretch')
    
    with c2:
        comparison = pd.DataFrame({
            "Group": ["Company Avg", "Risk Profile"],
            "Attrition Rate (%)": [overall_rate, risk_rate],
        })
        fig = px.bar(
            comparison, x="Group", y="Attrition Rate (%)",
            title="Risk vs Average",
            color="Group", color_discrete_map={"Company Avg": KB_LIGHT, "Risk Profile": KB},
            text="Attrition Rate (%)",
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(_theme(fig), width='stretch')
    
    _insight(f"{risk_rate:.1f}% attrition (1.4× avg). ~{int(risk_n * risk_rate/100):,} departures from this cohort.")
    _cta(f"<b>🎯 Action:</b> HR partner touchpoint for {risk_n:,} within 30 days. Eliminate 2+ risk factors. Prevent ~{int(risk_n * risk_rate/100 * 0.2):,} departures.")
    
    st.markdown("---")
    _qbadge("Q10 · What Moves the Needle")
    _section("If HR Could Fix One Thing Next Quarter...")
    
    drivers = q.get("driver_ranking", pd.DataFrame())
    if not drivers.empty:
        fig = px.bar(
            drivers, x="Effect (pp)", y="Driver", orientation="h",
            title="Top Drivers by Effect Size",
            color="Effect (pp)", color_continuous_scale=BLUE_SEQ,
            text="Effect (pp)",
        )
        fig.update_traces(texttemplate="%{text:.1f}pp", textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Attrition Difference (pp)", yaxis_title="")
        st.plotly_chart(_theme(fig), width='stretch')
    
    st.markdown("### 🏆 Top 3 Recommendations")
    r1, r2, r3 = st.columns(3)
    
    with r1:
        st.markdown(
            "<div class='risk-card'><b>#1 · Remote Work</b><br>"
            "Effect: <b>28.1pp</b><br>"
            "Policy change in 2 weeks. 19% remote now."
            "</div>",
            unsafe_allow_html=True,
        )
    
    with r2:
        st.markdown(
            "<div class='rec-box'><b>#2 · Promotions</b><br>"
            "Effect: <b>26.0pp</b><br>"
            "Non-linear jump at 3rd promotion."
            "</div>",
            unsafe_allow_html=True,
        )
    
    with r3:
        st.markdown(
            "<div class='rec-box'><b>#3 · Work-Life Balance</b><br>"
            "Effect: <b>24.5pp</b><br>"
            "Overrides job satisfaction."
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
        "**Month 3:** Launch peer-community programme for 18–25 single employees"
    )
    
    st.markdown("---")
    st.caption("Kayfa · Week 1 · HR Attrition Analytics · Synthetic dataset for learning")

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
