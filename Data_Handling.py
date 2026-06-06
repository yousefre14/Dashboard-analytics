"""
data_utils.py — HR Attrition Analytics
Kayfa AI & Data Analytics Internship · Week 1

All data loading, cleaning, and aggregation logic lives here.
app.py imports functions — no raw pandas in the UI layer.

Performance principle:
  - Every operation is vectorized (C-level pandas internals, not Python loops)
  - Heavy groupby aggregations are computed ONCE at load time via compute_aggregations()
  - The UI layer only touches pre-built DataFrames — sub-millisecond on rerun
"""

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────────────────────
# ORDINAL MAPS  ← verified against the REAL CSV values
# WHY define here: single source of truth — change once, applies everywhere.
# Each list goes LOW → HIGH so pd.Categorical respects sort order.
# ─────────────────────────────────────────────────────────────────
ORDINAL_MAPS = {
    "work_life_balance":    ["Poor", "Fair", "Good", "Excellent"],
    "job_satisfaction":     ["Low", "Medium", "High", "Very High"],
    "performance_rating":   ["Low", "Below Average", "Average", "High"],
    "education_level":      ["High School", "Associate Degree", "Bachelor's Degree",
                             "Master's Degree", "PhD"],
    "job_level":            ["Entry", "Mid", "Senior"],
    "company_size":         ["Small", "Medium", "Large"],
    "company_reputation":   ["Poor", "Fair", "Good", "Excellent"],
    "employee_recognition": ["Low", "Medium", "High", "Very High"],
}


# ─────────────────────────────────────────────────────────────────
# STEP 1 + 2  ·  LOAD, COMBINE & CLEAN
# ─────────────────────────────────────────────────────────────────
def load_and_clean(train_path: str, test_path: str) -> pd.DataFrame:
    """
    Loads train.csv + test.csv, combines them, and returns a fully cleaned DataFrame.

    WHY combine? The train/test split is an ML artifact from Kaggle.
    For pure analytics we want every row — no information left out.

    Complexity notes (all vectorized, no Python-level loops):
      Column rename   → O(k)   k = number of columns, negligible
      Type casting    → O(n)   one pass per column
      Null filling    → O(n)   vectorized fillna
      Deduplication   → O(n)   hash-based in pandas C internals
    """

    # ── 1. Load & combine ─────────────────────────────────────────
    train = pd.read_csv(train_path)
    test  = pd.read_csv(test_path)
    df    = pd.concat([train, test], ignore_index=True)
    # ignore_index=True resets index 0..N — avoids duplicate-index confusion

    # ── 2. Normalize column names ──────────────────────────────────
    # Raw CSVs have "Monthly Income" (spaces, capitals).
    # We want "monthly_income" everywhere — no quoting, no KeyError surprises.
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    # ── 3. Drop exact duplicates ───────────────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    if dropped:
        print(f"[clean] Removed {dropped} duplicate rows")

    # ── 4. Handle nulls — vectorized, no Python row loop ──────────
    # Rule: numeric  → fill with median (robust to outliers)
    #       object   → fill with mode (most frequent value)
    # This dataset has zero nulls but the logic is correct for any real HR file.
    numeric_cols     = df.select_dtypes(include="number").columns
    categorical_cols = df.select_dtypes(include="object").columns

    for col in numeric_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    for col in categorical_cols:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].mode()[0])

    # ── 5. FIX: Encode attrition as integer 0 / 1 ─────────────────
    # The CSV stores "Stayed" / "Left" — NOT 0/1.
    # Without this, .mean() returns NaN and all KPIs silently break.
    df["attrition"] = df["attrition"].map({"Stayed": 0, "Left": 1}).astype(int)

    # ── 6. Cast ordinal columns to ordered Categorical ─────────────
    # WHY: without ordered=True, "Poor" < "Good" is undefined.
    # With it, pandas understands the hierarchy for groupby sort order.
    # Values verified against the REAL CSV — not the task-sheet descriptions.
    for col, order in ORDINAL_MAPS.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=order, ordered=True)

    print(f"[clean] Final shape: {df.shape} | Attrition rate: {df['attrition'].mean():.1%}")
    return df


# ─────────────────────────────────────────────────────────────────
# STEP 3  ·  PRE-COMPUTED AGGREGATIONS
#
# WHY here and not in app.py?
#   Streamlit reruns the entire script on every widget interaction.
#   If groupby calls lived in app.py they'd re-execute every click.
#   By computing them here (called inside @st.cache_data) they run
#   ONCE and the result is frozen in memory. UI interactions are O(1).
#
# All operations below are single-pass groupby → mean/agg: O(n) each.
# ─────────────────────────────────────────────────────────────────
def compute_aggregration(df: pd.DataFrame) -> dict:
    """
    Returns a dict of pre-built summary DataFrames.
    Function name matches your original import in app.py.
    """
    aggs = {}

    # ── Scalars ────────────────────────────────────────────────────
    # .mean() on a 0/1 column IS the attrition rate — one O(n) pass
    aggs["overall_rate"]    = df["attrition"].mean()
    aggs["total_employees"] = len(df)
    aggs["total_left"]      = int(df["attrition"].sum())
    aggs["avg_income"]      = df["monthly_income"].mean()

    # ── Attrition rate by categorical dimensions ───────────────────
    for col in ["job_role", "gender", "marital_status", "job_level",
                "company_size", "education_level", "remote_work",
                "overtime", "leadership_opportunities", "innovation_opportunities"]:
        if col in df.columns:
            aggs[f"rate_by_{col}"] = (
                df.groupby(col, observed=True)["attrition"]
                .mean().mul(100).round(1)
                .reset_index()
                .rename(columns={"attrition": "Attrition Rate (%)"})
                .sort_values("Attrition Rate (%)", ascending=False)
            )

    # ── Attrition rate by ordinal — preserve category sort order ───
    for col in ["work_life_balance", "job_satisfaction",
                "performance_rating", "employee_recognition",
                "company_reputation"]:
        if col in df.columns:
            aggs[f"rate_by_{col}"] = (
                df.groupby(col, observed=True)["attrition"]
                .mean().mul(100).round(1)
                .reset_index()
                .rename(columns={"attrition": "Attrition Rate (%)"})
                # NOTE: no sort_values — ordinal order is respected by groupby
            )

    # ── Promotions vs attrition ────────────────────────────────────
    if "number_of_promotions" in df.columns:
        aggs["rate_by_promotions"] = (
            df.groupby("number_of_promotions", observed=True)["attrition"]
            .mean().mul(100).round(1)
            .reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)"})
        )

    # ── Numeric correlation matrix ─────────────────────────────────
    num_cols = df.select_dtypes("number").columns.tolist()
    aggs["corr_matrix"] = df[num_cols].corr().round(2)

    return aggs


# ─────────────────────────────────────────────────────────────────
# FILTERED KPIs  ·  called on every sidebar interaction
# Runs on the FILTERED subset — O(m) where m ≤ n
# Scalar operations only — single-pass each.
# ─────────────────────────────────────────────────────────────────
def filtered_kpis(df_filtered: pd.DataFrame) -> dict:
    n = len(df_filtered)
    if n == 0:
        return {"total": 0, "rate": 0.0, "avg_income": 0.0, "avg_tenure": 0.0}
    return {
        "total":      n,
        "rate":       df_filtered["attrition"].mean() * 100,
        "avg_income": df_filtered["monthly_income"].mean(),
        "avg_tenure": df_filtered["years_at_company"].mean(),
    }
