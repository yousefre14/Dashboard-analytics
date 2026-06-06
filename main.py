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

# PAGE CONFIG
st.set_page_config(
    page_title="Workforce Retention Intelligence · Kayfa",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# BRAND CONSTANTS
KB        = "#1A5AFF"
KB_DARK   = "#1245CC"
KB_LIGHT  = "#E8EFFF"
AMBER     = "#F59E0B"
GREEN     = "#16A34A"
RED       = "#DC2626"
WHITE     = "#FFFFFF"
DARK_BG   = "#0F1419"
ATTRITION_MAP = {"Stayed": KB_LIGHT, "Left": KB}

# CLEAN CSS - MINIMAL SIDEBAR
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── SIDEBAR - MINIMAL ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #1A5AFF 0%, #1245CC 100%) !important;
    width: 280px !important;
}

section[data-testid="stSidebar"] > div:first-child {
    width: 280px !important;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

/* Hide sidebar header/logo area - CLEAN */
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:first-child {
    display: none !important;
}

section[data-testid="stSidebar"] > div:first-child > div:first-child {
    padding-top: 1rem !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.3) !important;
    margin: 0.8rem 0 !important;
}

section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
    font-weight: 700;
    margin-bottom: 0.8rem;
}

/* Filter Styling */
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background: rgba(255,255,255,0.2) !important;
    color: white !important;
    border-radius: 4px !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.15) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    color: white !important;
}

section[data-testid="stSidebar"] .stRadio > label {
    color: white !important;
    font-weight: 500;
}

section[data-testid="stSidebar"] .stSlider > label {
    color: white !important;
}

/* ── MAIN CONTENT ── */
[data-testid="stMainBlockContainer"] {
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
}

/* ── INSIGHT BOX ── */
.insight-box {
    background: rgba(26,90,255,0.08);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin: 0.8rem 0;
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
    margin: 0.8rem 0;
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
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# LOGO LOADER
@st.cache_data
def load_logo():
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

# PLOTLY THEME - SINGLE COLOR, LARGER CHARTS
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", size=12),
    margin=dict(t=50, b=40, l=60, r=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    hovermode="x unified",
)

def _theme(fig: go.Figure, height: int = 500) -> go.Figure:
    """Apply Kayfa theme with larger height"""
    fig.update_layout(**_LAYOUT, height=height)
    fig.update_xaxes(
        gridcolor="rgba(26,90,255,0.1)", 
        linecolor="rgba(26,90,255,0.2)", 
        tickfont_size=11,
        showgrid=True
    )
    fig.update_yaxes(
        gridcolor="rgba(26,90,255,0.1)", 
        linecolor="rgba(26,90,255,0.2)", 
        tickfont_size=11,
        showgrid=True
    )
    return fig

def _add_avg_line(fig: go.Figure, y_val: float, label: str = "Company Average") -> go.Figure:
    """Add reference line"""
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

# DATA LOADING
@st.cache_data(show_spinner="🔄 Loading data…")
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
        st.error(f"Data Loading Failed: {str(e)}")
        st.stop()

df, aggs, q = get_data()
overall_rate = aggs["overall_rate"] * 100

# SIDEBAR 
with st.sidebar:
    st.markdown("### 🔍 Filters")
    
    all_roles   = sorted(df["job_role"].unique().tolist())
    all_genders = sorted(df["gender"].unique().tolist())
    all_levels  = df["job_level"].cat.categories.tolist()
    all_sizes   = df["company_size"].cat.categories.tolist()
    
    sel_roles   = st.multiselect("Job Role", all_roles, default=all_roles)
    sel_genders = st.multiselect("Gender", all_genders, default=all_genders)
    sel_levels  = st.multiselect("Job Level", all_levels, default=all_levels)
    sel_sizes   = st.multiselect("Company Size", all_sizes, default=all_sizes)
    
    age_min, age_max = int(df["age"].min()), int(df["age"].max())
    sel_age = st.slider("Age Range", age_min, age_max, (age_min, age_max))
    
    sel_remote = st.radio("Work Location", ["All", "Remote Only", "On-site Only"], index=0)
    sel_ot = st.radio("Overtime", ["All", "With Overtime", "No Overtime"], index=0)

# FILTER MASK
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
    st.warning("⚠️ No employees match filters. Adjust sidebar.")
    st.stop()

kpis = filtered_kpis(dff)

# SHARED KPI ROW
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

# PAGE 1: OVERVIEW WITH TABS
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
            st.image(logo, width=420)
        else:
            st.markdown(
                "<div style='text-align:center;font-size:2.2rem;font-weight:900;color:#1A5AFF;'>كيف</div>",
                unsafe_allow_html=True,
            )
    
    st.markdown("---")
    _kpi_row()
    st.markdown("---")
    
    # TABBED QUESTIONS
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "Headline",
        "Overtime",
        "Remote Work",
        "Pay Fairness",
        "Timeline",
        "Engagement",
        "Life Stage",
        "Stagnation",
        "Risk Profile",
        "Drivers"
    ])
    
    # Q1: THE HEADLINE
    # ────────────────────────────────────────────────────────────────────────
