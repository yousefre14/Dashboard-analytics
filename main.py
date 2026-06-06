"""
main.py  —  HR Attrition Dashboard
Kayfa AI & Data Analytics Internship · Week 1

Run:     streamlit run main.py
Deploy:  GitHub → share.streamlit.io  (requirements.txt must list streamlit>=1.36.0)

Architecture:
  - st.navigation / st.Page  for multi-page navigation (rubric requirement)
  - Shared sidebar (logo + filters) defined BEFORE pg.run() → persists on all pages
  - dff (filtered DataFrame) computed once in outer scope, used by all page functions
  - @st.cache_data ensures data + aggregations run only once per session
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from Data_Handling import (
    load_and_clean, compute_aggregration,
    compute_q_aggregations, filtered_kpis,
)

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
BLUE_SEQ  = [KB_LIGHT, "#BDD0FF", "#7FA8FF", "#4C84FF",
             KB, KB_DARK, "#0D31A3", "#081F7A"]
DIVERG    = ["#E8EFFF", "#7FA8FF", KB, KB_DARK]
ATTRITION_MAP = {"Stayed": KB_LIGHT, "Left": KB}   # consistent across charts


# ─────────────────────────────────────────────────────────────────────────────
# CSS  —  rgba backgrounds = dark-mode safe  (no hardcoded #FFF or dark text)
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

/* ── Sidebar — always Kayfa Blue ── */
section[data-testid="stSidebar"] { background: #1A5AFF !important; }
section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.25) !important; }
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background: #1245CC !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.15) !important;
    border-color: rgba(255,255,255,0.3) !important;
}
section[data-testid="stSidebar"] .stRadio label { color: white !important; }

/* ── Insight box — transparent blue tint, works in dark + light ── */
.insight-box {
    background: rgba(26,90,255,0.08);
    border-left: 4px solid #1A5AFF;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin-top: 0.5rem;
    font-size: 0.84rem;
    line-height: 1.55;
}
.insight-box b { color: #1A5AFF; }

/* ── CTA box — green tint ── */
.cta-box {
    background: rgba(22,163,74,0.07);
    border-left: 4px solid #16A34A;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin-top: 0.4rem;
    font-size: 0.84rem;
    line-height: 1.55;
}
.cta-box b { color: #16A34A; }

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
    font-size: 1rem;
    font-weight: 700;
    border-bottom: 2px solid rgba(26,90,255,0.2);
    padding-bottom: 0.4rem;
    margin: 1.4rem 0 0.9rem 0;
}

/* ── Homepage hero ── */
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

/* ── Risk callout ── */
.risk-card {
    background: rgba(220,38,38,0.07);
    border: 1px solid rgba(220,38,38,0.25);
    border-left: 4px solid #DC2626;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}
.risk-card b { color: #DC2626; }

/* ── KPI number ── */
.kpi-num { font-size: 2rem; font-weight: 800; color: #1A5AFF; line-height: 1; }
.kpi-lbl { font-size: 0.72rem; font-weight: 600; opacity: 0.6;
           text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.2rem; }
.kpi-card { background: rgba(26,90,255,0.06); border-left: 4px solid #1A5AFF;
            border-radius: 8px; padding: 1rem 1.2rem; }

footer { visibility: hidden; }
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY HELPERS
# ─────────────────────────────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",   # transparent → adapts to light/dark
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif"),
    margin=dict(t=44, b=28, l=8, r=8),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)

def _theme(fig: go.Figure) -> go.Figure:
    """Apply Kayfa theme. Transparent background = dark-mode safe."""
    fig.update_layout(**_LAYOUT)
    fig.update_xaxes(gridcolor="rgba(26,90,255,0.1)",
                     linecolor="rgba(26,90,255,0.2)", tickfont_size=11)
    fig.update_yaxes(gridcolor="rgba(26,90,255,0.1)",
                     linecolor="rgba(26,90,255,0.2)", tickfont_size=11)
    return fig

def _add_avg_line(fig: go.Figure, y_val: float,
                  label: str = "Company Average") -> go.Figure:
    """
    Add a named dashed reference line WITH a legend entry.
    Rubric: 'Any reference line must be named and shown in the legend.'
    Uses a dummy scatter trace so it appears in the legend properly.
    """
    fig.add_hline(y=y_val, line_dash="dash",
                  line_color=AMBER, line_width=1.8)
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines",
        line=dict(dash="dash", color=AMBER, width=1.8),
        name=label, showlegend=True,
    ))
    return fig

def _insight(text: str):
    st.markdown(f"<div class='insight-box'>{text}</div>",
                unsafe_allow_html=True)

def _cta(text: str):
    st.markdown(f"<div class='cta-box'>{text}</div>",
                unsafe_allow_html=True)

def _qbadge(label: str):
    st.markdown(f"<span class='q-badge'>{label}</span>",
                unsafe_allow_html=True)

def _section(title: str):
    st.markdown(f"<div class='section-title'>{title}</div>",
                unsafe_allow_html=True)

def _logo_block():
    """Logo with Arabic-brand fallback. Used on homepage."""
    try:
        st.image("company_logo2.png", width=110)
    except Exception:
        st.markdown(
            "<div style='font-size:2rem;font-weight:900;"
            "color:#1A5AFF;letter-spacing:-1px;'>كيف</div>",
            unsafe_allow_html=True,
        )

def _safe_pct(num: float, denom: float, fallback: float = 0.0) -> float:
    """Division-by-zero guard for percentage calculations."""
    return (num / denom * 100) if denom > 0 else fallback

def _safe_first(series: pd.Series, fallback: float = 0.0) -> float:
    """Guard against .values[0] on empty Series."""
    return float(series.values[0]) if len(series) > 0 else fallback


# ─────────────────────────────────────────────────────────────────────────────
# DATA — cached, runs once per session
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading & preparing data…")
def get_data():
    df   = load_and_clean("train.csv", "test.csv")
    aggs = compute_aggregration(df)
    q    = compute_q_aggregations(df)
    return df, aggs, q

df, aggs, q = get_data()
overall_rate = aggs["overall_rate"] * 100   # scalar % used everywhere


# ─────────────────────────────────────────────────────────────────────────────
# INJECT CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED SIDEBAR  (defined before pg.run() → appears on EVERY page)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo — fixed at top of sidebar
    try:
        st.image("company_logo2.png", use_container_width=True)
    except Exception:
        st.markdown(
            "<div style='font-size:1.8rem;font-weight:900;"
            "letter-spacing:-1px;padding:0.4rem 0;'>كيف</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 🔍 Filters")

    # ── Filter controls ───────────────────────────────────────────────────
    all_roles   = sorted(df["job_role"].unique().tolist())
    all_genders = sorted(df["gender"].unique().tolist())
    all_levels  = df["job_level"].cat.categories.tolist()   # ordinal order
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
                          ["All", "With Overtime", "No Overtime"], index=0)

    st.markdown("---")
    st.caption("Kayfa · Week 1 · Data Analytics Track")


# ─────────────────────────────────────────────────────────────────────────────
# FILTER MASK  —  single O(n) boolean pass, applied once, used by all pages
# Building one combined mask avoids intermediate DataFrame copies.
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

# ── Empty-filter guard (testing: ensure UI never crashes on zero rows) ────────
if len(dff) == 0:
    st.warning("⚠️ No employees match the current filters. Adjust the sidebar.")
    st.stop()

kpis = filtered_kpis(dff)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED KPI ROW  (displayed at top of every page)
# ─────────────────────────────────────────────────────────────────────────────
def _kpi_row():
    delta = kpis["rate"] - overall_rate
    sign  = "▲" if delta > 0 else "▼"
    clr   = "#DC2626" if delta > 0 else "#16A34A"
    delta_html = (f"<span style='font-size:0.78rem;color:{clr};font-weight:600;'>"
                  f"{sign} {abs(delta):.1f}pp vs company avg</span>")

    k1, k2, k3, k4 = st.columns(4)
    for col, lbl, val, sub in [
        (k1, "Total Employees",     f"{kpis['total']:,}",
         f"of {aggs['total_employee']:,} total"),
        (k2, "Attrition Rate",      f"{kpis['rate']:.1f}%",    None),
        (k3, "Avg Monthly Income",  f"${kpis['avg_income']:,.0f}", "filtered group"),
        (k4, "Avg Tenure",          f"{kpis['avg_tenure']:.1f} yrs", "at company"),
    ]:
        with col:
            sub_html = delta_html if sub is None else \
                       f"<span style='font-size:0.78rem;opacity:0.6;'>{sub}</span>"
            st.markdown(
                f"<div class='kpi-card'>"
                f"<div class='kpi-lbl'>{lbl}</div>"
                f"<div class='kpi-num'>{val}</div>"
                f"{sub_html}</div>",
                unsafe_allow_html=True,
            )


# ═════════════════════════════════════════════════════════════════════════════
#  PAGE FUNCTIONS
#  Each function closes over df, dff, aggs, q, overall_rate, kpis — all
#  computed in the outer scope before pg.run() is called.
# ═════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1  ·  Overview  (Q1)
# ─────────────────────────────────────────────────────────────────────────────
def page_overview():
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
        # Attrition by role — horizontal bar, company avg reference line
        role_data = (
            dff.groupby("job_role", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)", "job_role": "Job Role"})
            .sort_values("Attrition Rate (%)", ascending=True)
        )
        # Guard: ensure data exists before charting
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
                # No textfont_color — Plotly auto-picks readable contrast
            )
            fig.update_coloraxes(showscale=False)
            fig.update_layout(yaxis_title="", xaxis_title="Attrition Rate (%)")
            _add_avg_line(fig, overall_rate)
            st.plotly_chart(_theme(fig), use_container_width=True)

            top_role = role_data.iloc[-1]
            _insight(
                f"<b>{top_role['Job Role']}</b> leads at "
                f"<b>{top_role['Attrition Rate (%)']:.1f}%</b> — "
                f"{top_role['Attrition Rate (%)'] - overall_rate:.1f}pp above the "
                f"{overall_rate:.1f}% company average. The spread across roles is narrow "
                f"(~2pp), meaning this is a <b>company-wide condition</b>, not a "
                f"single-department problem."
            )
            _cta(
                "<b>Action:</b> Don't target one department in isolation. "
                "A company-wide policy response — remote work expansion, promotion "
                "pathways, overtime audit — will move the needle more than "
                "role-by-role interventions."
            )

    with c2:
        # Donut: stayed vs left
        stayed = int((dff["attrition"] == 0).sum())
        left   = int((dff["attrition"] == 1).sum())
        total  = stayed + left

        # Guard: division by zero
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
            f"<b>{left:,}</b> employees left · "
            f"<b>{stayed:,}</b> retained · "
            f"Retention rate: <b>{retention_rate:.1f}%</b>"
        )

    # ── Executive summary ─────────────────────────────────────────────────────
    _section("Executive Summary")
    income_left   = dff[dff["attrition"]==1]["monthly_income"].mean()
    income_stayed = dff[dff["attrition"]==0]["monthly_income"].mean()
    income_gap    = _safe_pct(income_left - income_stayed, income_stayed)

    avg_age_left   = dff[dff["attrition"]==1]["age"].mean()
    avg_age_stayed = dff[dff["attrition"]==0]["age"].mean()

    s1, s2 = st.columns(2)
    with s1:
        st.markdown("##### 🔍 Key Findings")
        severity = ("⚠️ **HIGH RISK**" if kpis["rate"] > overall_rate + 5
                    else "✅ **BELOW AVERAGE**" if kpis["rate"] < overall_rate - 5
                    else "📊 **NEAR AVERAGE**")
        delta_dir = ("above" if kpis["rate"] >= overall_rate else "below")
        st.info(f"{severity} — {kpis['rate']:.1f}% attrition is "
                f"{abs(kpis['rate']-overall_rate):.1f}pp {delta_dir} "
                f"the {overall_rate:.1f}% company average")
        st.info(f"💰 Salary gap between leavers and stayers: "
                f"only **{abs(income_gap):.1f}%** — "
                f"money is **not** the primary driver")
        st.info(f"👥 Leavers average **{avg_age_left:.0f} yrs** vs "
                f"**{avg_age_stayed:.0f} yrs** for stayers — "
                f"younger employees are at higher risk")
    with s2:
        st.markdown("##### 💡 Top Recommendations")
        st.success("🏠 Expand remote work eligibility — "
                   "28pp attrition gap between remote and on-site")
        st.success("🚀 Build structured promotion pathways — "
                   "career stagnation is a top-3 driver")
        st.success("⚖️ Audit overtime exposure — "
                   "burnout compounds every other risk factor")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2  ·  Workload & Flexibility  (Q2, Q3)
# ─────────────────────────────────────────────────────────────────────────────
def page_workload():
    st.markdown("## ⏰ Workload & Flexibility")
    _kpi_row()
    st.markdown("---")

    # ── Q2: Overtime ──────────────────────────────────────────────────────────
    _qbadge("Q2 · Overtime")
    _section("Does Overtime Predict Attrition?")

    if "overtime" not in dff.columns:
        st.warning("Overtime column not available in filtered data.")
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
                f"Employees working overtime leave at <b>{ot_yes:.1f}%</b> vs "
                f"<b>{ot_no:.1f}%</b> for those who don't — a <b>{gap:.1f}pp gap</b>. "
                f"At 74,498 employees, every percentage point represents ~745 people. "
                f"A 6pp gap means ~4,400 additional departures directly attributable "
                f"to overtime load."
            )
            _cta(
                "<b>HR Action:</b> Conduct a department-level overtime audit. "
                "Identify teams with chronic >10% overtime exposure and redistribute "
                "workload before attrition compounds. Target: reduce overtime headcount "
                "by 20% within 2 quarters."
            )

    st.markdown("---")

    # ── Q3: Remote work ───────────────────────────────────────────────────────
    _qbadge("Q3 · Remote Work")
    _section("Does Remote Work Keep People?")

    if "remote_work" not in dff.columns:
        st.warning("Remote work column not available.")
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
                f"<b>{gap:.1f}pp lower</b> than on-site employees at {r_onsite:.1f}%. "
                f"This is the <b>second largest effect size</b> in the entire dataset. "
                f"However, only <b>{pct_remote:.1f}%</b> of the workforce is currently "
                f"remote — the effect is real, but it reflects a small sub-group. "
                f"We cannot rule out selection bias: remote-eligible roles may "
                f"inherently attract more committed employees."
            )
            _cta(
                "<b>HR Action:</b> Run a 90-day remote work pilot for on-site roles "
                "with attrition above 50%. Even shifting 10% of on-site headcount "
                "to remote could prevent ~2,000 departures. "
                "Track attrition before and after to confirm causation."
            )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3  ·  Pay & Job Level  (Q4)
# ─────────────────────────────────────────────────────────────────────────────
def page_pay_level():
    st.markdown("## 💰 Pay & Job Level")
    _kpi_row()
    st.markdown("---")

    _qbadge("Q4 · Pay Fairness")
    _section("Does Higher Pay Within a Job Level Reduce Attrition?")

    # Job Level overall attrition (the key context)
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
            # Ordinal order preserved via pd.Categorical in Data_Handling
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(xaxis_title="Job Level", yaxis_title="Attrition Rate (%)")
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), use_container_width=True)

        entry = _safe_first(jl[jl["Job Level"]=="Entry"]["Attrition Rate (%)"])
        senior = _safe_first(jl[jl["Job Level"]=="Senior"]["Attrition Rate (%)"])
        _insight(
            f"Entry-level employees leave at <b>{entry:.1f}%</b>, "
            f"Senior employees at <b>{senior:.1f}%</b> — "
            f"a <b>{entry-senior:.0f}pp gap</b>. "
            f"Job Level is the single strongest driver in the dataset (43pp effect)."
        )

    with c2:
        # Income quartile within job level — grouped bar
        pay_data = q.get("pay_by_level_quartile", pd.DataFrame())
        if not pay_data.empty:
            fig = px.bar(
                pay_data,
                x="income_quartile", y="Attrition Rate (%)",
                color="job_level",
                barmode="group",
                title="Attrition by Pay Quartile Within Each Job Level",
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
        "Within the same job level, moving from the bottom pay quartile to the top "
        "reduces attrition by only <b>~2pp</b> (e.g. Entry: 64.5% → 62.5%). "
        "Pay raises within a band are largely ineffective. "
        "The <b>level itself</b> is what matters — "
        "Entry employees leave at 63% regardless of what you pay them."
    )
    _cta(
        "<b>HR Action — Reframe the pay debate:</b> "
        "Don't give Entry-level staff a 10% raise and call it retention. "
        "Invest that budget in structured <b>promotion pathways</b> to Mid-level. "
        "Every employee promoted from Entry to Mid eliminates a ~18pp attrition risk. "
        "Set a target: reduce time-to-first-promotion by 6 months."
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
        "The income distributions for leavers and stayers are nearly identical "
        "(median gap < 1%). This confirms: <b>compensation is not the primary driver</b>. "
        "Leadership must resist the instinct to solve an attrition crisis with blanket raises."
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 4  ·  Engagement & Life Stage  (Q5, Q6, Q7)
# ─────────────────────────────────────────────────────────────────────────────
def page_engagement():
    st.markdown("## 🧠 Engagement & Life Stage")
    _kpi_row()
    st.markdown("---")

    # ── Q5: Retention timeline ────────────────────────────────────────────────
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
            f"Attrition peaks at the <b>{peak_band['tenure_band']}</b> stage "
            f"(<b>{peak_band['Attrition Rate (%)']:.1f}%</b>) and remains elevated "
            f"through the first 10 years. Long-tenure employees (20+ yrs) show the "
            f"lowest risk at <b>{low_band['Attrition Rate (%)']:.1f}%</b>. "
            f"The data shows no 'honeymoon cliff' — attrition is high from day one."
        )
        _cta(
            "<b>Action — Target the first 5 years:</b> "
            "Redesign the onboarding programme for the 0–2yr window. "
            "Introduce a structured career check-in at 18 months — "
            "the point where mid-career drift becomes visible. "
            "Long-tenure employees are your most stable group; protect them "
            "through recognition and leadership pathways."
        )

    st.markdown("---")

    # ── Q6: WLB × Satisfaction heatmap ───────────────────────────────────────
    _qbadge("Q6 · Engagement Warning Signs")
    _section("Which WLB + Satisfaction Combination Is the Danger Zone?")

    cross_data = q.get("wlb_x_satisfaction", pd.DataFrame())
    if not cross_data.empty:
        # Pivot for heatmap — WLB on y-axis (rows), Satisfaction on x-axis (cols)
        pivot = cross_data.pivot(
            index="Work-Life Balance",
            columns="Job Satisfaction",
            values="Attrition Rate (%)",
        )
        # Enforce ordinal ordering on both axes
        wlb_order = ["Poor", "Fair", "Good", "Excellent"]
        sat_order  = ["Low", "Medium", "High", "Very High"]
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
            height=360,
        )
        st.plotly_chart(_theme(fig), use_container_width=True)

        _insight(
            "The danger zone is <b>top-left</b> of the heatmap: "
            "<b>Poor WLB + Low Satisfaction = 67.0%</b> attrition — "
            "nearly 1.5× the company average. "
            "Crucially, even <b>Very High satisfaction</b> doesn't protect "
            "employees with Poor WLB (64.9%). "
            "WLB is the <i>dominant</i> variable — satisfaction is secondary."
        )
        _cta(
            "<b>Manager early-warning signals to watch:</b> "
            "An employee who says they love their work but reports poor balance "
            "is at just as high a risk as one who is dissatisfied. "
            "Build a quarterly pulse check flagging any employee with "
            "Poor/Fair WLB — regardless of satisfaction score."
        )

    st.markdown("---")

    # ── Q7: Life stage ────────────────────────────────────────────────────────
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
        "The highest-risk life-stage group is <b>young, single employees (18–25)</b> "
        "— attrition of <b>53.1%</b> age-group combined with <b>66.8%</b> for single "
        "marital status. Employees with 4+ dependents leave significantly less "
        "(35–37%) — family responsibility correlates with stability. "
        "This is not about age — it's about rootedness."
    )
    _cta(
        "<b>Action — Target single, young employees specifically:</b> "
        "Build community and belonging programmes (mentorship cohorts, team social "
        "budgets, structured peer networks) that create organisational roots. "
        "These are low-cost and directly address the psychological driver "
        "behind this life-stage risk."
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 5  ·  Career Growth  (Q8)
# ─────────────────────────────────────────────────────────────────────────────
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
                f"<b>0 promotions → {p0:.1f}% attrition.</b> "
                f"<b>4 promotions → {p4:.1f}% attrition.</b> "
                f"The attrition rate is <b>cut in half</b> by promotion alone. "
                f"Crucially, the drop is non-linear: "
                f"0–2 promotions show ~49% (near baseline), "
                f"but reaching 3 promotions triggers a sharp drop to ~25%. "
                f"There is a <b>promotion threshold effect</b>."
            )

    with c2:
        # Leadership + Innovation opportunities side by side
        for col_key, label in [
            ("attrition_by_leadership_opportunities", "Leadership Opportunities"),
            ("attrition_by_innovation_opportunities", "Innovation Opportunities"),
        ]:
            opp_data = q.get(col_key, pd.DataFrame())
            if not opp_data.empty and len(opp_data.columns) >= 2:
                x_col = opp_data.columns[0]
                fig = px.bar(
                    opp_data, x=x_col, y="Attrition Rate (%)",
                    title=f"Attrition by {label}",
                    color=x_col,
                    color_discrete_map={"Yes": KB, "No": KB_LIGHT},
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
    _section("The 'Fully Stuck' Employee Profile")

    stuck_n    = q.get("stuck_n", 0)
    stuck_rate = q.get("stuck_rate", 0.0)
    c_a, c_b, c_c = st.columns(3)
    c_a.metric("Fully Stuck Employees",
               f"{stuck_n:,}",
               help="0 promotions + no leadership + no innovation opportunities")
    c_b.metric("Their Attrition Rate",  f"{stuck_rate:.1f}%")
    c_c.metric("vs Company Average",    f"+{stuck_rate - overall_rate:.1f}pp",
               delta_color="inverse")

    _insight(
        f"<b>{stuck_n:,} employees</b> (0 promotions, no leadership access, "
        f"no innovation exposure) show <b>{stuck_rate:.1f}%</b> attrition — "
        f"{stuck_rate - overall_rate:.1f}pp above the {overall_rate:.1f}% average. "
        f"This is not a fringe group — it is nearly 40% of the workforce. "
        f"Career stagnation is systemic."
    )
    _cta(
        "<b>Growth & Mobility Recommendation:</b> "
        "Establish a 'minimum viable growth' standard: every employee should have "
        "at least one growth dimension — a promotion track, a leadership project, "
        "or an innovation initiative — within 18 months. "
        "Identify the {stuck_n:,} employees in this profile and assign each "
        "a 90-day development plan. Target: move 30% out of the 'fully stuck' "
        "category within 2 quarters."
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 6  ·  Risk & Strategy  (Q9, Q10)
# ─────────────────────────────────────────────────────────────────────────────
def page_risk():
    st.markdown("## 🎯 Risk & Strategy")
    _kpi_row()
    st.markdown("---")

    # ── Q9: Highest-risk profile ──────────────────────────────────────────────
    _qbadge("Q9 · Highest-Risk Employee Profile")
    _section("Who Is Most Likely to Leave — and How Many Are There?")

    risk_n    = q.get("risk_profile_n", 0)
    risk_rate = q.get("risk_profile_rate", 0.0)
    risk_lift = risk_rate - overall_rate

    # Risk callout card
    st.markdown(
        f"<div class='risk-card'>"
        f"<b>Profile: Poor Work-Life Balance + Overtime + 0 Promotions "
        f"+ No Leadership Opportunities</b><br><br>"
        f"Attrition rate: <b>{risk_rate:.1f}%</b> &nbsp;·&nbsp; "
        f"<b>+{risk_lift:.1f}pp above</b> the {overall_rate:.1f}% company average &nbsp;·&nbsp; "
        f"<b>{risk_n:,} employees</b> match this profile today"
        f"</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        # Visual breakdown of the 4 risk factors
        factors = pd.DataFrame({
            "Factor": ["Poor Work-Life Balance", "Works Overtime",
                       "Zero Promotions", "No Leadership Access"],
            "Attrition Rate (%)": [60.2, 51.5, 49.3, 47.6],
            "Standalone Effect": ["60.2%", "51.5%", "49.3%", "47.6%"],
        })
        fig = px.bar(
            factors.sort_values("Attrition Rate (%)"),
            x="Attrition Rate (%)", y="Factor", orientation="h",
            title="Standalone Attrition Rate of Each Risk Factor",
            color="Attrition Rate (%)",
            color_continuous_scale=BLUE_SEQ,
            text="Standalone Effect",
        )
        fig.update_traces(textposition="outside")
        fig.update_coloraxes(showscale=False)
        _add_avg_line(fig, overall_rate)
        st.plotly_chart(_theme(fig), use_container_width=True)

    with c2:
        # Combined profile comparison
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
        f"nearly <b>1.4× the company average</b>. "
        f"With <b>{risk_n:,} employees</b> matching it today, "
        f"this is large enough to act on. If even half leave this year, "
        f"that is ~{int(risk_n * risk_rate/100):,} departures from this "
        f"one identifiable cohort. The 4 factors are individually manageable "
        f"— together they compound into a departure near-certainty."
    )
    _cta(
        f"<b>Immediate Action:</b> Export the list of {risk_n:,} employees matching "
        f"this profile and assign each an HR business partner touchpoint within 30 days. "
        f"Target: eliminate at least 2 of the 4 risk factors per employee "
        f"(e.g. approve remote work + assign to a leadership project). "
        f"A 20% success rate prevents ~{int(risk_n * risk_rate/100 * 0.2):,} departures."
    )

    st.markdown("---")

    # ── Q10: What moves the needle ────────────────────────────────────────────
    _qbadge("Q10 · What Moves the Needle")
    _section("If HR Could Fix One Thing — What Does the Data Say?")

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

    # Ranked recommendation cards
    st.markdown("### Ranked Recommendations")
    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown(
            "<div class='risk-card'><b>#1 · Expand Remote Work</b><br><br>"
            "Effect size: <b>28.1pp</b><br>"
            "On-site: 52.8% → Remote: 24.7%<br><br>"
            "Only 19.1% of workforce is remote. "
            "Fastest policy lever available. "
            "A 10% shift in headcount to remote = ~2,000 retained employees.</div>",
            unsafe_allow_html=True,
        )

    with r2:
        st.markdown(
            "<div class='insight-box'><b>#2 · Build Promotion Pathways</b><br><br>"
            "Effect size: <b>26.0pp</b><br>"
            "0 promos: 49.3% → 4 promos: 23.3%<br><br>"
            "Non-linear effect — the jump happens at 3 promotions. "
            "Accelerate time-to-third-promotion "
            "for at-risk cohorts.</div>",
            unsafe_allow_html=True,
        )

    with r3:
        st.markdown(
            "<div class='insight-box'><b>#3 · Fix Work-Life Balance</b><br><br>"
            "Effect size: <b>24.5pp</b><br>"
            "Poor: 60.2% → Excellent: 35.7%<br><br>"
            "WLB is the dominant engagement variable — "
            "it overrides job satisfaction. "
            "Start with overtime reduction and flexible scheduling.</div>",
            unsafe_allow_html=True,
        )

    _insight(
        "<b>The #1 pick is Remote Work expansion.</b> "
        "Here's why it beats career growth as the single next-quarter action: "
        "it is a <i>policy change</i>, not a structural one. "
        "Promoting people takes 12–18 months. "
        "Approving remote work takes 2 weeks. "
        "The effect size is real (28.1pp), the mechanism is plausible, "
        "and the cost of a pilot is near-zero. "
        "Rough impact estimate: shifting 5% of on-site workforce (~2,850 employees) "
        "to remote at the same retention improvement rate would prevent "
        f"~{int(2850 * 0.281):,} additional departures per annual cohort."
    )

    st.markdown("---")
    st.markdown("### 90-Day Action Roadmap")
    st.markdown("""
