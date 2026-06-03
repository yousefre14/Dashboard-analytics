import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from PIL import Image


from Task1 import load_and_clean, compute_aggregration, filtered_kpis


KAYFA_BLUE       = "#1A5AFF"
KAYFA_BLUE_DARK  = "#1245CC"
KAYFA_BLUE_LIGHT = "#E8EFFF"
BLUE_SEQ = ["#E8EFFF", "#BDD0FF", "#7FA8FF", "#4C84FF",
            "#1A5AFF", "#1245CC", "#0D31A3", "#081F7A"]

def _theme(fig: go.Figure) -> go.Figure:
    """Apply Kayfa blue/white theme to any Plotly figure."""
    fig.update_xaxes(gridcolor="#E8EFFF", linecolor="#C8CDD8", tickfont_size=11)
    fig.update_yaxes(gridcolor="#E8EFFF", linecolor="#C8CDD8", tickfont_size=11)
    return fig
 
def _insight(text: str):
    """Render a branded insight box below a chart."""
    st.markdown(f"<div class='insight-box'>{text}</div>", unsafe_allow_html=True)

st.set_page_config(
    page_title="HR Attrition Dashboard",
    layout="wide",
)

# cashed data
@st.cache_data
def get_data():
    df = load_and_clean("train.csv", "test.csv")
    aggs = compute_aggregration(df)
    return df, aggs

df, aggs = get_data()

#header

col_logo, col_title = st.columns([1, 4]) #the distance between the logo and the title 

with col_logo:
    try:
        logo = Image.open("company_logo2.png")  
        st.image(logo, width=800)
    except:
        st.markdown(
            unsafe_allow_html=True
        )

st.title("Employee Attrition Dashboard")
st.subheader("HR Analytics - Strategic Insights & Recommendations")

st.markdown("---")

#sidebar

with st.sidebar:
    st.header("Filters")  
    
    # the filters to each column
    all_roles = sorted(df["job_role"].unique().tolist())
    all_genders = sorted(df["gender"].unique().tolist())
    all_levels = df["job_level"].cat.categories.tolist()
    all_sizes = df["company_size"].cat.categories.tolist()
    
    sel_roles = st.multiselect("Job Role", all_roles, default=all_roles)
    sel_genders = st.multiselect("Gender", all_genders, default=all_genders)
    sel_levels = st.multiselect("Job Level", all_levels, default=all_levels)
    sel_sizes = st.multiselect("Company Size", all_sizes, default=all_sizes)
    
    age_min, age_max = int(df["age"].min()), int(df["age"].max())
    sel_age = st.slider("Age Range", age_min, age_max, (age_min, age_max))
    
    sel_remote = st.radio("Work Location", ["All", "Remote Only", "On-site Only"])

#filters
#boolean mask to add to filtered dataset = dff
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

dff = df[mask]

if len(dff) == 0:
    st.warning("No employees match the current filters.")
    st.stop()

#kpi(metric)

kpis = filtered_kpis(dff)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Employees", f"{kpis['total']:,}")

with col2:
    overall_rate = aggs['overall_rate'] * 100
    delta = kpis['rate'] - overall_rate
    st.metric("Attrition Rate", f"{kpis['rate']:.1f}%", delta=f"{delta:+.1f}%")

with col3:
    st.metric("Avg Monthly Income", f"${kpis['avg_income']:,.0f}")

with col4:
    st.metric("Avg Tenure", f"{kpis['avg_tenure']:.1f} yrs")

st.markdown("---")

# key insights
st.header("Executive Summary")

# Calculate insights
attrition_rate = kpis['rate']
employees_left = int(dff['attrition'].sum())
employees_stayed = len(dff) - employees_left

col1, col2 = st.columns(2)