# Q1: THE HEADLINE
# ────────────────────────────────────────────────────────────────────────
    with tab1:
        _qbadge("The Headline")
        _section("Who Is Leaving — and Where to Look First")
            
        role_data = (
            dff.groupby("job_role", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "job_role": "Job Role"})
            .sort_values("Attrition Rate (%)", ascending=True)
        )
        
        if len(role_data) > 0:
            # CHART 1: Attrition by Role (FULL WIDTH, TALL)
            fig = px.bar(
            role_data,
            x="Attrition Rate (%)",
            y="Job Role",
            orientation="h",
            title="Attrition Rate by Job Role",
            text="Attrition Rate (%)",
        )
        fig.update_traces(
            texttemplate="%{x:.1f}%",
            textposition="outside",
            marker_color=KB,
            marker_line=dict(width=0),
        )
        fig.update_layout(
            yaxis_title="",
            xaxis_title="Attrition Rate (%)",
            showlegend=False,
            height=400,
            margin=dict(l=100, r=50, t=60, b=60),
            xaxis=dict(range=[0, role_data["Attrition Rate (%)"].max() + 10]),
        )
       _add_avg_line(fig, overall_rate, is_horizontal=True)
        st.plotly_chart(_theme(fig, height=450), width='stretch')
        
        top_role = role_data.iloc[-1]
        pp = top_role['Attrition Rate (%)'] - overall_rate
        _insight(f"<b>{top_role['Job Role']}</b> leads at <b>{top_role['Attrition Rate (%)']:.1f}%</b> — {pp:+.1f}pp vs {overall_rate:.1f}% average.")
        _cta("<b>🎯 Action:</b> Company-wide policy response, not role-specific fixes.")
    
    st.markdown("---")
        
        # CHART 2: Workforce Split (PIE)
    stayed = int((dff["attrition"] == 0).sum())
    left = int((dff["attrition"] == 1).sum())
    total = stayed + left
    
    fig = go.Figure(go.Pie(
        labels=["Stayed", "Left"], 
        values=[stayed, left], 
        hole=0.62,
        marker=dict(
            colors=[KB_LIGHT, KB],
            line=dict(color='white', width=2)
        ),
        textinfo="percent+label",
        textposition="auto",
        textfont=dict(size=13, color="white"),
    ))
    fig.update_layout(
        title="Workforce Split",
        height=450 + (len(role_data) * 20),
        margin=dict(l=100, r=50, t=80, b=50),
        annotations=[dict(
            text=f"<b>{_safe_pct(left, total):.1f}%</b><br>Left",
            x=0.5, y=0.5, font=dict(size=16, color=KB), showarrow=False,
        )],
    )
    st.plotly_chart(_theme(fig), use_container_width=True)
    _insight(f"<b>{left:,}</b> left · <b>{stayed:,}</b> retained")
    
    # Q2: OVERTIME
    with tab2:
        _qbadge("Overtime Burden")
        _section("Are Employees Who Work Overtime More Likely to Leave?")
        
        ot = (
            dff.groupby("overtime", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "overtime": "Overtime"})
        )
        
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            fig = px.bar(
                ot, 
                x="Overtime", 
                y="Attrition Rate (%)",
                title="Overtime vs Attrition", 
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%", 
                textposition="outside",
                marker_color=KB,
                marker_line=dict(width=0)
            )
            fig.update_layout(
                xaxis_title="Works Overtime", 
                yaxis_title="Attrition Rate (%)", 
                showlegend=False
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig, height=450), width='stretch')
        
        with c2:
            ot_yes = _safe_first(ot[ot["Overtime"]=="Yes"]["Attrition Rate (%)"])
            ot_no = _safe_first(ot[ot["Overtime"]=="No"]["Attrition Rate (%)"])
            gap = ot_yes - ot_no
            st.markdown("<br><br>", unsafe_allow_html=True)
            _insight(f"<b>{ot_yes:.1f}%</b> vs <b>{ot_no:.1f}%</b> — <b>{gap:.1f}pp gap</b>")
            _cta("<b>🎯 Action:</b> Overtime audit. 20% reduction in 2Q.")
    
    # ────────────────────────────────────────────────────────────────────────
    # Q3: REMOTE WORK
    # ────────────────────────────────────────────────────────────────────────
    with tab3:
        _qbadge("Remote Work Policy")
        _section("Does Remote Work Keep People?")
        
        remote = (
            dff.groupby("remote_work", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "remote_work": "Location"})
        )
        remote["Location"] = remote["Location"].map({"Yes": "Remote", "No": "On-site"})
        
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            fig = px.bar(
                remote, 
                x="Location", 
                y="Attrition Rate (%)",
                title="Remote vs On-site", 
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%", 
                textposition="outside",
                marker_color=KB,
                marker_line=dict(width=0)
            )
            fig.update_layout(
                xaxis_title="", 
                yaxis_title="Attrition Rate (%)", 
                showlegend=False
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig, height=450), width='stretch')
        
        with c2:
            r_remote = _safe_first(remote[remote["Location"]=="Remote"]["Attrition Rate (%)"])
            r_onsite = _safe_first(remote[remote["Location"]=="On-site"]["Attrition Rate (%)"])
            gap = r_onsite - r_remote
            st.markdown("<br><br>", unsafe_allow_html=True)
            _insight(f"<b>{r_remote:.1f}%</b> vs <b>{r_onsite:.1f}%</b> — <b>{gap:.1f}pp gap</b>")
            _cta("<b>🎯 Action:</b> 90-day pilot for on-site roles.")
    
    # Q4: PAY FAIRNESS
    with tab4:
        _qbadge("Pay Fairness Within Job Levels")
        _section("Does Higher Pay Within a Level Reduce Attrition?")
        
        jl = (
            dff.groupby("job_level", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "job_level": "Job Level"})
        )
        
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            fig = px.bar(
                jl, 
                x="Job Level", 
                y="Attrition Rate (%)",
                title="Attrition by Job Level",
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%", 
                textposition="outside",
                marker_color=KB,
                marker_line=dict(width=0)
            )
            fig.update_layout(xaxis_title="", yaxis_title="Attrition Rate (%)", showlegend=False)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig, height=450), width='stretch')
            
            entry = _safe_first(jl[jl["Job Level"]=="Entry"]["Attrition Rate (%)"])
            senior = _safe_first(jl[jl["Job Level"]=="Senior"]["Attrition Rate (%)"])
            _insight(
                f"Entry: <b>{entry:.1f}%</b>, Senior: <b>{senior:.1f}%</b> — "
                f"<b>{entry-senior:.0f}pp gap.</b> Job Level is strongest driver."
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
                )
                fig.update_layout(xaxis_title="", legend_title="Level", showlegend=False)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=450), width='stretch')
        
        _cta("<b>🎯 Action:</b> Invest in promotion pathways, not salary hikes.")
    
    # Q5: RETENTION TIMELINE
    with tab5:
        _qbadge("Retention Timeline")
        _section("When Are Employees Most Likely to Leave?")
        
        tenure_data = q.get("attrition_by_tenure", pd.DataFrame())
        if not tenure_data.empty:
            fig = px.bar(
                tenure_data, 
                x="tenure_band", 
                y="Attrition Rate (%)",
                title="Attrition by Tenure",
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%", 
                textposition="outside",
                marker_color=KB,
                marker_line=dict(width=0)
            )
            fig.update_layout(xaxis_title="Years at Company", yaxis_title="Attrition Rate (%)", showlegend=False)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig, height=500), width='stretch')
            
            peak = tenure_data.loc[tenure_data["Attrition Rate (%)"].idxmax()]
            _insight(f"Peak at <b>{peak['tenure_band']}</b> (<b>{peak['Attrition Rate (%)']:.1f}%</b>)")
            _cta("<b>🎯 Action:</b> Target 0–5yr with enhanced onboarding.")
    
    # Q6: ENGAGEMENT WARNING SIGNS
    with tab6:
        _qbadge("Engagement Warning Signs")
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
            )
            st.plotly_chart(_theme(fig, height=500), width='stretch')
            
            _insight("Danger: <b>Poor WLB + Low Satisfaction = 67%</b> attrition. WLB is dominant.")
            _cta("<b>🎯 Action:</b> Flag Poor/Fair WLB in pulse checks.")
    
    # Q7: LIFE STAGE
    with tab7:
        _qbadge("Life Stage Factors")
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
                    text="Attrition Rate (%)",
                )
                fig.update_traces(
                    texttemplate="%{y:.1f}%", 
                    marker_color=KB,
                    marker_line=dict(width=0)
                )
                fig.update_layout(showlegend=False)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=400), width='stretch')
        
        with c2:
            marital_data = q.get("attrition_by_marital", pd.DataFrame())
            if not marital_data.empty:
                fig = px.bar(
                    marital_data, 
                    x="Marital Status", 
                    y="Attrition Rate (%)",
                    title="By Marital Status",
                    text="Attrition Rate (%)",
                )
                fig.update_traces(
                    texttemplate="%{y:.1f}%", 
                    marker_color=KB,
                    marker_line=dict(width=0)
                )
                fig.update_layout(showlegend=False)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=400), width='stretch')
        
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
                st.plotly_chart(_theme(fig, height=400), width='stretch')
        
        _insight("Highest-risk: young, single. With dependents = stable.")
        _cta("<b>🎯 Action:</b> Community programs for young employees.")
    
    # Q8: CAREER STAGNATION
    with tab8:
        _qbadge("Career Stagnation")
        _section("Does Feeling Stuck Drive Attrition?")
        
        c1, c2 = st.columns([1.5, 1])
        
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
                fig.update_traces(line_color=KB, marker_color=KB, marker_size=10)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=450), width='stretch')
                
                p0 = _safe_first(promo_data[promo_data["Number of Promotions"]==0]["Attrition Rate (%)"])
                p4 = _safe_first(promo_data[promo_data["Number of Promotions"]==4]["Attrition Rate (%)"])
                _insight(f"0 promos: <b>{p0:.1f}%</b> → 4 promos: <b>{p4:.1f}%</b>. Non-linear jump at 3rd.")
        
        with c2:
            opp_data = q.get("attrition_by_leadership_opportunities", pd.DataFrame())
            if not opp_data.empty and len(opp_data.columns) >= 2:
                x_col = opp_data.columns[0]
                fig = px.bar(
                    opp_data, 
                    x=x_col, 
                    y="Attrition Rate (%)",
                    title="Leadership Opportunities",
                    text="Attrition Rate (%)",
                )
                fig.update_traces(
                    texttemplate="%{y:.1f}%",
                    marker_color=KB,
                    marker_line=dict(width=0)
                )
                fig.update_layout(xaxis_title="", showlegend=False)
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=450), width='stretch')
        
        stuck_n = q.get("stuck_n", 0)
        stuck_rate = q.get("stuck_rate", 0.0)
        _risk(f"<b>{stuck_n:,}</b> fully stuck: 0 promos + no leadership + no innovation = <b>{stuck_rate:.1f}%</b> attrition.")
        _cta(f"<b>🎯 Action:</b> 90-day dev plans for {stuck_n:,} employees.")
    
    # Q9: HIGHEST-RISK PROFILE
    with tab9:
        _qbadge("Highest-Risk Profile")
        _section("Who Is Most Likely to Leave?")
        
        risk_n = q.get("risk_profile_n", 0)
        risk_rate = q.get("risk_profile_rate", 0.0)
        risk_lift = risk_rate - overall_rate
        
        _risk(f"<b>Profile:</b> Poor WLB + Overtime + 0 Promos + No Leadership<br>"
              f"<b>{risk_rate:.1f}%</b> attrition ({risk_lift:+.1f}pp) · <b>{risk_n:,} employees</b>")
        
        c1, c2 = st.columns([1.5, 1])
        
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
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{x:.1f}%", 
                marker_color=KB,
                marker_line=dict(width=0)
            )
            fig.update_layout(showlegend=False)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig, height=450), width='stretch')
        
        with c2:
            comparison = pd.DataFrame({
                "Group": ["Avg", "Risk"],
                "Attrition Rate (%)": [overall_rate, risk_rate],
            })
            fig = px.bar(
                comparison, 
                x="Group", 
                y="Attrition Rate (%)",
                title="Risk vs Average",
                text="Attrition Rate (%)",
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%",
                marker_color=KB,
                marker_line=dict(width=0)
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(_theme(fig, height=450), width='stretch')
        
        _cta(f"<b>🎯 Action:</b> HR touchpoint for {risk_n:,} within 30 days.")
    
    # Q10: WHAT MOVES THE NEEDLE
    with tab10:
        _qbadge("What Moves the Needle")
        _section("If HR Could Fix One Thing Next Quarter...")
        
        drivers = q.get("driver_ranking", pd.DataFrame())
        if not drivers.empty:
            fig = px.bar(
                drivers, 
                x="Effect (pp)", 
                y="Driver", 
                orientation="h",
                title="Top Drivers by Effect Size",
                text="Effect (pp)",
            )
            fig.update_traces(
                texttemplate="%{x:.1f}pp",
                marker_color=KB,
                marker_line=dict(width=0)
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(_theme(fig, height=450), width='stretch')
        
        st.markdown("### 🏆 Top 3 Recommendations")
        r1, r2, r3 = st.columns(3)
        
        with r1:
            st.markdown(
                "<div class='rec-box'><b>#1 Remote Work</b><br>28.1pp effect<br>2-week policy</div>",
                unsafe_allow_html=True,
            )
        
        with r2:
            st.markdown(
                "<div class='rec-box'><b>#2 Promotions</b><br>26.0pp effect<br>Non-linear jump</div>",
                unsafe_allow_html=True,
            )
        
        with r3:
            st.markdown(
                "<div class='rec-box'><b>#3 Work-Life Balance</b><br>24.5pp effect<br>Overrides satisfaction</div>",
                unsafe_allow_html=True,
            )

# NAVIGATION
pg = st.navigation({
    "📊 Dashboard": [
        st.Page(page_overview, title="Overview", icon="🏠", default=True),
    ],
})

pg.run()
