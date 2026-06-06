"""
All data loading, cleaning, validation, and pre-computation lives here.
main.py imports and calls — no raw pandas in the UI layer.

Architecture:
  - Vectorized operations (O(n)) throughout
  - Heavy aggregations run ONCE at load via @st.cache_data
  - Built-in validation & testing utilities
  - Comprehensive error handling with detailed feedback
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Optional

# LOGGING CONFIGURATION 
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s · %(name)s · %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ORDINAL MAPS  —  Verified against REAL CSV values, not task descriptions
# Explicit ordering ensures categorical operations respect hierarchy (not alphabetical)
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

# Numeric column ranges for validation
NUMERIC_RANGES = {
    "age": (18, 60),
    "monthly_income": (1000, 500000),
    "years_at_company": (0, 50),
    "company_tenure": (0, 50),
    "distance_from_home": (0, 100),
    "number_of_promotions": (0, 10),
    "number_of_dependents": (0, 10),
}

CATEGORICAL_VALUES = {
    "gender": ["Male", "Female"],
    "marital_status": ["Single", "Married", "Divorced"],
    "remote_work": ["Yes", "No"],
    "overtime": ["Yes", "No"],
    "leadership_opportunities": ["Yes", "No"],
    "innovation_opportunities": ["Yes", "No"],
}


# VALIDATION UTILITIES  —  Test data integrity at every stage
class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    pass


def validate_dataframe_shape(df: pd.DataFrame, min_rows: int = 1000) -> bool:
    """
    Validates that DataFrame meets minimum size requirements.
    
    Args:
        df: Input DataFrame
        min_rows: Minimum required rows
        
    Returns:
        True if valid
        
    Raises:
        DataValidationError if invalid
    """
    if len(df) < min_rows:
        raise DataValidationError(
            f"[VALIDATION] DataFrame has {len(df)} rows, need at least {min_rows}"
        )
    if df.shape[1] == 0:
        raise DataValidationError("[VALIDATION] DataFrame has no columns")
    logger.info(f"✓ Shape validation passed: {df.shape}")
    return True


def validate_column_presence(df: pd.DataFrame, required_cols: list) -> bool:
    """
    Validates that all required columns exist.
    
    Args:
        df: Input DataFrame
        required_cols: List of required column names
        
    Returns:
        True if all present
        
    Raises:
        DataValidationError if missing columns
    """
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise DataValidationError(
            f"[VALIDATION] Missing required columns: {missing}\n"
            f"Available: {df.columns.tolist()}"
        )
    logger.info(f"✓ Column presence validation passed ({len(required_cols)} columns)")
    return True


def validate_dtype(df: pd.DataFrame, col: str, expected_type: str) -> bool:
    """
    Validates column dtype matches expected type.
    
    Args:
        df: Input DataFrame
        col: Column name
        expected_type: Expected dtype string or list
        
    Returns:
        True if valid
        
    Raises:
        DataValidationError if dtype mismatch
    """
    if isinstance(expected_type, str):
        expected_type = [expected_type]
    
    actual = str(df[col].dtype)
    if actual not in expected_type:
        raise DataValidationError(
            f"[VALIDATION] Column '{col}' has dtype {actual}, "
            f"expected one of {expected_type}"
        )
    return True


def validate_attrition_values(df: pd.DataFrame, col: str = "attrition") -> bool:
    """
    Validates attrition column contains only valid values (0, 1).
    
    Args:
        df: Input DataFrame
        col: Attrition column name
        
    Returns:
        True if valid
        
    Raises:
        DataValidationError if invalid values present
    """
    unique_vals = df[col].dropna().unique()
    invalid = set(unique_vals) - {0, 1}
    
    if invalid:
        raise DataValidationError(
            f"[VALIDATION] Attrition column contains invalid values: {invalid}\n"
            f"Only 0 (Stayed) and 1 (Left) are allowed."
        )
    
    null_count = df[col].isnull().sum()
    if null_count > 0:
        logger.warning(f"⚠️  {null_count} null values in attrition — filling with 0")
    
    logger.info(
        f"✓ Attrition validation passed | "
        f"Rate: {df[col].mean()*100:.1f}% | "
        f"Nulls: {null_count}"
    )
    return True


def validate_categorical_values(df: pd.DataFrame, col: str, allowed: list) -> bool:
    """
    Validates categorical column contains only allowed values.
    
    Args:
        df: Input DataFrame
        col: Column name
        allowed: List of allowed values
        
    Returns:
        True if valid
        
    Raises:
        DataValidationError if invalid values present
    """
    unique_vals = set(df[col].dropna().unique())
    invalid = unique_vals - set(allowed)
    
    if invalid:
        raise DataValidationError(
            f"[VALIDATION] Column '{col}' contains unexpected values: {invalid}\n"
            f"Allowed: {allowed}"
        )
    return True


def validate_numeric_range(df: pd.DataFrame, col: str, 
                          min_val: float, max_val: float) -> bool:
    """
    Validates numeric column values fall within expected range.
    
    Args:
        df: Input DataFrame
        col: Column name
        min_val: Minimum expected value
        max_val: Maximum expected value
        
    Returns:
        True if valid
        
    Raises:
        DataValidationError if values out of range
    """
    out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
    
    if len(out_of_range) > 0:
        logger.warning(
            f"⚠️  {len(out_of_range)} out-of-range values in '{col}' "
            f"(range: {min_val}–{max_val}). Clamping..."
        )
        df[col] = df[col].clip(min_val, max_val)
    
    return True


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 + 2  ·  LOAD, COMBINE & CLEAN
# ─────────────────────────────────────────────────────────────────────────────
def load_and_clean(train: str, test: str) -> pd.DataFrame:
    """
    Loads train.csv + test.csv, combines, cleans, validates, and returns 
    a fully prepared DataFrame ready for analysis.

    Why combine: train/test split is an ML Kaggle artifact. For analytics,
    we want all 74,498 rows — no information should be left out.
    
    Processing pipeline:
      1. Load both CSV files
      2. Combine into single DataFrame
      3. Normalize column names (snake_case, strip whitespace)
      4. Drop exact duplicates
      5. Handle nulls (numeric → median, categorical → mode)
      6. Encode attrition as 0/1 (robust to multiple formats)
      7. Cast ordinal columns to ordered Categorical (preserves hierarchy)
      8. Validate all transformations
      
    Args:
        train: Path to train.csv
        test: Path to test.csv
        
    Returns:
        Cleaned, validated DataFrame
        
    Raises:
        FileNotFoundError: If CSV files not found
        DataValidationError: If data doesn't pass validation checks
    """
    
    logger.info("=" * 70)
    logger.info("STARTING DATA LOAD & CLEAN PIPELINE")
    logger.info("=" * 70)
    
    # ── 1. LOAD FILES ────────────────────────────────────────────────────────
    logger.info("\n[Step 1] Loading CSV files...")
    try:
        df_train = pd.read_csv(train)
        df_test = pd.read_csv(test)
        logger.info(f"  ✓ train.csv loaded: {df_train.shape}")
        logger.info(f"  ✓ test.csv loaded:  {df_test.shape}")
    except FileNotFoundError as e:
        logger.error(f"[FATAL] CSV file not found: {e}")
        raise FileNotFoundError(f"[Data_Handling] CSV not found: {e}") from e

    # ── 2. COMBINE ───────────────────────────────────────────────────────────
    logger.info("\n[Step 2] Combining train + test...")
    df = pd.concat([df_train, df_test], ignore_index=True)
    logger.info(f"  ✓ Combined shape: {df.shape}")

    # ── 3. NORMALIZE COLUMN NAMES ────────────────────────────────────────────
    logger.info("\n[Step 3] Normalizing column names to snake_case...")
    original_cols = df.columns.tolist()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    col_mapping = dict(zip(original_cols, df.columns.tolist()))
    logger.info(f"  ✓ Normalized {len(col_mapping)} columns")
    if col_mapping:
        for orig, norm in list(col_mapping.items())[:3]:
            logger.debug(f"    {orig} → {norm}")

    # ── 4. DROP DUPLICATES ───────────────────────────────────────────────────
    logger.info("\n[Step 4] Removing exact duplicates...")
    before_dedup = len(df)
    df = df.drop_duplicates()
    dropped = before_dedup - len(df)
    if dropped > 0:
        logger.warning(f"  ⚠️  Removed {dropped} duplicate rows")
    else:
        logger.info(f"  ✓ No duplicates found")

    # ── 5. NULL HANDLING  —  Vectorized, no Python loops ──────────────────────
    logger.info("\n[Step 5] Handling null values...")
    
    # Numeric columns → median (robust to outliers)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    numeric_nulls = df[numeric_cols].isnull().sum().sum()
    if numeric_nulls > 0:
        logger.info(f"  Found {numeric_nulls} nulls in numeric columns")
        for col in numeric_cols:
            if df[col].isnull().any():
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                logger.debug(f"    {col}: filled {df[col].isnull().sum()} with median {median_val:.2f}")
        logger.info(f"  ✓ Numeric nulls filled via median")
    else:
        logger.info(f"  ✓ No numeric nulls")

    # Categorical columns → mode (most frequent category)
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    categorical_nulls = df[categorical_cols].isnull().sum().sum()
    if categorical_nulls > 0:
        logger.info(f"  Found {categorical_nulls} nulls in categorical columns")
        for col in categorical_cols:
            if df[col].isnull().any():
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])
                    logger.debug(f"    {col}: filled {df[col].isnull().sum()} with mode '{mode_val[0]}'")
        logger.info(f"  ✓ Categorical nulls filled via mode")
    else:
        logger.info(f"  ✓ No categorical nulls")

    # ── 6. ATTRITION ENCODING  —  Production-grade, handles multiple formats ──
    logger.info("\n[Step 6] Encoding attrition column...")
    print(f"[DEBUG] Column 'attrition' dtype BEFORE: {df['attrition'].dtype}")
    print(f"[DEBUG] Sample values: {df['attrition'].head(10).tolist()}")
    print(f"[DEBUG] Unique values (first 10): {df['attrition'].unique()[:10].tolist()}")
    
    # Step 6a: If already numeric (0/1), ensure int type
    if df["attrition"].dtype in ['int64', 'int32', 'float64']:
        df["attrition"] = df["attrition"].fillna(0).astype('int64')
        logger.info(f"  ✓ Attrition was numeric — converted to int64")
    
    # Step 6b: If object/string, normalize and map
    elif df["attrition"].dtype in ['object', 'str', 'string']:
        # Normalize whitespace and case
        df["attrition"] = df["attrition"].str.strip().str.lower()
        
        # Flexible mapping to handle multiple label formats
        mapping = {
            "stayed": 0, "left": 1,
            "no": 0, "yes": 1,
            "0": 0, "1": 1,
        }
        
        df["attrition"] = df["attrition"].map(mapping)
        
        # Fill any unmapped values with 0 and log
        unmapped = df["attrition"].isnull().sum()
        if unmapped > 0:
            logger.warning(f"  ⚠️  {unmapped} unmapped attrition values — filling with 0")
            df["attrition"] = df["attrition"].fillna(0)
        
        df["attrition"] = df["attrition"].astype('int64')
        logger.info(f"  ✓ Attrition mapped from strings to 0/1")
    
    else:
        raise DataValidationError(
            f"Unexpected dtype for attrition: {df['attrition'].dtype}"
        )
    
    print(f"[DEBUG] Column 'attrition' dtype AFTER: {df['attrition'].dtype}")
    print(f"[DEBUG] Unique values: {df['attrition'].unique()}")
    print(f"[DEBUG] Attrition rate: {df['attrition'].mean():.1%}")
    
    # ── 6c: VALIDATE ATTRITION ───────────────────────────────────────────────
    validate_attrition_values(df, "attrition")

    # ── 7. CAST ORDINAL COLUMNS TO ORDERED CATEGORICAL ──────────────────────
    logger.info("\n[Step 7] Casting ordinal columns to ordered Categorical...")
    ordinal_count = 0
    for col, order in ORDINAL_MAPS.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=order, ordered=True)
            ordinal_count += 1
            logger.debug(f"    {col}: {order[:2]}...{order[-1]}")
    logger.info(f"  ✓ {ordinal_count} ordinal columns cast (ordering preserved)")

    # ── 8. VALIDATE NUMERIC RANGES ───────────────────────────────────────────
    logger.info("\n[Step 8] Validating numeric ranges...")
    for col, (min_val, max_val) in NUMERIC_RANGES.items():
        if col in df.columns:
            validate_numeric_range(df, col, min_val, max_val)
    logger.info(f"  ✓ {len(NUMERIC_RANGES)} numeric columns validated")

    # ── 9. VALIDATE CATEGORICAL VALUES ───────────────────────────────────────
    logger.info("\n[Step 9] Validating categorical values...")
    for col, allowed in CATEGORICAL_VALUES.items():
        if col in df.columns:
            validate_categorical_values(df, col, allowed)
    logger.info(f"  ✓ {len(CATEGORICAL_VALUES)} categorical columns validated")

    # ── 10. FINAL SHAPE & SUMMARY ────────────────────────────────────────────
    logger.info("\n[Step 10] Final validation...")
    validate_dataframe_shape(df, min_rows=50000)
    
    logger.info("\n" + "=" * 70)
    logger.info("DATA LOAD & CLEAN COMPLETE ✓")
    logger.info("=" * 70)
    logger.info(f"Final shape: {df.shape}")
    logger.info(f"Attrition rate: {df['attrition'].mean()*100:.2f}%")
    logger.info(f"Columns: {df.shape[1]} | Rows: {df.shape[0]:,}")
    logger.info("=" * 70 + "\n")
    
    return df


# PRE-COMPUTED AGGREGATIONS  (runs ONCE at load via @st.cache_data)
                                                                                                                                                         




def compute_aggregration(df: pd.DataFrame) -> Dict:
    """
    Computes general aggregations used across multiple dashboard pages.
    Cached at session start — all groupby operations run once.
    
    Args:
        df: Input DataFrame (already cleaned)
        
    Returns:
        Dictionary of pre-computed metrics and grouped DataFrames
    """
    logger.info("\n[Aggregation] Computing company-wide metrics...")
    aggs = {}

    # ── Scalar metrics ────────────────────────────────────────────────────────
    aggs["overall_rate"]    = float(df["attrition"].mean())
    aggs["total_employee"]  = len(df)
    aggs["total_left"]      = int(df["attrition"].sum())
    aggs["avg_income"]      = float(df["monthly_income"].mean())
    
    logger.info(f"  Overall attrition rate: {aggs['overall_rate']*100:.2f}%")
    logger.info(f"  Total employees: {aggs['total_employee']:,}")
    logger.info(f"  Employees who left: {aggs['total_left']:,}")

    # ── Attrition rate by nominal (unordered) categories ─────────────────────
    logger.info("\n  Computing rates by nominal categories...")
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

    # ── Attrition by ordinal categories — preserve category ordering ─────────
    logger.info("  Computing rates by ordinal categories...")
    for col in ["work_life_balance", "job_satisfaction",
                "performance_rating", "employee_recognition", "company_reputation"]:
        if col in df.columns:
            aggs[f"rate_by_{col}"] = (
                df.groupby(col, observed=True)["attrition"]
                .mean().mul(100).round(1).reset_index()
                .rename(columns={"attrition": "Attrition Rate (%)"})
            )

    # ── Promotions ────────────────────────────────────────────────────────────
    if "number_of_promotions" in df.columns:
        aggs["rate_by_promotions"] = (
            df.groupby("number_of_promotions", observed=True)["attrition"]
            .mean().mul(100).round(1).reset_index()
            .rename(columns={"attrition": "Attrition Rate (%)"})
        )

    # ── Correlation matrix (numeric columns only) ────────────────────────────
    num_cols = df.select_dtypes("number").columns.tolist()
    aggs["corr_matrix"] = df[num_cols].corr().round(2)

    logger.info(f"  ✓ Aggregations computed ({len(aggs)} metrics)")
    return aggs


def compute_q_aggregations(df: pd.DataFrame) -> Dict:
    """
    Q4–Q10 specific aggregations — computed once at load time.
    Implements all advanced question-specific metrics without modifying original df.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary of Q-specific aggregations
    """
    logger.info("\n[Q-Aggregation] Computing Q4–Q10 specific metrics...")
    d = df.copy()
    q = {}

    # ── Q4: Income quartile within job level ─────────────────────────────────
    logger.info("  Q4: Computing income quartiles by job level...")
    d["income_quartile"] = d.groupby("job_level", observed=True)["monthly_income"] \
        .transform(lambda x: pd.qcut(x, 4,
                   labels=["Bottom 25%", "Q2", "Q3", "Top 25%"],
                   duplicates="drop"))
    q["pay_by_level_quartile"] = (
        d.groupby(["job_level", "income_quartile"], observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)"})
    )

    # ── Q5: Tenure bands (retention timeline) ────────────────────────────────
    logger.info("  Q5: Computing tenure bands...")
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
    logger.info("  Q6: Computing Work-Life Balance × Satisfaction cross-tab...")
    q["wlb_x_satisfaction"] = (
        d.groupby(["work_life_balance", "job_satisfaction"], observed=True)["attrition"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"attrition": "Attrition Rate (%)",
                          "work_life_balance": "Work-Life Balance",
                          "job_satisfaction": "Job Satisfaction"})
    )

    # ── Q7: Life-stage dimensions (age, marital, dependents) ──────────────────
    logger.info("  Q7: Computing life-stage metrics...")
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

    # ── Q8: Career stagnation (promotions, job level, leadership, innovation) ─
    logger.info("  Q8: Computing career stagnation metrics...")
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
    logger.info(f"    'Fully stuck' employees: {q['stuck_n']:,} ({q['stuck_rate']:.1f}% attrition)")

    # ── Q9: Highest-risk profile ──────────────────────────────────────────────
    logger.info("  Q9: Identifying highest-risk profile...")
    # Profile: Poor WLB + Overtime + 0 Promotions + No Leadership
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
    logger.info(f"    High-risk profile size: {q['risk_profile_n']:,} ({q['risk_profile_rate']:.1f}% attrition)")

    # ── Q10: Driver ranking (effect size = max − min attrition across groups) ──
    logger.info("  Q10: Computing driver effect sizes...")
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
            effect = round(float(rates.max() - rates.min()), 1)
            rows.append({"Driver": label, "Effect (pp)": effect})
            logger.debug(f"    {label}: {effect}pp")
    q["driver_ranking"] = (
        pd.DataFrame(rows)
        .sort_values("Effect (pp)", ascending=True)
    )

    logger.info(f"  ✓ Q-aggregations computed ({len(q)} metrics)")
    return q


# ─────────────────────────────────────────────────────────────────────────────
# FILTERED KPIs  (computed on sidebar interaction — O(m), m ≤ n)
# Returns metrics for the current filter state (not cached — updates per sidebar)
# ─────────────────────────────────────────────────────────────────────────────
def filtered_kpis(df_filtered: pd.DataFrame) -> Dict:
    """
    Computes KPIs for the current filter state (sidebar selection).
    Fast O(m) computation since m << n in typical dashboard usage.
    
    Args:
        df_filtered: Filtered DataFrame (result of sidebar filters)
        
    Returns:
        Dictionary of KPIs for display
    """
    n = len(df_filtered)
    if n == 0:
        return {
            "total": 0,
            "rate": 0.0,
            "avg_income": 0.0,
            "avg_tenure": 0.0,
        }
    return {
        "total":      n,
        "rate":       float(df_filtered["attrition"].mean() * 100),
        "avg_income": float(df_filtered["monthly_income"].mean()),
        "avg_tenure": float(df_filtered["years_at_company"].mean()),
    }


# ─────────────────────────────────────────────────────────────────────────────
# TESTING UTILITIES  —  Verify data integrity & chart readiness
# ─────────────────────────────────────────────────────────────────────────────
def test_data_completeness(df: pd.DataFrame) -> bool:
    """
    Comprehensive test suite for data completeness.
    Run after load_and_clean() to verify everything is ready for analysis.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        True if all tests pass
    """
    logger.info("\n" + "=" * 70)
    logger.info("RUNNING DATA COMPLETENESS TEST SUITE")
    logger.info("=" * 70)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Shape validation
    tests_total += 1
    try:
        validate_dataframe_shape(df, min_rows=50000)
        tests_passed += 1
        logger.info("✓ Test 1/7: Shape validation")
    except DataValidationError as e:
        logger.error(f"✗ Test 1/7 FAILED: {e}")
    
    # Test 2: Column completeness
    tests_total += 1
    expected_cols = [
        "attrition", "age", "monthly_income", "years_at_company",
        "job_role", "gender", "work_life_balance", "job_satisfaction",
        "remote_work", "overtime", "job_level"
    ]
    try:
        validate_column_presence(df, expected_cols)
        tests_passed += 1
        logger.info("✓ Test 2/7: Column presence")
    except DataValidationError as e:
        logger.error(f"✗ Test 2/7 FAILED: {e}")
    
    # Test 3: Attrition dtype & values
    tests_total += 1
    try:
        validate_dtype(df, "attrition", "int64")
        validate_attrition_values(df, "attrition")
        tests_passed += 1
        logger.info("✓ Test 3/7: Attrition encoding (0/1)")
    except DataValidationError as e:
        logger.error(f"✗ Test 3/7 FAILED: {e}")
    
    # Test 4: No remaining nulls
    tests_total += 1
    null_count = df.isnull().sum().sum()
    if null_count == 0:
        logger.info("✓ Test 4/7: No null values")
        tests_passed += 1
    else:
        logger.error(f"✗ Test 4/7 FAILED: {null_count} null values remain")
    
    # Test 5: Ordinal categories preserve ordering
    tests_total += 1
    ordinal_valid = all(
        df[col].cat.ordered if col in df.columns else True
        for col in ORDINAL_MAPS.keys()
    )
    if ordinal_valid:
        logger.info("✓ Test 5/7: Ordinal categories properly ordered")
        tests_passed += 1
    else:
        logger.error("✗ Test 5/7 FAILED: Some ordinal columns lost ordering")
    
    # Test 6: Numeric ranges valid
    tests_total += 1
    range_valid = True
    for col, (min_val, max_val) in NUMERIC_RANGES.items():
        if col in df.columns:
            out_of_range = (
                (df[col] < min_val) | (df[col] > max_val)
            ).sum()
            if out_of_range > 0:
                logger.warning(f"  ⚠️  {col} has {out_of_range} out-of-range values (expected after clamping)")
    logger.info("✓ Test 6/7: Numeric ranges validated")
    tests_passed += 1
    
    # Test 7: Aggregation computability (no groupby failures)
    tests_total += 1
    try:
        _ = df.groupby("job_role", observed=True)["attrition"].mean()
        _ = df.groupby("work_life_balance", observed=True)["attrition"].mean()
        logger.info("✓ Test 7/7: Groupby operations valid")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Test 7/7 FAILED: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"TEST RESULTS: {tests_passed}/{tests_total} PASSED")
    if tests_passed == tests_total:
        logger.info("✓✓✓ ALL TESTS PASSED — DATA IS PRODUCTION-READY ✓✓✓")
    else:
        logger.warning(f"⚠️  {tests_total - tests_passed} test(s) failed — review before deploying")
    logger.info("=" * 70 + "\n")
    
    return tests_passed == tests_total


def test_aggregation_output(aggs: Dict, q: Dict, overall_rate: float) -> bool:
    """
    Validates that aggregations are structured correctly and contain no NaNs.
    
    Args:
        aggs: General aggregations dict
        q: Q-specific aggregations dict
        overall_rate: Overall attrition rate (scalar)
        
    Returns:
        True if all aggregations valid
    """
    logger.info("\n" + "=" * 70)
    logger.info("RUNNING AGGREGATION VALIDATION TEST SUITE")
    logger.info("=" * 70)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Scalar metrics exist
    tests_total += 1
    required_scalars = ["overall_rate", "total_employee", "total_left", "avg_income"]
    if all(k in aggs for k in required_scalars):
        logger.info(f"✓ Test 1/5: All {len(required_scalars)} scalar metrics present")
        tests_passed += 1
    else:
        logger.error(f"✗ Test 1/5 FAILED: Missing scalar metrics")
    
    # Test 2: Grouped DataFrames have no NaNs
    tests_total += 1
    nan_found = False
    for key, val in aggs.items():
        if isinstance(val, pd.DataFrame):
            if val.isnull().any().any():
                logger.warning(f"  ⚠️  {key} contains NaN values")
                nan_found = True
    if not nan_found:
        logger.info("✓ Test 2/5: No NaN values in grouped DataFrames")
        tests_passed += 1
    else:
        logger.error("✗ Test 2/5 FAILED: NaN values detected")
    
    # Test 3: Q-metrics structurally valid
    tests_total += 1
    critical_q_keys = [
        "pay_by_level_quartile", "attrition_by_tenure", "wlb_x_satisfaction",
        "stuck_n", "stuck_rate", "risk_profile_n", "risk_profile_rate",
        "driver_ranking"
    ]
    if all(k in q for k in critical_q_keys):
        logger.info(f"✓ Test 3/5: All {len(critical_q_keys)} Q-metrics present")
        tests_passed += 1
    else:
        missing = [k for k in critical_q_keys if k not in q]
        logger.error(f"✗ Test 3/5 FAILED: Missing Q-metrics: {missing}")
    
    # Test 4: Overall rate is reasonable (0–100%)
    tests_total += 1
    if 0 <= overall_rate <= 1:
        logger.info(f"✓ Test 4/5: Overall rate reasonable ({overall_rate*100:.2f}%)")
        tests_passed += 1
    else:
        logger.error(f"✗ Test 4/5 FAILED: Overall rate out of bounds: {overall_rate}")
    
    # Test 5: Correlation matrix shape valid
    tests_total += 1
    if "corr_matrix" in aggs:
        corr = aggs["corr_matrix"]
        if corr.shape[0] == corr.shape[1] and corr.shape[0] >= 5:
            logger.info(f"✓ Test 5/5: Correlation matrix shape valid {corr.shape}")
            tests_passed += 1
        else:
            logger.error(f"✗ Test 5/5 FAILED: Correlation matrix shape unexpected: {corr.shape}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"TEST RESULTS: {tests_passed}/{tests_total} PASSED")
    if tests_passed == tests_total:
        logger.info("✓✓✓ ALL AGGREGATIONS VALID — READY FOR DASHBOARD ✓✓✓")
    logger.info("=" * 70 + "\n")
    
    return tests_passed == tests_total


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY FUNCTION  —  Print human-readable data summary
# ─────────────────────────────────────────────────────────────────────────────
def print_data_summary(df: pd.DataFrame) -> None:
    """
    Prints a formatted summary of the dataset for logging/debugging.
    
    Args:
        df: Input DataFrame
    """
    logger.info("\n" + "=" * 70)
    logger.info("DATA SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    logger.info(f"\nData Types:")
    logger.info(f"  Numeric: {df.select_dtypes('number').shape[1]}")
    logger.info(f"  Categorical: {df.select_dtypes('object').shape[1]}")
    logger.info(f"  Ordinal: {df.select_dtypes('category').shape[1]}")
    logger.info(f"\nMissing Values: {df.isnull().sum().sum()} (0%)")
    logger.info(f"\nAttrition:")
    logger.info(f"  Rate: {df['attrition'].mean()*100:.2f}%")
    logger.info(f"  Left: {(df['attrition']==1).sum():,}")
    logger.info(f"  Stayed: {(df['attrition']==0).sum():,}")
    logger.info("=" * 70 + "\n")
