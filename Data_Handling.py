import pandas as pd
import numpy as np
import os

ORDINAL_MAPS = {
    "work_life_balance":   ["Poor", "Fair", "Good", "Excellent"],
    "job_satisfaction":    ["Low", "Medium", "High","Very High"],
    "performance_rating":  ["Low", "Below Average", "Average", "High"],
    "education_level":     ["High School", "Associate Degree", "Bachelor's Degree", "Master's Degree", "PhD"],
    "job_level":           ["Entry", "Mid", "Senior"],
    "company_size":        ["Small", "Medium", "Large"],
    "company_reputation":  ["Poor","Fair", "Good", "Excellent"],
    "employee_recognition":["Low", "Medium", "High","Very High"],
}

#loading data and concatinating
def load_and_clean(train:str,test:str)-> pd.DataFrame:

    train = pd.read_csv("train.csv")
    test= pd.read_csv("test.csv")
    df= pd.concat([train,test], ignore_index=True)

    #cleaning 
    df.columns = (
        df.columns
        .str.strip() 
        .str.lower() 
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    # remove duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"[clean] Removed {before - len(df)} duplicate rows")

    # let's handling wih null and categrious
    cols_numiric= df.select_dtypes(include="number").columns.tolist()
    cols_categorical= df.select_dtypes(include="object").columns.tolist()
    
    for col in cols_numiric:
        if df[col].isnull().any():
            df[col]=df[col].fillna(df[col].median())
    
    for col in cols_categorical:
        if df[col].isnull().any():
            mode_val = df[col].mode()[0]    # returns the most frequent value mode()
            df[col]  = df[col].fillna(mode_val)

    #cateforize [low,medium,high] so the code does't compare with them as plain text
    for col, order in ORDINAL_MAPS.items():
        if col in df.columns:
            df[col] = pd.Categorical(df[col], categories=order, ordered=True)
    # deals with attrition as 0/1 int
    df["attrition"] = df["attrition"].map({"Stayed": 0, "Left": 1})

 
    print(f"[clean] Final shape: {df.shape}")
    return df

def compute_aggregration(df: pd.DataFrame)-> dict:
    aggs={}

    aggs["overall_rate"]=df["attrition"].mean()
    aggs["total_employee"]=len(df)
    aggs["total_left"]=df["attrition"].sum()
    aggs["avg_income"] = df["monthly_income"].mean()

    #to assign rating to the exact option 
    for col in ["job_role", "gender", "marital_status", "job_level",
            "company_size", "education_level", "remote_work"]:
        if col in df.columns:
            aggs[f"rate_by_{col}"] = (                          #store results
                df.groupby(col, observed=True)["attrition"]
                .mean()
                .mul(100)               # percentage
                .round(1)
                .reset_index()           #back the grouped results to normal table 
                .rename(columns={"attrition": "attrition_rate_%"})
                .sort_values("attrition_rate_%", ascending=False)
            )
 
    #to assign rating to the level of the option
    for col in ["work_life_balance", "job_satisfaction",
                "performance_rating", "employee_recognition"]:
        if col in df.columns:
            aggs[f"rate_by_{col}"] = (
                df.groupby(col, observed=True)["attrition"]
                .mean()
                .mul(100)
                .round(1)
                .reset_index()
                .rename(columns={"attrition": "attrition_rate_%"})
                )

    aggs["income_by_attrition"] = (
        df.groupby("attrition", observed=True)["monthly_income"]
        .agg(["mean", "median"])
        .round(0)
        .reset_index()
    )
 
    aggs["age_col"] = df[["age", "attrition"]].copy()
 
    # Promotions vs attrition
    if "number_of_promotions" in df.columns:
        aggs["rate_by_promotions"] = (
            df.groupby("number_of_promotions", observed=True)["attrition"]
            .mean()
            .mul(100)
            .round(1)
            .reset_index()
            .rename(columns={"attrition": "attrition_rate_%"})
        )
 
    # heatmap
    num_cols = df.select_dtypes(include="number").columns.tolist()
    aggs["corr_matrix"] = df[num_cols].corr().round(2)
 
    return aggs
 
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
    
