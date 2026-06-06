"""
app.py — HR Attrition Dashboard
Kayfa AI & Data Analytics Internship · Week 1

Run locally:  streamlit run app.py
Deploy:       Push to GitHub → share.streamlit.io
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from Data_Handling import load_and_clean, compute_aggregration, filtered_kpis


# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG — must be the FIRST Streamlit call in the script
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HR Attrition Dashboard · Kayfa",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────
# THEME — Blue & White  (Kayfa brand)
# All color values are CSS variables — change the hex in :root once
# and every card, sidebar, and widget updates automatically.
# ─────────────────────────────────────────────────────────────────
KAYFA_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    :root {
        --kayfa-blue:        #1A5AFF;
        --kayfa-blue-dark:   #1245CC;
        --kayfa-blue-mid:    #3B72FF;
        --kayfa-blue-light:  #E8EFFF;
        --kayfa-blue-faint:  #F4F7FF;
        --white:             #FFFFFF;
        --gray-100:          #F0F2F6;
        --gray-300:          #C8CDD8;
        --gray-600:          #6B7280;
        --text-primary:      #0F1C3F;
        --text-secondary:    #4B5563;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: var(--text-primary);
    }

    /* Main area */
    .main .block-container { background: var(--white); padding: 2rem 2.5rem; }

    /* Sidebar — Kayfa blue */
    section[data-testid="stSidebar"] { background: var(--kayfa-blue) !important; }
    section[data-testid="stSidebar"] * { color: var(--white) !important; }
    section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background: var(--kayfa-blue-dark) !important;
    }
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div {
        background: var(--kayfa-blue-dark) !important;
        border-color: var(--kayfa-blue-mid) !important;
    }

    /* KPI cards */
    .kpi-card {
        background: var(--kayfa-blue-faint);
        border: 1px solid var(--kayfa-blue-light);
        border-left: 4px solid var(--kayfa-blue);
        border-radius: 10px;
        padding: 1.1rem 1.4rem;
        margin-bottom: 0.5rem;
    }
    .kpi-label {
        font-size: 0.72rem; font-weight: 600; color: var(--gray-600);
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem;
    }
    .kpi-value { font-size: 2rem; font-weight: 700; color: var(--kayfa-blue); line-height: 1; }
    .kpi-delta-bad  { font-size: 0.78rem; color: #DC2626; margin-top: 0.25rem; font-weight: 600; }
    .kpi-delta-good { font-size: 0.78rem; color: #16A34A; margin-top: 0.25rem; font-weight: 600; }
    .kpi-sub        { font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.25rem; }

    /* Section headers */
    .section-title {
        font-size: 1rem; font-weight: 700; color: var(--text-primary);
        border-bottom: 2px solid var(--kayfa-blue-light);
        padding-bottom: 0.4rem; margin-bottom: 1rem; margin-top: 1.6rem;
    }

    /* Insight boxes */
    .insight-box {
        background: var(--kayfa-blue-faint);
        border-left: 3px solid var(--kayfa-blue);
        border-radius: 6px; padding: 0.7rem 1rem;
        font-size: 0.83rem; color: var(--text-secondary);
        margin-top: 0.5rem;
    }
    .insight-box b { color: var(--kayfa-blue); }

    /* Override Streamlit defaults */
    h1, h2, h3 { color: var(--text-primary) !important; }
    footer { visibility: hidden; }
    .stAlert { border-radius: 8px; }
</style>
"""

# ─────────────────────────────────────────────────────────────────
# PLOTLY THEME HELPERS
# One config dict reused across every chart — change colors globally
# by editing these constants, nothing else.
# ─────────────────────────────────────────────────────────────────
KAYFA_BLUE       = "#1A5AFF"
KAYFA_BLUE_DARK  = "#1245CC"
KAYFA_BLUE_LIGHT = "#E8EFFF"
BLUE_SEQ = ["#E8EFFF", "#BDD0FF", "#7FA8FF", "#4C84FF",
            "#1A5AFF", "#1245CC", "#0D31A3", "#081F7A"]

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#0F1C3F"),
    margin=dict(t=44, b=28, l=8, r=8),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)

def _theme(fig: go.Figure) -> go.Figure:
    """Apply Kayfa blue/white theme to any Plotly figure."""
    fig.update_layout(**_LAYOUT)
    fig.update_xaxes(gridcolor="#E8EFFF", linecolor="#C8CDD8", tickfont_size=11)
    fig.update_yaxes(gridcolor="#E8EFFF", linecolor="#C8CDD8", tickfont_size=11)
    return fig