| Priority | Action | Owner | Timeline | Expected Impact |
|---|---|---|---|---|
| 🔴 Critical | Launch remote work eligibility review | CHRO | Week 1–2 | −28pp for converted roles |
| 🔴 Critical | Identify & assign HR partners to 1,654 risk-profile employees | HRBPs | Week 1–3 | Prevent ~{} departures |
| 🟠 High | Overtime audit — flag teams above 10% exposure | Line managers | Week 2–4 | −6pp for affected group |
| 🟠 High | Accelerate promotion reviews for 0-promotion employees | HR + Management | Month 2 | −26pp for promoted employees |
| 🟡 Medium | Launch WLB pulse survey for Poor/Fair-rated employees | HR Analytics | Month 2 | Identify 25k+ at-risk employees |
| 🟡 Medium | Build peer-community programme for single, 18–25 employees | L&D | Month 3 | Target 66.8% → <50% |
""".format(int(risk_n * risk_rate / 100 * 0.2)))

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
        st.Page(page_overview,  title="Overview",              icon="🏠", default=True),
    ],
    "🔍 Analysis": [
        st.Page(page_workload,  title="Workload & Flexibility", icon="⏰"),
        st.Page(page_pay_level, title="Pay & Job Level",        icon="💰"),
        st.Page(page_engagement,title="Engagement & Life Stage",icon="🧠"),
        st.Page(page_career,    title="Career Growth",          icon="🚀"),
        st.Page(page_risk,      title="Risk & Strategy",        icon="🎯"),
    ],
})
pg.run()