with col1:
    st.subheader("Key Insights")
    
    insights = []
    
    # Insight 1: Attrition severity
    if attrition_rate > overall_rate + 5:
        insights.append(f"⚠️ **HIGH RISK**: Attrition rate ({attrition_rate:.1f}%) is {attrition_rate - overall_rate:.1f}% above company average")
    elif attrition_rate < overall_rate - 5:
        insights.append(f"✅ **POSITIVE**: Attrition rate ({attrition_rate:.1f}%) is {overall_rate - attrition_rate:.1f}% below company average")
    else:
        insights.append(f"📊 Attrition rate ({attrition_rate:.1f}%) is near company average ({overall_rate:.1f}%)")
    
    # Insight 2: Number of people affected
    insights.append(f"💼 {employees_left:,} out of {len(dff):,} employees have left ({employees_left/len(dff)*100:.1f}%)")
    
    # Insight 3: Age distribution
    avg_age_left = dff[dff['attrition'] == 1]['age'].mean()
    avg_age_stayed = dff[dff['attrition'] == 0]['age'].mean()
    insights.append(f"👥 Employees who left are younger (avg {avg_age_left:.0f} yrs) vs those who stayed ({avg_age_stayed:.0f} yrs)")
    
    # Insight 4: Income gap
    income_left = dff[dff['attrition'] == 1]['monthly_income'].mean()
    income_stayed = dff[dff['attrition'] == 0]['monthly_income'].mean()
    income_diff = ((income_left - income_stayed) / income_stayed * 100)
    if income_diff < 0:
        insights.append(f"💰 Lower-paid employees are leaving ({income_diff:.1f}% less income than those who stayed)")
    
    for insight in insights:
        st.info(insight)

with col2:
    st.subheader("💡 Recommendations")
    
    recommendations = []
    
    # Recommendation based on attrition
    if attrition_rate > 15:
        recommendations.append("🎯 **PRIORITY**: Conduct exit interviews to understand root causes")
        recommendations.append("💰 Review compensation structure, especially for high-risk groups")
    
    if income_diff < -5:
        recommendations.append("💵 Implement salary review program for lower-paid employees")
        recommendations.append("📈 Consider career development paths to increase retention")
    
    recommendations.append("🎓 Invest in professional development & training programs")
    recommendations.append("🤝 Improve work-life balance initiatives")
    recommendations.append("🎖️ Strengthen employee recognition programs")
    
    for i, rec in enumerate(recommendations, 1):
        st.success(rec)

st.markdown("---")

# attrition overview

st.subheader("Attrition Overview")

col1, col2 = st.columns(2)

with col1:
    # Bar chart: Attrition by job role
    role_data = (
        dff.groupby("job_role", observed=True)["attrition"]
        .mean().mul(100).round(1)
        .reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)"})
        .sort_values("Attrition Rate (%)", ascending=True)
    )
    fig_role = px.bar(
        role_data, x="Attrition Rate (%)", y="job_role",
        orientation="h",
        title="Attrition Rate by Job Role",
    )
    st.plotly_chart(fig_role, use_container_width=True)
    
    # Insight for job roles
    highest_attrition_role = role_data.iloc[-1]
    st.info(f"**Highest Risk Role**: {highest_attrition_role['job_role']} ({highest_attrition_role['Attrition Rate (%)']:.1f}%) - Consider role-specific retention strategies")

with col2:
    # Donut chart: Stayed vs Left
    stayed = len(dff[dff["attrition"] == 0])
    left = len(dff[dff["attrition"] == 1])
    fig_donut = go.Figure(go.Pie(
        labels=["Stayed", "Left"],
        values=[stayed, left],
        hole=0.4,
    ))
    fig_donut.update_layout(title="Stayed vs Left")
    st.plotly_chart(fig_donut, use_container_width=True)
    
    # Insight for stayed/left
    st.info(f"📌 **Insight**: {stayed:,} employees retained | {left:,} employees lost | Retention rate: {(stayed/(stayed+left)*100):.1f}%")

st.markdown("---")

# INCOME vs AGE

st.subheader("💰 Income & Age Patterns")

col1, col2 = st.columns(2)