def _insight(text: str):
    """Render a branded insight box below a chart."""
    st.markdown(f"<div class='insight-box'>{text}</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# DATA LOADING — cached so it runs ONCE per session
# @st.cache_data stores the result in memory after the first call.
# Every widget rerun calls this but gets the cached copy instantly.
# ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading & cleaning data…")
def get_data():
    df   = load_and_clean("train.csv", "test.csv")
    aggs = compute_aggregration(df)
    return df, aggs

df, aggs = get_data()


# ─────────────────────────────────────────────────────────────────
# INJECT CSS
# ─────────────────────────────────────────────────────────────────
st.markdown(KAYFA_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# SIDEBAR — FILTERS
# All filters build a single boolean mask applied in one O(n) step.
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Filters")
    st.markdown("---")

    all_roles   = sorted(df["job_role"].unique().tolist())
    all_genders = sorted(df["gender"].unique().tolist())
    all_levels  = df["job_level"].cat.categories.tolist()   # respects ordinal order
    all_sizes   = df["company_size"].cat.categories.tolist()

    sel_roles   = st.multiselect("Job Role",    all_roles,   default=all_roles)
    sel_genders = st.multiselect("Gender",       all_genders, default=all_genders)
    sel_levels  = st.multiselect("Job Level",    all_levels,  default=all_levels)
    sel_sizes   = st.multiselect("Company Size", all_sizes,   default=all_sizes)

    age_min, age_max = int(df["age"].min()), int(df["age"].max())
    sel_age = st.slider("Age Range", age_min, age_max, (age_min, age_max))

    sel_remote = st.radio("Work Location", ["All", "Remote Only", "On-site Only"], index=0)
    sel_ot     = st.radio("Overtime",      ["All", "With Overtime", "No Overtime"],  index=0)

    st.markdown("---")
    st.caption("Kayfa AI & Data Analytics Internship · Week 1")


# ─────────────────────────────────────────────────────────────────
# APPLY FILTERS — single boolean mask, O(n), one indexing step
# Build all conditions first then AND them together.
# WHY: chained df[c1][c2][c3] creates intermediate DataFrame copies.
#      One mask avoids that entirely.
# ─────────────────────────────────────────────────────────────────
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
    st.warning("No employees match the current filters. Adjust the sidebar.")
    st.stop()


# ─────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 7])

with col_logo:
    # Replace with: st.image("company_logo2.png", width=90)
    # Fallback renders the Arabic brand mark so the header is never empty
    try:
        st.image("company_logo2.png", width=90)
    except Exception:
        st.markdown(
            "<div style='font-size:2.4rem;font-weight:900;"
            "color:#1A5AFF;letter-spacing:-1px;padding-top:6px;'>كيف</div>",
            unsafe_allow_html=True,
        )

with col_title:
    st.markdown(
        "<h1 style='margin:0;font-size:1.7rem;font-weight:700;color:#0F1C3F;'>"
        "Employee Attrition Dashboard</h1>"
        "<p style='color:#6B7280;margin:0;font-size:0.85rem;'>"
        "HR Analytics · Synthetic Dataset · 74,498 records</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")


# ─────────────────────────────────────────────────────────────────
# KPI ROW
# filtered_kpis() is O(m) — scalar passes on the filtered subset.
# Delta shows how the filtered group compares to the overall company.
# ─────────────────────────────────────────────────────────────────
kpis         = filtered_kpis(dff)
overall_rate = aggs["overall_rate"] * 100
delta        = kpis["rate"] - overall_rate

def _kpi(col, label, value, sub="", delta_val=None):
    if delta_val is not None:
        sign   = "+" if delta_val >= 0 else ""
        cls    = "kpi-delta-bad" if delta_val > 0 else "kpi-delta-good"
        sub_html = f"<div class='{cls}'>{sign}{delta_val:.1f}% vs overall</div>"
    else:
        sub_html = f"<div class='kpi-sub'>{sub}</div>"

    col.markdown(
        f"<div class='kpi-card'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div>"
        f"{sub_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

k1, k2, k3, k4 = st.columns(4)
_kpi(k1, "Total Employees",    f"{kpis['total']:,}",          sub=f"of {aggs['total_employees']:,} total")
_kpi(k2, "Attrition Rate",     f"{kpis['rate']:.1f}%",        delta_val=delta)
_kpi(k3, "Avg Monthly Income", f"${kpis['avg_income']:,.0f}", sub="filtered group")
_kpi(k4, "Avg Tenure",         f"{kpis['avg_tenure']:.1f} yrs", sub="years at company")


# ─────────────────────────────────────────────────────────────────
# EXECUTIVE SUMMARY
# ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📋 Executive Summary</div>", unsafe_allow_html=True)

employees_left   = int(dff["attrition"].sum())
employees_stayed = len(dff) - employees_left
income_left      = dff[dff["attrition"] == 1]["monthly_income"].mean()
income_stayed    = dff[dff["attrition"] == 0]["monthly_income"].mean()
income_diff_pct  = (income_left - income_stayed) / income_stayed * 100
avg_age_left     = dff[dff["attrition"] == 1]["age"].mean()
avg_age_stayed   = dff[dff["attrition"] == 0]["age"].mean()

c_ins, c_rec = st.columns(2)

with c_ins:
    st.subheader("Key Insights")
    if kpis["rate"] > overall_rate + 5:
        st.error(f"⚠️ **HIGH RISK** — Attrition ({kpis['rate']:.1f}%) is {kpis['rate']-overall_rate:.1f}% above company average")
    elif kpis["rate"] < overall_rate - 5:
        st.success(f"✅ **POSITIVE** — Attrition ({kpis['rate']:.1f}%) is {overall_rate-kpis['rate']:.1f}% below company average")
    else:
        st.info(f"📊 Attrition ({kpis['rate']:.1f}%) is near company average ({overall_rate:.1f}%)")

    st.info(f"💼 {employees_left:,} of {len(dff):,} employees left ({employees_left/len(dff)*100:.1f}%)")
    st.info(f"👥 Leavers are younger on average — {avg_age_left:.0f} yrs vs {avg_age_stayed:.0f} yrs for those who stayed")
    if income_diff_pct < 0:
        st.warning(f"💰 Leavers earned {abs(income_diff_pct):.1f}% less than those who stayed — compensation is a likely factor")

with c_rec:
    st.subheader("💡 Recommendations")
    if kpis["rate"] > 15:
        st.error("🎯 **PRIORITY** — Conduct exit interviews to identify root causes")
        st.error("💰 Review compensation for high-attrition roles immediately")
    if income_diff_pct < -5:
        st.warning("💵 Implement salary review for lower-paid employee bands")
        st.warning("📈 Create clear career development paths to improve retention")
    st.success("🎓 Invest in professional development & training programs")
    st.success("🤝 Launch work-life balance improvement initiatives")
    st.success("🎖️ Strengthen employee recognition programs")

st.markdown("---")


# ─────────────────────────────────────────────────────────────────
# SECTION 1: ATTRITION OVERVIEW
# Groupby on filtered df — O(m) per chart
# ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>📊 Attrition Overview</div>", unsafe_allow_html=True)

c1, c2 = st.columns([3, 2])

with c1:
    role_data = (
        dff.groupby("job_role", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)"})
        .sort_values("Attrition Rate (%)", ascending=True)
    )
    fig = px.bar(
        role_data, x="Attrition Rate (%)", y="job_role", orientation="h",
        title="Attrition Rate by Job Role",
        color="Attrition Rate (%)", color_continuous_scale=BLUE_SEQ,
        text="Attrition Rate (%)",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_layout(yaxis_title="", xaxis_title="Attrition Rate (%)")
    st.plotly_chart(_theme(fig), use_container_width=True)

    top_role = role_data.iloc[-1]
    _insight(f"<b>Highest-risk role:</b> {top_role['job_role']} at {top_role['Attrition Rate (%)']:.1f}% — consider role-specific retention strategies.")

with c2:
    fig = go.Figure(go.Pie(
        labels=["Stayed", "Left"],
        values=[employees_stayed, employees_left],
        hole=0.62,
        marker_colors=[KAYFA_BLUE_LIGHT, KAYFA_BLUE],
        textinfo="percent+label",
        hovertemplate="%{label}: %{value:,} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title="Stayed vs. Left",
        annotations=[dict(
            text=f"<b>{employees_left/(employees_stayed+employees_left)*100:.1f}%</b><br>Left",
            x=0.5, y=0.5, font_size=16, font_color=KAYFA_BLUE, showarrow=False,
        )]
    )
    st.plotly_chart(_theme(fig), use_container_width=True)
    _insight(f"<b>{employees_stayed:,}</b> retained &nbsp;·&nbsp; <b>{employees_left:,}</b> lost &nbsp;·&nbsp; Retention rate: <b>{employees_stayed/(employees_stayed+employees_left)*100:.1f}%</b>")


# ─────────────────────────────────────────────────────────────────
# SECTION 2: INCOME & AGE
# ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>💰 Income & Age Patterns</div>", unsafe_allow_html=True)

c3, c4 = st.columns(2)

with c3:
    # Box plot — shows distribution shape, not just averages. More honest.
    fig = px.box(
        dff, x=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        y="monthly_income", title="Monthly Income Distribution",
        color=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        color_discrete_map={"Stayed": KAYFA_BLUE_LIGHT, "Left": KAYFA_BLUE},
        points=False,  # dataset is 74k rows — individual points would be noise
    )
    fig.update_layout(xaxis_title="", yaxis_title="Monthly Income ($)", showlegend=False)
    st.plotly_chart(_theme(fig), use_container_width=True)
    _insight(f"Employees who left earned <b>{abs(income_diff_pct):.1f}% {'less' if income_diff_pct < 0 else 'more'}</b> on average — compensation is {'likely a driver' if income_diff_pct < -3 else 'not a primary driver'}.")

with c4:
    fig = px.histogram(
        dff, x="age",
        color=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        barmode="overlay", opacity=0.75, nbins=20,
        title="Age Distribution by Attrition",
        color_discrete_map={"Stayed": KAYFA_BLUE_LIGHT, "Left": KAYFA_BLUE},
    )
    fig.update_layout(xaxis_title="Age", yaxis_title="Count", legend_title="")
    st.plotly_chart(_theme(fig), use_container_width=True)
    _insight(f"Leavers average <b>{avg_age_left:.0f} years</b> vs <b>{avg_age_stayed:.0f} years</b> for stayers — younger employees are at higher risk.")


# ─────────────────────────────────────────────────────────────────
# SECTION 3: SATISFACTION & WORK-LIFE FACTORS
# ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🧠 Satisfaction & Work-Life Factors</div>", unsafe_allow_html=True)

c5, c6 = st.columns(2)

with c5:
    wlb = (
        dff.groupby("work_life_balance", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)"})
    )
    fig = px.bar(
        wlb, x="work_life_balance", y="Attrition Rate (%)",
        title="Work-Life Balance vs Attrition",
        color="Attrition Rate (%)", color_continuous_scale=BLUE_SEQ,
        text="Attrition Rate (%)",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_layout(xaxis_title="Work-Life Balance", yaxis_title="Attrition Rate (%)")
    st.plotly_chart(_theme(fig), use_container_width=True)

    poor_wlb = wlb[wlb["work_life_balance"] == "Poor"]["Attrition Rate (%)"]
    if len(poor_wlb):
        _insight(f"Employees with <b>Poor</b> work-life balance show <b>{poor_wlb.values[0]:.1f}%</b> attrition — nearly double Excellent-rated employees.")

with c6:
    sat = (
        dff.groupby("job_satisfaction", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)"})
    )
    fig = px.bar(
        sat, x="job_satisfaction", y="Attrition Rate (%)",
        title="Job Satisfaction vs Attrition",
        color="Attrition Rate (%)", color_continuous_scale=BLUE_SEQ,
        text="Attrition Rate (%)",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_layout(xaxis_title="Job Satisfaction", yaxis_title="Attrition Rate (%)")
    st.plotly_chart(_theme(fig), use_container_width=True)

    low_sat = sat[sat["job_satisfaction"] == "Low"]["Attrition Rate (%)"]
    if len(low_sat):
        _insight(f"<b>Low</b> satisfaction employees have <b>{low_sat.values[0]:.1f}%</b> attrition — engagement improvement is a high-ROI intervention.")


# ─────────────────────────────────────────────────────────────────
# SECTION 4: OVERTIME & REMOTE WORK
# Overtime was missing in the original — real data shows it's a signal
# ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🕐 Overtime & Remote Work</div>", unsafe_allow_html=True)

c7, c8 = st.columns(2)

with c7:
    ot = (
        dff.groupby("overtime", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)"})
    )
    fig = px.bar(
        ot, x="overtime", y="Attrition Rate (%)",
        title="Overtime vs Attrition Rate",
        color="overtime",
        color_discrete_map={"Yes": KAYFA_BLUE, "No": KAYFA_BLUE_LIGHT},
        text="Attrition Rate (%)",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(xaxis_title="Works Overtime", yaxis_title="Attrition Rate (%)", showlegend=False)
    st.plotly_chart(_theme(fig), use_container_width=True)

    ot_yes = ot[ot["overtime"] == "Yes"]["Attrition Rate (%)"]
    ot_no  = ot[ot["overtime"] == "No"]["Attrition Rate (%)"]
    if len(ot_yes) and len(ot_no):
        diff = ot_yes.values[0] - ot_no.values[0]
        _insight(f"Overtime employees leave at <b>{diff:+.1f}%</b> higher rate — burnout is a measurable retention risk.")

with c8:
    remote = (
        dff.groupby("remote_work", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)"})
    )
    fig = px.bar(
        remote, x="remote_work", y="Attrition Rate (%)",
        title="Remote Work vs Attrition Rate",
        color="remote_work",
        color_discrete_map={"Yes": KAYFA_BLUE, "No": KAYFA_BLUE_LIGHT},
        text="Attrition Rate (%)",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(xaxis_title="Remote Work", yaxis_title="Attrition Rate (%)", showlegend=False)
    st.plotly_chart(_theme(fig), use_container_width=True)

    r_yes = remote[remote["remote_work"] == "Yes"]["Attrition Rate (%)"]
    r_no  = remote[remote["remote_work"] == "No"]["Attrition Rate (%)"]
    if len(r_yes) and len(r_no):
        diff = r_no.values[0] - r_yes.values[0]
        if diff > 0:
            _insight(f"Remote workers leave <b>{diff:.1f}% less</b> than on-site employees — expanding remote options could improve retention.")
        else:
            _insight(f"Remote workers leave <b>{abs(diff):.1f}% more</b> — evaluate remote work engagement policies.")


# ─────────────────────────────────────────────────────────────────
# SECTION 5: PROMOTIONS
# ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🚀 Promotions & Career Growth</div>", unsafe_allow_html=True)

if "number_of_promotions" in dff.columns:
    promo = (
        dff.groupby("number_of_promotions", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)"})
    )
    fig = px.line(
        promo, x="number_of_promotions", y="Attrition Rate (%)",
        title="Number of Promotions vs Attrition Rate",
        markers=True, line_shape="spline",
    )
    fig.update_traces(line_color=KAYFA_BLUE, marker_color=KAYFA_BLUE, marker_size=9)
    fig.update_layout(xaxis_title="Number of Promotions", yaxis_title="Attrition Rate (%)")
    st.plotly_chart(_theme(fig), use_container_width=True)

    zero_promo = promo[promo["number_of_promotions"] == 0]["Attrition Rate (%)"]
    if len(zero_promo):
        _insight(f"Employees with <b>0 promotions</b> show <b>{zero_promo.values[0]:.1f}%</b> attrition — career stagnation is a key driver. Structured promotion pathways are essential.")


# ─────────────────────────────────────────────────────────────────
# SECTION 6: CORRELATION HEATMAP
# ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🔗 Numeric Feature Correlations</div>", unsafe_allow_html=True)

num_cols = dff.select_dtypes("number").columns.tolist()
corr     = dff[num_cols].corr().round(2)

fig = go.Figure(go.Heatmap(
    z=corr.values,
    x=corr.columns.tolist(),
    y=corr.columns.tolist(),
    colorscale=[[0, KAYFA_BLUE_LIGHT], [0.5, "#7FA8FF"], [1, KAYFA_BLUE_DARK]],
    zmin=-1, zmax=1,
    text=corr.values,
    texttemplate="%{text}",
    hovertemplate="%{x} × %{y}: %{z}<extra></extra>",
))
fig.update_layout(title="Feature Correlation Matrix", height=420, xaxis=dict(tickangle=-35))
st.plotly_chart(_theme(fig), use_container_width=True)
_insight("Use this to spot multicollinearity and find which numeric features co-move with attrition (bottom row / rightmost column).")


# ─────────────────────────────────────────────────────────────────
# ACTION PLAN
# ─────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>🎯 Action Plan for Stakeholders</div>", unsafe_allow_html=True)

st.markdown("""
### Immediate Actions (0–30 days)
1. **Exit Interviews** — Conduct structured interviews with all departing employees
2. **Compensation Audit** — Review salaries for roles with attrition above 50%
3. **Employee Survey** — Gather real-time feedback on work-life balance & satisfaction

### Short-term Initiatives (1–3 months)
1. **Career Development** — Launch mentorship & structured promotion pathways
2. **Overtime Audit** — Identify teams with chronic overtime; redistribute workload
3. **Recognition Program** — Implement peer and manager recognition system

### Long-term Strategy (3–12 months)
1. **Hybrid Work Policy** — Expand remote options for on-site roles where feasible
2. **Culture Investment** — Build inclusive, growth-oriented organizational culture
3. **Retention Metrics** — Track attrition KPIs monthly against these baselines

### Expected Impact
- 📉 Reduce overall attrition rate by **15–25%** within 12 months
- 💰 Lower recruitment & onboarding costs significantly
- 📈 Improve team productivity, morale, and institutional knowledge retention
""")

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#6B7280;font-size:0.78rem;'>"
    "Kayfa AI & Data Analytics Internship · Week 1 · "
    "Synthetic dataset — findings are for learning purposes only.</p>",
    unsafe_allow_html=True,
)
