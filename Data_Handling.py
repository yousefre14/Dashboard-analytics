"""
Data_Handling.py  —  HR Attrition Analytics
Kayfa AI & Data Analytics Internship · Week 1

All data loading, cleaning, and pre-computation lives here.
main.py imports and calls — no raw pandas in the UI layer.

Complexity contract: every operation is vectorized O(n).
Heavy aggregations run ONCE at load time via @st.cache_data.
"""

import pandas as pd
import numpy as np


# ── Ordinal maps — verified against the REAL CSV values ──────────────────────
ORDINAL_MAPS = {
    "work_life_balance":    ["Poor", "Fair", "Good", "Excellent"],
    "job_satisfaction":     ["Low", "Medium", "High", "Very High"],
    "performance_rating":   ["Low", "Below Average", "Average", "High"],
    "education_level":      ["High School", "Associate Degree",
                             "Bachelor's Degree", "Master's Degree", "PhD"],
    "job_level":            ["Entry", "Mid", "Senior"],
    "company_size":         ["Small", "Medium", "Large"],
    "company_reputation":   ["Poor", "Fair", "Good", "Excellent"],
    "employee_recognition": ["Low", "Medium", "High", "Very High"],
}


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 + 2  ·  LOAD, COMBINE & CLEAN
# ─────────────────────────────────────────────────────────────────────────────
def load_and_clean(train: str, test: str) -> pd.DataFrame:
    """
    Loads train.csv + test.csv, combines, cleans, and returns a typed DataFrame.

    WHY combine: train/test split is an ML Kaggle artifact — for analytics
    we want all 74,498 rows. No information should be left out.
    """
    # ── 1. Load & combine ────────────────────────────────────────────────────
    try:
        df_train = pd.read_csv(train)
        df_test  = pd.read_csv(test)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"[Data_Handling] CSV not found: {e}") from e

    df = pd.concat([df_train, df_test], ignore_index=True)

    # ── 2. Normalize column names → snake_case ───────────────────────────────
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    # ── 3. Drop exact duplicates (hash-based, O(n)) ──────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    if (dropped := before - len(df)):
        print(f"[clean] Removed {dropped} duplicate rows")

    # ── 4. Null handling — vectorized, no Python row loop ────────────────────
    # numeric  → median  (robust to outliers)
    # object   → mode    (most frequent category)
    for col in df.select_dtypes(include="number").columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    for col in df.select_dtypes(include="object").columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].mode()[0])

       # ── 5. CRITICAL: encode attrition 0 / 1 ─────────────────────────────────
    if df["attrition"].dtype == object:
        df["attrition"] = (
            df["attrition"]
            .str.strip()
            .str.lower()
            .map({
                "stayed": 0, "left": 1,
                "no": 0, "yes": 1,
                "0": 0, "1": 1,
            })
            .fillna(0)  # ← Fill ANY unmapped value with 0
        )

    df["attrition"] = df["attrition"].astype(int)

    # ── 6. Cast ordinals to ordered Categorical ──────────────────────────────
    # Without ordered=True, "Poor" < "Good" is undefined.
    # Values verified against real CSV — not the task-sheet descriptions.
    for col, order in ORDINAL_MAPS.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=order, ordered=True)

    print(f"[clean] Final shape: {df.shape} | "
          f"Attrition rate: {df['attrition'].mean():.1%}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PRE-COMPUTED AGGREGATIONS  (called once inside @st.cache_data)
# All O(n) groupby → mean/agg single passes.
# ─────────────────────────────────────────────────────────────────────────────
def compute_aggregration(df: pd.DataFrame) -> dict:
    """General aggregations used across multiple pages."""
    aggs = {}

    # Scalars
    aggs["overall_rate"]    = float(df["attrition"].mean())
    aggs["total_employee"]  = len(df)
    aggs["total_left"]      = int(df["attrition"].sum())
    aggs["avg_income"]      = float(df["monthly_income"].mean())

    # Attrition rate by categorical dimensions
    for col in ["job_role", "gender", "marital_status", "job_level",
                "company_size", "education_level", "remote_work",
                "overtime", "leadership_opportunities", "innovation_opportunities"]:
        if col in df.columns:
            aggs[f"rate_by_{col}"] = (
                df.groupby(col, observed=True)["attrition"]
                .mean().mul(100).round(1).reset_index()
                .rename(columns={"attrition": "Attrition Rate (%)"})
                .sort_values("Attrition Rate (%)", ascending=False)
            )

    # Attrition by ordinal — preserve category sort order (NOT sorted by value)
    for col in ["work_life_balance", "job_satisfaction",
                "performance_rating", "employee_recognition", "company_reputation"]:
        if col in df.columns:
            aggs[f"rate_by_{col}"] = (
                df.groupby(col, observed=True)["attrition"]
                .mean().mul(100).round(1).reset_index()
                .rename(columns={"attrition": "Attrition Rate (%)"})
            )

    # Promotions
    if "number_of_promotions" in df.columns:
        aggs["rate_by_promotions"] = (
            df.groupby("number_of_promotions", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)"})
        )

    # Numeric correlation matrix
    num_cols = df.select_dtypes("number").columns.tolist()
    aggs["corr_matrix"] = df[num_cols].corr().round(2)

    return aggs


def compute_q_aggregations(df: pd.DataFrame) -> dict:
    """
    Q4–Q10 specific aggregations — computed once at load time.
    Works on a copy so the original df is never mutated.
    """
    d = df.copy()
    q = {}

    # ── Q4: Income quartile within job level ─────────────────────────────────
    # Shows whether pay spread within a level drives attrition
    d["income_quartile"] = d.groupby("job_level", observed=True)["monthly_income"] \
        .transform(lambda x: pd.qcut(x, 4,
                   labels=["Bottom 25%", "Q2", "Q3", "Top 25%"],
                   duplicates="drop"))
    q["pay_by_level_quartile"] = (
        d.groupby(["job_level", "income_quartile"], observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)"})
    )

    # ── Q5: Retention timeline (tenure bands) ────────────────────────────────
    bins   = [0, 2, 5, 10, 20, 200]
    labels = ["0–2 yrs", "2–5 yrs", "5–10 yrs", "10–20 yrs", "20+ yrs"]
    d["tenure_band"] = pd.cut(d["years_at_company"], bins=bins,
                               labels=labels, right=False)
    q["attrition_by_tenure"] = (
        d.groupby("tenure_band", observed=True)["attrition"]
        .agg(["mean", "count"]).reset_index()
        .rename(columns={"mean": "Attrition Rate (%)", "count": "Employees"})
        .assign(**{"Attrition Rate (%)": lambda x: (x["Attrition Rate (%)"] * 100).round(1)})
    )

    # ── Q6: WLB × Job Satisfaction heatmap ──────────────────────────────────
    q["wlb_x_satisfaction"] = (
        d.groupby(["work_life_balance", "job_satisfaction"], observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)",
                          "work_life_balance": "Work-Life Balance",
                          "job_satisfaction": "Job Satisfaction"})
    )

    # ── Q7: Life-stage dimensions ────────────────────────────────────────────
    d["age_group"] = pd.cut(d["age"], bins=[17, 25, 35, 45, 60],
                             labels=["18–25", "26–35", "36–45", "46–60"])
    q["attrition_by_age_group"] = (
        d.groupby("age_group", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)", "age_group": "Age Group"})
    )
    q["attrition_by_marital"] = (
        d.groupby("marital_status")["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)",
                          "marital_status": "Marital Status"})
        .sort_values("Attrition Rate (%)", ascending=False)
    )
    q["attrition_by_dependents"] = (
        d.groupby("number_of_dependents")["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)",
                          "number_of_dependents": "Number of Dependents"})
    )

    # ── Q8: Career stagnation ────────────────────────────────────────────────
    q["attrition_by_promotions"] = (
        d.groupby("number_of_promotions", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)",
                          "number_of_promotions": "Number of Promotions"})
    )
    q["attrition_by_job_level"] = (
        d.groupby("job_level", observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)", "job_level": "Job Level"})
    )
    for col, label in [("leadership_opportunities", "Leadership Opportunities"),
                       ("innovation_opportunities", "Innovation Opportunities")]:
        if col in d.columns:
            q[f"attrition_by_{col}"] = (
                d.groupby(col)["attrition"]
                .mean().mul(100).round(1).reset_index()
                .rename(columns={"attrition": "Attrition Rate (%)", col: label})
            )
    # "Fully stuck" profile: 0 promotions + no leadership + no innovation
    stuck = d[
        (d["number_of_promotions"] == 0) &
        (d["leadership_opportunities"] == "No") &
        (d["innovation_opportunities"] == "No")
    ]
    q["stuck_n"]    = int(len(stuck))
    q["stuck_rate"] = float(stuck["attrition"].mean() * 100) if len(stuck) else 0.0

    # ── Q9: Highest-risk profile ─────────────────────────────────────────────
    # Poor WLB + Overtime + 0 Promotions + No Leadership
    risk_mask = (
        (d["work_life_balance"] == "Poor") &
        (d["overtime"] == "Yes") &
        (d["number_of_promotions"] == 0) &
        (d["leadership_opportunities"] == "No")
    )
    risk_group = d[risk_mask]
    q["risk_profile_n"]    = int(len(risk_group))
    q["risk_profile_rate"] = float(risk_group["attrition"].mean() * 100) \
                             if len(risk_group) else 0.0

    # ── Q10: Driver ranking — effect size = max − min attrition across groups ─
    driver_specs = [
        ("job_level",            "Job Level"),
        ("remote_work",          "Remote Work Policy"),
        ("number_of_promotions", "Career Growth"),
        ("work_life_balance",    "Work-Life Balance"),
        ("performance_rating",   "Performance Rating"),
        ("overtime",             "Overtime Load"),
    ]
    rows = []
    for col, label in driver_specs:
        if col in d.columns:
            rates = d.groupby(col, observed=True)["attrition"].mean().mul(100)
            rows.append({"Driver": label,
                         "Effect (pp)": round(float(rates.max() - rates.min()), 1)})
    q["driver_ranking"] = (
        pd.DataFrame(rows)
        .sort_values("Effect (pp)", ascending=True)
    )

    return q


# ─────────────────────────────────────────────────────────────────────────────
# FILTERED KPIs  (called on every sidebar interaction — O(m), m ≤ n)
# ─────────────────────────────────────────────────────────────────────────────
def filtered_kpis(df_filtered: pd.DataFrame) -> dict:
    n = len(df_filtered)
    if n == 0:
        return {"total": 0, "rate": 0.0, "avg_income": 0.0, "avg_tenure": 0.0}
    return {
        "total":      n,
        "rate":       float(df_filtered["attrition"].mean() * 100),
        "avg_income": float(df_filtered["monthly_income"].mean()),
        "avg_tenure": float(df_filtered["years_at_company"].mean()),
    }