with col1:
    # Box plot: Income by attrition
    fig_box = px.box(
        dff, x=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        y="monthly_income",
        title="Monthly Income Distribution",
    )
    st.plotly_chart(fig_box, use_container_width=True)
    
    # Income insight
    income_diff_pct = income_diff
    st.warning(f"⚠️ Employees who left earn **{abs(income_diff_pct):.1f}% less** on average - compensation may be a factor")

with col2:
    # Histogram: Age distribution
    fig_age = px.histogram(
        dff,
        x="age",
        color=dff["attrition"].map({0: "Stayed", 1: "Left"}),
        barmode="overlay",
        title="Age Distribution by Attrition",
        nbins=20,
    )
    st.plotly_chart(fig_age, use_container_width=True)
    
    # Age insight
    st.info(f"📍 **Age Insight**: High turnover in younger employees ({avg_age_left:.0f} yrs) - focus on entry-level retention programs")

st.markdown("---")

# SATISFACTION FACTORS

st.subheader("🧠 Satisfaction & Work-Life Factors")

col1, col2 = st.columns(2)

with col1:
    if "work_life_balance" in dff.columns:
        wlb = (
            dff.groupby("work_life_balance", observed=True)["attrition"]
            .mean().mul(100).round(1)
            .reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)"})
        )
        fig_wlb = px.bar(
            wlb, x="work_life_balance", y="Attrition Rate (%)",
            title="Work-Life Balance vs Attrition",
        )
        st.plotly_chart(fig_wlb, use_container_width=True)
        
        # Insight for work-life balance
        poor_wlb = wlb[wlb['work_life_balance'] == 'Poor']['Attrition Rate (%)'].values
        if len(poor_wlb) > 0 and poor_wlb[0] > 20:
            st.warning(f"⚠️ Employees with Poor work-life balance have {poor_wlb[0]:.1f}% attrition - immediate action needed")
        else:
            st.info("✅ Work-life balance is positively correlated with retention")

with col2:
    if "job_satisfaction" in dff.columns:
        sat = (
            dff.groupby("job_satisfaction", observed=True)["attrition"]
            .mean().mul(100).round(1)
            .reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)"})
        )
        fig_sat = px.bar(
            sat, x="job_satisfaction", y="Attrition Rate (%)",
            title="Job Satisfaction vs Attrition",
        )
        st.plotly_chart(fig_sat, use_container_width=True)
        
        # Insight for job satisfaction
        low_sat = sat[sat['job_satisfaction'] == 'Low']['Attrition Rate (%)'].values
        if len(low_sat) > 0:
            st.warning(f"⚠️ Employees with Low satisfaction have {low_sat[0]:.1f}% attrition - engagement improvement needed")

st.markdown("---")

#REMOTE WORK
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
st.markdown("---")

 
# PROMOTIONS
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
st.markdown("---")


# FINAL RECOMMENDATIONS 
st.header("🎯 Action Plan for Stakeholders")

st.markdown("""
### Immediate Actions (0-30 days)
1. **Exit Interviews**: Conduct structured interviews with departing employees
2. **Compensation Audit**: Review salaries for roles with high attrition
3. **Employee Survey**: Gather feedback on work-life balance & satisfaction

### Short-term Initiatives (1-3 months)
1. **Career Development**: Launch mentorship & training programs
2. **Recognition Program**: Implement peer recognition system
3. **Work-Life Balance**: Review workload distribution & deadlines

### Long-term Strategy (3-12 months)
1. **Organizational Culture**: Foster inclusive, supportive environment
2. **Career Pathways**: Create clear advancement opportunities
3. **Retention Metrics**: Track improvements in attrition KPIs

### Expected Impact
- 📉 Reduce attrition rate by **15-25%**
- 💰 Save costs from reduced recruitment & training expenses
- 📈 Improve team productivity & morale
""")

st.markdown("---")
st.caption("Kayfa AI & Data Analytics Internship · Week 1 | Data-driven HR Analytics Dashboard")