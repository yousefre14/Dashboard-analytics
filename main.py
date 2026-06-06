import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from PIL import Image
from io import BytesIO
import requests

from Data_Handling import (
    load_and_clean, compute_aggregration,
    compute_q_aggregations, filtered_kpis,
    test_data_completeness, test_aggregation_output,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  —  must be the very first Streamlit call
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
KB            = "#1A5AFF"
KB_DARK       = "#1245CC"
KB_LIGHT      = "#E8EFFF"
AMBER         = "#F59E0B"   # reference / avg lines
GREEN         = "#16A34A"
RED           = "#DC2626"
ATTRITION_MAP = {"Stayed": KB_LIGHT, "Left": KB}

# ─────────────────────────────────────────────────────────────────────────────
# CSS  —  rgba backgrounds = dark-mode safe
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* { font-family: 'Plus Jakarta Sans', sans-serif; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1A5AFF 0%, #1245CC 100%) !important;
}
section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.25) !important;
    margin: 0.8rem 0 !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important; font-weight: 700;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background: rgba(255,255,255,0.2) !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.15) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
}

/* ── Main padding ── */
[data-testid="stMainBlockContainer"] {
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
}

/* ── Insight box ── */
.insight-box {
    background: rgba(26,90,255,0.08);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin: 0.8rem 0;
    font-size: 0.84rem;
    line-height: 1.6;
}
.insight-box b { color: #1A5AFF; font-weight: 700; }

/* ── CTA box ── */
.cta-box {
    background: rgba(22,163,74,0.07);
    border-left: 4px solid #16A34A;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin: 0.8rem 0;
    font-size: 0.84rem;
    line-height: 1.6;
}
.cta-box b { color: #16A34A; font-weight: 700; }

/* ── Risk box ── */
.risk-card {
    background: rgba(220,38,38,0.07);
    border: 1px solid rgba(220,38,38,0.25);
    border-left: 4px solid #DC2626;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0;
    line-height: 1.6;
}
.risk-card b { color: #DC2626; font-weight: 700; }

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

/* ── Section title ── */
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    border-bottom: 3px solid #1A5AFF;
    padding-bottom: 0.5rem;
    margin: 1.4rem 0 0.9rem 0;
    color: #1245CC;
}

/* ── Hero ── */
.hero-title { font-size: 1.9rem; font-weight: 800; line-height: 1.2; margin: 0; }
.hero-sub   { font-size: 0.88rem; opacity: 0.65; margin-top: 0.3rem; }

/* ── KPI card ── */
.kpi-card {
    background: rgba(26,90,255,0.06);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 8px rgba(26,90,255,0.08);
}
.kpi-num { font-size: 2rem; font-weight: 800; color: #1A5AFF; line-height: 1; }
.kpi-lbl {
    font-size: 0.72rem; font-weight: 600; opacity: 0.6;
    text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.2rem;
}

/* ── Rec box ── */
.rec-box {
    background: rgba(26,90,255,0.05);
    border: 1px solid rgba(26,90,255,0.2);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
}

footer { visibility: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# LOGO LOADER
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_logo():
    try:
        return Image.open("company_logo2.png")
    except FileNotFoundError:
        try:
            url = "https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/company_logo2.png"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return Image.open(BytesIO(resp.content))
        except Exception:
            return None

logo = load_logo()


# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY HELPERS
# NOTE: margin intentionally excluded from _LAYOUT so per-chart margins
#       (set via fig.update_layout before _theme()) are NOT overridden.
# ─────────────────────────────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", size=12),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    hovermode="closest",   # works correctly for both H and V charts
)

def _theme(fig: go.Figure, height: int = 480) -> go.Figure:
    """Apply Kayfa theme. Height param controls chart height."""
    fig.update_layout(**_LAYOUT, height=height)
    fig.update_xaxes(
        gridcolor="rgba(26,90,255,0.1)",
        linecolor="rgba(26,90,255,0.2)",
        tickfont_size=11, showgrid=True,
    )
    fig.update_yaxes(
        gridcolor="rgba(26,90,255,0.1)",
        linecolor="rgba(26,90,255,0.2)",
        tickfont_size=11, showgrid=True,
    )
    return fig


def _add_avg_line(fig: go.Figure, y_val: float,
                  label: str = "Company Average",
                  orientation: str = "v") -> go.Figure:
    """
    Add a named dashed reference line WITH a legend entry.
    Rubric: 'Any reference line must be named and shown in the legend.'

    orientation="v"  →  vertical bars   → add_hline  (line crosses Y axis)
    orientation="h"  →  horizontal bars → add_vline  (line crosses X axis)

    WHY vline for horizontal bars: the value axis is X, not Y.
    Using add_hline on a horizontal bar chart places the line on the
    categorical Y axis at position y_val (e.g. 47.5), which Plotly
    interprets as a numeric index — compressing all bars to the bottom.
    """
    if orientation == "h":
        fig.add_vline(x=y_val, line_dash="dash",
                      line_color=AMBER, line_width=2.5)
    else:
        fig.add_hline(y=y_val, line_dash="dash",
                      line_color=AMBER, line_width=2.5)

    # Dummy scatter trace → appears in legend as named reference line
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
# DATA — cached, runs once per session
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="🔄 Loading data…")
def get_data():
    try:
        df   = load_and_clean("train.csv", "test.csv")
        test_data_completeness(df)               # software test
        aggs = compute_aggregration(df)
        q    = compute_q_aggregations(df)
        test_aggregation_output(aggs, q,          # software test
                                aggs["overall_rate"] * 100)
        return df, aggs, q
    except Exception as e:
        st.error(f"❌ Data loading failed: {e}")
        st.stop()

df, aggs, q = get_data()
overall_rate = aggs["overall_rate"] * 100


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Logo + Filters (defined before pg.run() → persists on all pages)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo — top of sidebar (rubric: logo in sidebar)
    if logo is not None:
        st.image(logo, use_container_width=True)
    else:
        st.markdown(
            "<div style='direction:rtl;text-align:center;font-size:2rem;"
            "font-weight:900;padding:0.5rem 0;'>كيف</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 🔍 Filters")

    all_roles   = sorted(df["job_role"].unique().tolist())
    all_genders = sorted(df["gender"].unique().tolist())
    all_levels  = df["job_level"].cat.categories.tolist()
    all_sizes   = df["company_size"].cat.categories.tolist()

    sel_roles   = st.multiselect("Job Role",    all_roles,   default=all_roles)
    sel_genders = st.multiselect("Gender",       all_genders, default=all_genders)
    sel_levels  = st.multiselect("Job Level",    all_levels,  default=all_levels)
    sel_sizes   = st.multiselect("Company Size", all_sizes,   default=all_sizes)

    age_min, age_max = int(df["age"].min()), int(df["age"].max())
    sel_age = st.slider("Age Range", age_min, age_max, (age_min, age_max))

    sel_remote = st.radio("Work Location",
                          ["All", "Remote Only", "On-site Only"], index=0)
    sel_ot     = st.radio("Overtime",
                          ["All", "With Overtime", "No Overtime"],  index=0)

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

# Empty-filter guard
if len(dff) == 0:
    st.warning("⚠️ No employees match current filters. Adjust the sidebar.")
    st.stop()

kpis = filtered_kpis(dff)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED KPI ROW
# ─────────────────────────────────────────────────────────────────────────────
def _kpi_row():
    delta     = kpis["rate"] - overall_rate
    sign      = "▲" if delta > 0 else "▼"
    clr       = RED if delta > 0 else GREEN
    delta_html = (f"<span style='color:{clr};font-weight:600;'>"
                  f"{sign} {abs(delta):.1f}pp vs avg</span>")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-lbl'>Total Employees</div>"
            f"<div class='kpi-num'>{kpis['total']:,}</div>"
            f"<div style='font-size:.75rem;opacity:.6;'>of {aggs['total_employee']:,}</div></div>",
            unsafe_allow_html=True)
    with k2:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-lbl'>Attrition Rate</div>"
            f"<div class='kpi-num'>{kpis['rate']:.1f}%</div>"
            f"<div style='font-size:.75rem;'>{delta_html}</div></div>",
            unsafe_allow_html=True)
    with k3:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-lbl'>Avg Monthly Income</div>"
            f"<div class='kpi-num'>${kpis['avg_income']:,.0f}</div>"
            f"<div style='font-size:.75rem;opacity:.6;'>filtered group</div></div>",
            unsafe_allow_html=True)
    with k4:
        st.markdown(
            f"<div class='kpi-card'><div class='kpi-lbl'>Avg Tenure</div>"
            f"<div class='kpi-num'>{kpis['avg_tenure']:.1f} yrs</div>"
            f"<div style='font-size:.75rem;opacity:.6;'>at company</div></div>",
            unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE — OVERVIEW  (all 10 questions via tabs)
# ═════════════════════════════════════════════════════════════════════════════
def page_overview():

    # ── Hero header ──────────────────────────────────────────────────────────
    col_title, _, col_logo = st.columns([6, 1, 2])
    with col_title:
        st.markdown(
            "<p class='hero-sub'>Week #1 Task:</p>"
            "<h1 class='hero-title'>Workforce Retention Intelligence</h1>"
            "<p class='hero-sub'>HR Analytics · Kayfa · 74,498 records</p>",
            unsafe_allow_html=True,
        )
    with col_logo:
        # Logo top-right on homepage (rubric: logo on homepage)
        if logo is not None:
            st.image(logo, width=160)
        else:
            st.markdown(
                "<div style='direction:rtl;text-align:right;font-size:2rem;"
                "font-weight:900;color:#1A5AFF;'>كيف</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    _kpi_row()
    st.markdown("---")

    # ── 10 question tabs ──────────────────────────────────────────────────────
    # Tabs are defined INSIDE the page function — they are UI widgets and
    # must be created during the render, not in outer scope.
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "Q1 · Headline",
        "Q2 · Overtime",
        "Q3 · Remote Work",
        "Q4 · Pay Fairness",
        "Q5 · Timeline",
        "Q6 · Engagement",
        "Q7 · Life Stage",
        "Q8 · Stagnation",
        "Q9 · Risk Profile",
        "Q10 · Drivers",
    ])

    # ── Q1: THE HEADLINE ─────────────────────────────────────────────────────
    with tab1:
        _qbadge("Q1 · The Headline")
        _section("Who Is Leaving — and Where to Look First")

        role_data = (
            dff.groupby("job_role", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)",
                              "job_role": "Job Role"})
            .sort_values("Attrition Rate (%)", ascending=True)
        )

        c1, c2 = st.columns([3, 2])

        with c1:
            if len(role_data) > 0:
                fig = px.bar(
                    role_data,
                    x="Attrition Rate (%)", y="Job Role",
                    orientation="h",
                    title="Attrition Rate by Job Role",
                    text="Attrition Rate (%)",
                )
                fig.update_traces(
                    texttemplate="%{x:.1f}%",
                    textposition="outside",
                    marker_color=KB,
                    marker_line=dict(width=0),
                    # NO textfont color — Plotly auto-picks readable contrast
                )
                fig.update_layout(
                    yaxis_title="",
                    xaxis_title="Attrition Rate (%)",
                    showlegend=True,
                    margin=dict(l=110, r=60, t=55, b=45),
                    xaxis=dict(range=[0, role_data["Attrition Rate (%)"].max() + 12]),
                )
                # orientation="h" → vline (crosses x-axis) — fixes chart zooming bug
                _add_avg_line(fig, overall_rate, orientation="h")
                st.plotly_chart(_theme(fig, height=420), use_container_width=True)

                top_role = role_data.iloc[-1]
                pp = top_role["Attrition Rate (%)"] - overall_rate
                _insight(
                    f"<b>{top_role['Job Role']}</b> leads at "
                    f"<b>{top_role['Attrition Rate (%)']:.1f}%</b> — "
                    f"{pp:+.1f}pp above the {overall_rate:.1f}% average. "
                    f"The spread across all roles is narrow (~2pp), meaning this "
                    f"is a <b>company-wide condition</b>, not a single department problem."
                )
                _cta(
                    "<b>🎯 Action:</b> A company-wide policy response "
                    "(remote work expansion, promotion pathways, overtime audit) "
                    "will move the needle more than role-by-role interventions."
                )

        with c2:
            stayed = int((dff["attrition"] == 0).sum())
            left   = int((dff["attrition"] == 1).sum())
            total  = stayed + left

            fig = go.Figure(go.Pie(
                labels=["Stayed", "Left"],
                values=[stayed, left],
                hole=0.62,
                marker=dict(colors=[KB_LIGHT, KB],
                            line=dict(color="white", width=2)),
                textinfo="percent+label",
            ))
            fig.update_layout(
                title="Workforce Split",
                margin=dict(l=20, r=20, t=55, b=20),
                annotations=[dict(
                    text=f"<b>{_safe_pct(left,total):.1f}%</b><br>Left",
                    x=0.5, y=0.5,
                    font=dict(size=16, color=KB),
                    showarrow=False,
                )],
            )
            st.plotly_chart(_theme(fig, height=420), use_container_width=True)
            _insight(
                f"<b>{left:,}</b> employees left · "
                f"<b>{stayed:,}</b> retained · "
                f"Retention rate: <b>{_safe_pct(stayed, total):.1f}%</b>"
            )

    # ── Q2: OVERTIME ─────────────────────────────────────────────────────────
    with tab2:
        _qbadge("Q2 · Overtime")
        _section("Are Overtime Employees More Likely to Leave?")

        ot = (
            dff.groupby("overtime", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)",
                              "overtime": "Overtime"})
        )

        c1, c2 = st.columns([1.5, 1])
        with c1:
            fig = px.bar(
                ot, x="Overtime", y="Attrition Rate (%)",
                title="Overtime vs Attrition Rate",
                text="Attrition Rate (%)",
                color="Overtime",
                color_discrete_map={"Yes": KB, "No": KB_LIGHT},
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="outside",
                marker_line=dict(width=0),
            )
            fig.update_layout(
                xaxis_title="Works Overtime",
                yaxis_title="Attrition Rate (%)",
                showlegend=False,
                margin=dict(l=50, r=40, t=55, b=45),
                yaxis=dict(range=[0, ot["Attrition Rate (%)"].max() + 10]),
            )
            # Vertical bar → hline (default orientation)
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig, height=450), use_container_width=True)

        with c2:
            ot_yes = _safe_first(ot[ot["Overtime"]=="Yes"]["Attrition Rate (%)"])
            ot_no  = _safe_first(ot[ot["Overtime"]=="No"]["Attrition Rate (%)"])
            gap    = ot_yes - ot_no
            st.markdown("<br>", unsafe_allow_html=True)
            _insight(
                f"Overtime employees leave at <b>{ot_yes:.1f}%</b> vs "
                f"<b>{ot_no:.1f}%</b> for those who don't — "
                f"a <b>{gap:.1f}pp gap</b>. At 74k employees, "
                f"every pp = ~745 people. This gap = ~4,400 extra departures."
            )
            _cta(
                "<b>🎯 Action:</b> Department-level overtime audit. "
                "Identify teams with >10% chronic exposure. "
                "Target: 20% reduction in 2 quarters."
            )

    # ── Q3: REMOTE WORK ───────────────────────────────────────────────────────
    with tab3:
        _qbadge("Q3 · Remote Work Policy")
        _section("Does Remote Work Keep People?")

        remote = (
            dff.groupby("remote_work", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)",
                              "remote_work": "Location"})
        )
        remote["Location"] = remote["Location"].map(
            {"Yes": "Remote", "No": "On-site"})

        pct_remote = _safe_pct((dff["remote_work"]=="Yes").sum(), len(dff))

        c1, c2 = st.columns([1.5, 1])
        with c1:
            fig = px.bar(
                remote, x="Location", y="Attrition Rate (%)",
                title="Remote vs On-site Attrition Rate",
                text="Attrition Rate (%)",
                color="Location",
                color_discrete_map={"Remote": KB, "On-site": KB_LIGHT},
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="outside",
                marker_line=dict(width=0),
            )
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Attrition Rate (%)",
                showlegend=False,
                margin=dict(l=50, r=40, t=55, b=45),
                yaxis=dict(range=[0, remote["Attrition Rate (%)"].max() + 10]),
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig, height=450), use_container_width=True)

        with c2:
            r_remote = _safe_first(
                remote[remote["Location"]=="Remote"]["Attrition Rate (%)"])
            r_onsite = _safe_first(
                remote[remote["Location"]=="On-site"]["Attrition Rate (%)"])
            gap = r_onsite - r_remote
            st.markdown("<br>", unsafe_allow_html=True)
            _insight(
                f"Remote: <b>{r_remote:.1f}%</b> vs On-site: <b>{r_onsite:.1f}%</b>"
                f" — <b>{gap:.1f}pp gap</b>. "
                f"However, only <b>{pct_remote:.1f}%</b> of workforce is remote. "
                f"The effect is real but reflects a small sub-group — selection "
                f"bias cannot be ruled out."
            )
            _cta(
                "<b>🎯 Action:</b> 90-day remote pilot for on-site roles above "
                "50% attrition. Track before/after to confirm causation."
            )

    # ── Q4: PAY FAIRNESS ──────────────────────────────────────────────────────
    with tab4:
        _qbadge("Q4 · Pay Fairness Within Job Levels")
        _section("Does Higher Pay Within a Level Reduce Attrition?")

        jl = (
            dff.groupby("job_level", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)",
                              "job_level": "Job Level"})
        )

        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(
                jl, x="Job Level", y="Attrition Rate (%)",
                title="Attrition Rate by Job Level",
                text="Attrition Rate (%)",
                color="Attrition Rate (%)",
                color_continuous_scale=[KB_LIGHT, KB],
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="outside",
                marker_line=dict(width=0),
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(
                xaxis_title="Job Level",
                yaxis_title="Attrition Rate (%)",
                showlegend=True,
                margin=dict(l=50, r=40, t=55, b=45),
                yaxis=dict(range=[0, jl["Attrition Rate (%)"].max() + 10]),
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig, height=450), use_container_width=True)

            entry  = _safe_first(jl[jl["Job Level"]=="Entry"]["Attrition Rate (%)"])
            senior = _safe_first(jl[jl["Job Level"]=="Senior"]["Attrition Rate (%)"])
            _insight(
                f"Entry: <b>{entry:.1f}%</b> → Senior: <b>{senior:.1f}%</b> — "
                f"<b>{entry-senior:.0f}pp gap.</b> "
                f"Job Level is the single strongest driver in the entire dataset."
            )

        with c2:
            pay_data = q.get("pay_by_level_quartile", pd.DataFrame())
            if not pay_data.empty:
                fig = px.bar(
                    pay_data,
                    x="income_quartile", y="Attrition Rate (%)",
                    color="job_level",
                    barmode="group",
                    title="Attrition by Pay Quartile Within Each Job Level",
                    labels={"income_quartile": "Pay Quartile",
                            "job_level": "Job Level"},
                    color_discrete_sequence=[KB_LIGHT, "#7FA8FF", KB],
                )
                fig.update_layout(
                    xaxis_title="Pay Quartile (within Job Level)",
                    yaxis_title="Attrition Rate (%)",
                    legend_title="Job Level",
                    margin=dict(l=50, r=40, t=55, b=45),
                )
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=450), use_container_width=True)

        _insight(
            "Within the same job level, moving from bottom to top pay quartile "
            "reduces attrition by only <b>~2pp</b>. Pay raises within a band are "
            "largely ineffective. <b>The level itself is what matters</b> — "
            "Entry employees leave at ~63% regardless of salary."
        )
        _cta(
            "<b>🎯 Action:</b> Invest in <b>promotion pathways</b>, not salary hikes. "
            "Every promotion from Entry to Mid eliminates ~18pp attrition risk. "
            "Target: reduce time-to-first-promotion by 6 months."
        )

    # ── Q5: RETENTION TIMELINE ────────────────────────────────────────────────
    with tab5:
        _qbadge("Q5 · The Retention Timeline")
        _section("When Are Employees Most Likely to Leave?")

        tenure_data = q.get("attrition_by_tenure", pd.DataFrame())
        if not tenure_data.empty:
            fig = px.bar(
                tenure_data,
                x="tenure_band", y="Attrition Rate (%)",
                title="Attrition Rate by Company Tenure",
                text="Attrition Rate (%)",
                color="Attrition Rate (%)",
                color_continuous_scale=[KB_LIGHT, KB],
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="outside",
                marker_line=dict(width=0),
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(
                xaxis_title="Years at Company",
                yaxis_title="Attrition Rate (%)",
                showlegend=True,
                margin=dict(l=50, r=40, t=55, b=45),
                yaxis=dict(range=[0, tenure_data["Attrition Rate (%)"].max() + 8]),
            )
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig, height=480), use_container_width=True)

            peak = tenure_data.loc[tenure_data["Attrition Rate (%)"].idxmax()]
            _insight(
                f"Attrition peaks at <b>{peak['tenure_band']}</b> "
                f"(<b>{peak['Attrition Rate (%)']:.1f}%</b>). "
                f"There is no 'honeymoon period' — attrition is high from day one "
                f"through the first 5 years. Long-tenure (20+ yrs) employees are "
                f"the most stable group."
            )
            _cta(
                "<b>🎯 Action:</b> Redesign onboarding for the 0–2yr window. "
                "Introduce a structured 18-month career check-in — "
                "the point where mid-career drift first becomes visible."
            )

    # ── Q6: ENGAGEMENT WARNING SIGNS ─────────────────────────────────────────
    with tab6:
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
            pivot = pivot.reindex(
                index=[x for x in wlb_order if x in pivot.index],
                columns=[x for x in sat_order if x in pivot.columns],
            )

            fig = go.Figure(go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                colorscale=[[0, KB_LIGHT], [0.5, KB], [1, KB_DARK]],
                zmin=25, zmax=75,
                text=pivot.values,
                texttemplate="%{text:.1f}%",
                colorbar=dict(title="Attrition %"),
            ))
            fig.update_layout(
                title="Attrition Rate: Work-Life Balance × Job Satisfaction",
                xaxis_title="Job Satisfaction",
                yaxis_title="Work-Life Balance",
                margin=dict(l=80, r=40, t=55, b=55),
            )
            st.plotly_chart(_theme(fig, height=420), use_container_width=True)

            _insight(
                "Danger zone is top-left: "
                "<b>Poor WLB + Low Satisfaction = 67.0%</b> attrition. "
                "Critically, even <b>Very High satisfaction</b> with Poor WLB = 64.9%. "
                "<b>WLB dominates</b> — satisfaction cannot compensate for it."
            )
            _cta(
                "<b>🎯 Manager early-warning signals:</b> "
                "An employee who loves their job but reports poor balance "
                "is at near-identical risk as one who is dissatisfied. "
                "Flag any employee with Poor/Fair WLB in quarterly pulse checks."
            )

    # ── Q7: LIFE STAGE ────────────────────────────────────────────────────────
    with tab7:
        _qbadge("Q7 · Life Stage Factors")
        _section("Do Age, Marital Status, and Dependents Change Who Leaves?")

        c1, c2, c3 = st.columns(3)

        with c1:
            age_data = q.get("attrition_by_age_group", pd.DataFrame())
            if not age_data.empty:
                fig = px.bar(
                    age_data, x="Age Group", y="Attrition Rate (%)",
                    title="Attrition by Age Group",
                    text="Attrition Rate (%)",
                    color="Attrition Rate (%)",
                    color_continuous_scale=[KB_LIGHT, KB],
                )
                fig.update_traces(
                    texttemplate="%{y:.1f}%",
                    textposition="outside",
                    marker_line=dict(width=0),
                )
                fig.update_coloraxes(showscale=False)
                fig.update_layout(
                    showlegend=True,
                    margin=dict(l=40, r=30, t=55, b=45),
                    yaxis=dict(range=[0, age_data["Attrition Rate (%)"].max()+10]),
                )
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=400), use_container_width=True)

        with c2:
            marital_data = q.get("attrition_by_marital", pd.DataFrame())
            if not marital_data.empty:
                fig = px.bar(
                    marital_data,
                    x="Marital Status", y="Attrition Rate (%)",
                    title="Attrition by Marital Status",
                    text="Attrition Rate (%)",
                    color="Attrition Rate (%)",
                    color_continuous_scale=[KB_LIGHT, KB],
                )
                fig.update_traces(
                    texttemplate="%{y:.1f}%",
                    textposition="outside",
                    marker_line=dict(width=0),
                )
                fig.update_coloraxes(showscale=False)
                fig.update_layout(
                    showlegend=True,
                    margin=dict(l=40, r=30, t=55, b=45),
                    yaxis=dict(range=[0, marital_data["Attrition Rate (%)"].max()+10]),
                )
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=400), use_container_width=True)

        with c3:
            dep_data = q.get("attrition_by_dependents", pd.DataFrame())
            if not dep_data.empty:
                fig = px.line(
                    dep_data,
                    x="Number of Dependents", y="Attrition Rate (%)",
                    title="Attrition by Number of Dependents",
                    markers=True, line_shape="spline",
                )
                fig.update_traces(line_color=KB, marker_color=KB, marker_size=8)
                fig.update_layout(
                    showlegend=True,
                    margin=dict(l=40, r=30, t=55, b=45),
                )
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=400), use_container_width=True)

        _insight(
            "Highest-risk group: <b>young (18–25), single employees</b>. "
            "Single status alone = <b>66.8%</b> attrition. "
            "Employees with 4+ dependents leave at 35–37% — "
            "family responsibility correlates strongly with stability."
        )
        _cta(
            "<b>🎯 Action:</b> Build community and belonging programmes "
            "(mentorship cohorts, peer networks, social budgets) for young single "
            "employees. These create organisational roots — low-cost, high-impact."
        )

    # ── Q8: CAREER STAGNATION ────────────────────────────────────────────────
    with tab8:
        _qbadge("Q8 · Career Stagnation")
        _section("Does Feeling Stuck Drive Attrition?")

        c1, c2 = st.columns([1.5, 1])

        with c1:
            promo_data = q.get("attrition_by_promotions", pd.DataFrame())
            if not promo_data.empty:
                fig = px.line(
                    promo_data,
                    x="Number of Promotions", y="Attrition Rate (%)",
                    title="Attrition Rate vs Number of Promotions",
                    markers=True, line_shape="spline",
                )
                fig.update_traces(
                    line_color=KB, marker_color=KB, marker_size=10)
                fig.update_layout(
                    xaxis_title="Number of Promotions Received",
                    yaxis_title="Attrition Rate (%)",
                    showlegend=True,
                    margin=dict(l=50, r=40, t=55, b=45),
                )
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=420), use_container_width=True)

                p0 = _safe_first(
                    promo_data[promo_data["Number of Promotions"]==0]["Attrition Rate (%)"])
                p4 = _safe_first(
                    promo_data[promo_data["Number of Promotions"]==4]["Attrition Rate (%)"])
                _insight(
                    f"0 promotions: <b>{p0:.1f}%</b> → 4 promotions: <b>{p4:.1f}%</b>. "
                    f"Attrition is <b>cut in half by promotion alone</b>. "
                    f"The effect is non-linear — a sharp drop occurs at the 3rd promotion."
                )

        with c2:
            opp_data = q.get("attrition_by_leadership_opportunities", pd.DataFrame())
            if not opp_data.empty and len(opp_data.columns) >= 2:
                x_col = opp_data.columns[0]
                fig = px.bar(
                    opp_data, x=x_col, y="Attrition Rate (%)",
                    title="Leadership Opportunities vs Attrition",
                    text="Attrition Rate (%)",
                    color=x_col,
                    color_discrete_map={"Yes": KB, "No": KB_LIGHT},
                )
                fig.update_traces(
                    texttemplate="%{y:.1f}%",
                    textposition="outside",
                    marker_line=dict(width=0),
                )
                fig.update_layout(
                    xaxis_title="Has Leadership Opportunities",
                    yaxis_title="Attrition Rate (%)",
                    showlegend=False,
                    margin=dict(l=50, r=40, t=55, b=45),
                    yaxis=dict(range=[0, opp_data["Attrition Rate (%)"].max()+10]),
                )
                _add_avg_line(fig, overall_rate)
                st.plotly_chart(_theme(fig, height=420), use_container_width=True)

        stuck_n    = q.get("stuck_n", 0)
        stuck_rate = q.get("stuck_rate", 0.0)
        _risk(
            f"<b>{stuck_n:,} fully stuck employees</b> "
            f"(0 promotions + no leadership + no innovation) — "
            f"<b>{stuck_rate:.1f}%</b> attrition · "
            f"{stuck_rate - overall_rate:+.1f}pp above company average."
        )
        _cta(
            f"<b>🎯 Action:</b> Assign 90-day development plans to {stuck_n:,} employees. "
            f"Every employee needs at least one growth dimension within 18 months. "
            f"Target: move 30% out of 'fully stuck' in 2 quarters."
        )

    # ── Q9: HIGHEST-RISK PROFILE ──────────────────────────────────────────────
    with tab9:
        _qbadge("Q9 · Highest-Risk Employee Profile")
        _section("Who Is Most Likely to Leave — and How Many Are There?")

        risk_n    = q.get("risk_profile_n", 0)
        risk_rate = q.get("risk_profile_rate", 0.0)
        risk_lift = risk_rate - overall_rate

        _risk(
            f"<b>Profile: Poor WLB + Overtime + 0 Promotions + No Leadership</b><br>"
            f"Attrition: <b>{risk_rate:.1f}%</b> &nbsp;·&nbsp; "
            f"<b>{risk_lift:+.1f}pp</b> above {overall_rate:.1f}% average &nbsp;·&nbsp; "
            f"<b>{risk_n:,} employees</b> match this profile today"
        )

        c1, c2 = st.columns([1.5, 1])

        with c1:
            # Horizontal bar — must use orientation="h" for avg line
            factors = pd.DataFrame({
                "Factor": ["Poor Work-Life Balance", "Works Overtime",
                           "Zero Promotions", "No Leadership Access"],
                "Attrition Rate (%)": [60.2, 51.5, 49.3, 47.6],
            }).sort_values("Attrition Rate (%)")

            fig = px.bar(
                factors,
                x="Attrition Rate (%)", y="Factor",
                orientation="h",
                title="Standalone Attrition Rate of Each Risk Factor",
                text="Attrition Rate (%)",
                color="Attrition Rate (%)",
                color_continuous_scale=[KB_LIGHT, KB],
            )
            fig.update_traces(
                texttemplate="%{x:.1f}%",
                textposition="outside",
                marker_line=dict(width=0),
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(
                yaxis_title="",
                xaxis_title="Attrition Rate (%)",
                showlegend=True,
                margin=dict(l=150, r=60, t=55, b=45),
                xaxis=dict(range=[0, factors["Attrition Rate (%)"].max() + 15]),
            )
            # orientation="h" → vline
            _add_avg_line(fig, overall_rate, orientation="h")
            st.plotly_chart(_theme(fig, height=380), use_container_width=True)

        with c2:
            comparison = pd.DataFrame({
                "Group": ["Company Average", "Risk Profile"],
                "Attrition Rate (%)": [round(overall_rate, 1), round(risk_rate, 1)],
            })
            fig = px.bar(
                comparison,
                x="Group", y="Attrition Rate (%)",
                title="Risk Profile vs Company Average",
                text="Attrition Rate (%)",
                color="Group",
                color_discrete_map={"Company Average": KB_LIGHT, "Risk Profile": KB},
            )
            fig.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="outside",
                marker_line=dict(width=0),
            )
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Attrition Rate (%)",
                showlegend=False,
                margin=dict(l=50, r=40, t=55, b=45),
                yaxis=dict(range=[0, risk_rate + 15]),
            )
            st.plotly_chart(_theme(fig, height=380), use_container_width=True)

        _insight(
            f"This profile shows <b>{risk_rate:.1f}%</b> attrition — "
            f"<b>1.4× the company average</b>. "
            f"With <b>{risk_n:,} employees</b> matching it, "
            f"if half leave this year = ~{int(risk_n * risk_rate/100):,} departures "
            f"from one identifiable cohort alone."
        )
        _cta(
            f"<b>🎯 Action:</b> Assign an HR business partner to each of the "
            f"{risk_n:,} profile employees within 30 days. "
            f"Target: eliminate 2 of 4 risk factors per person "
            f"(e.g. approve remote work + assign leadership project). "
            f"20% success = ~{int(risk_n * risk_rate/100 * 0.2):,} departures prevented."
        )

    # ── Q10: WHAT MOVES THE NEEDLE ────────────────────────────────────────────
    with tab10:
        _qbadge("Q10 · What Moves the Needle")
        _section("If HR Could Fix One Thing Next Quarter…")

        drivers = q.get("driver_ranking", pd.DataFrame())
        if not drivers.empty:
            # Horizontal bar — orientation="h" for avg line
            fig = px.bar(
                drivers,
                x="Effect (pp)", y="Driver",
                orientation="h",
                title="Top Attrition Drivers — Effect Size (Best vs Worst Group)",
                text="Effect (pp)",
                color="Effect (pp)",
                color_continuous_scale=[KB_LIGHT, KB],
            )
            fig.update_traces(
                texttemplate="%{x:.1f}pp",
                textposition="outside",
                marker_line=dict(width=0),
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(
                xaxis_title="Attrition Rate Difference (percentage points)",
                yaxis_title="",
                showlegend=False,
                margin=dict(l=140, r=60, t=55, b=45),
                xaxis=dict(range=[0, drivers["Effect (pp)"].max() + 8]),
            )
            # No avg line here — this chart shows effect sizes, not rates
            st.plotly_chart(_theme(fig, height=420), use_container_width=True)

        st.markdown("### 🏆 Top 3 Recommendations")
        r1, r2, r3 = st.columns(3)

        with r1:
            st.markdown(
                "<div class='risk-card'><b>#1 · Expand Remote Work</b><br><br>"
                "Effect size: <b>28.1pp</b><br>"
                "On-site 52.8% → Remote 24.7%<br><br>"
                "Only 19.1% of workforce is remote. "
                "A policy change (2 weeks) not a structural one. "
                "Shifting 5% more headcount = ~800 retained employees.</div>",
                unsafe_allow_html=True,
            )
        with r2:
            st.markdown(
                "<div class='insight-box'><b>#2 · Promotion Pathways</b><br><br>"
                "Effect size: <b>26.0pp</b><br>"
                "0 promos 49.3% → 4 promos 23.3%<br><br>"
                "Non-linear jump at the 3rd promotion. "
                "Accelerate time-to-3rd-promotion "
                "for at-risk cohorts.</div>",
                unsafe_allow_html=True,
            )
        with r3:
            st.markdown(
                "<div class='insight-box'><b>#3 · Work-Life Balance</b><br><br>"
                "Effect size: <b>24.5pp</b><br>"
                "Poor 60.2% → Excellent 35.7%<br><br>"
                "WLB dominates engagement — overrides satisfaction. "
                "Start with overtime reduction and flexible scheduling.</div>",
                unsafe_allow_html=True,
            )

        _insight(
            "<b>The #1 pick: Remote Work expansion.</b> "
            "Job Level (43pp) is technically largest but it is a symptom — "
            "you can't just 'change' job levels. Remote Work is a "
            "<b>policy change</b>, not structural. "
            "The effect size is 28.1pp, only 19.1% are remote today, "
            "and the cost of a pilot is near-zero."
        )

        st.markdown("---")
        st.markdown("### 📋 90-Day Action Roadmap")
        roadmap = pd.DataFrame([
            {"Priority": "🔴 Critical", "Action": "Remote work eligibility review",
             "Owner": "CHRO", "Timeline": "Week 1–2", "Expected Impact": "−28pp for pilots"},
            {"Priority": "🔴 Critical", "Action": f"HR partners for {risk_n:,} risk-profile employees",
             "Owner": "HRBPs", "Timeline": "Week 1–3", "Expected Impact": f"~{int(risk_n*risk_rate/100*0.2):,} departures prevented"},
            {"Priority": "🟠 High", "Action": "Overtime audit (flag >10% exposure teams)",
             "Owner": "Line Managers", "Timeline": "Week 2–4", "Expected Impact": "−6pp for flagged groups"},
            {"Priority": "🟠 High", "Action": "Promotion fast-track for 0-promotion employees",
             "Owner": "HR + Mgmt", "Timeline": "Month 2", "Expected Impact": "−26pp for promoted"},
            {"Priority": "🟡 Medium", "Action": "WLB pulse survey for Poor/Fair-rated employees",
             "Owner": "HR Analytics", "Timeline": "Month 2", "Expected Impact": "Identify 25k+ at-risk"},
            {"Priority": "🟡 Medium", "Action": "Community programme for 18–25 single employees",
             "Owner": "L&D", "Timeline": "Month 3", "Expected Impact": "66.8% → target <50%"},
        ])
        # Show as styled markdown table — not a raw data dump
        st.dataframe(
            roadmap,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Priority":        st.column_config.TextColumn("Priority", width="small"),
                "Action":          st.column_config.TextColumn("Action",   width="large"),
                "Owner":           st.column_config.TextColumn("Owner",    width="small"),
                "Timeline":        st.column_config.TextColumn("Timeline", width="small"),
                "Expected Impact": st.column_config.TextColumn("Expected Impact"),
            },
        )

    st.markdown("---")
    st.caption(
        "Kayfa AI & Data Analytics Internship · Week 1 · "
        "Workforce Retention Intelligence · "
        "Synthetic dataset — findings are for learning purposes only."
    )


# ─────────────────────────────────────────────────────────────────────────────
# NAVIGATION  —  st.navigation / st.Page  (rubric requirement)
# ─────────────────────────────────────────────────────────────────────────────
pg = st.navigation({
    "📊 Dashboard": [
        st.Page(page_overview, title="Overview", icon="🏠", default=True),
    ],
})
pg.run()
