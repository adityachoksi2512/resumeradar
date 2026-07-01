"""
ResumeRadar — Layer 2: Pandas
File: etl/data_processor.py
"""

import pandas as pd


def load_resumes(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df["skills_list"] = df["skills_raw"].str.split(", ")
    df["skill_count"] = df["skills_list"].apply(len)
    df["has_degree"] = df["has_degree"].astype(bool)
    return df


def eda_summary(df: pd.DataFrame) -> None:
    print(f"\n{'='*55}")
    print(f"  ResumeRadar — Resume Dataset EDA")
    print(f"{'='*55}")

    print(f"\nTotal candidates : {len(df)}")
    print(f"Roles            : {df['role_applied'].unique().tolist()}")
    print(f"Departments      : {df['department'].unique().tolist()}")

    print(f"\n--- Candidates per role ---")
    print(df["role_applied"].value_counts().to_string())

    print(f"\n--- Avg experience by role ---")
    print(df.groupby("role_applied")["years_experience"].mean().round(1).to_string())

    print(f"\n--- Degree holders by department ---")
    print(df.groupby("department")["has_degree"].sum().to_string())

    print(f"\n--- Avg skill count by role ---")
    print(df.groupby("role_applied")["skill_count"].mean().round(1).to_string())

    print(f"\n--- Top 10 most common skills ---")
    all_skills = df["skills_list"].explode()
    print(all_skills.value_counts().head(10).to_string())

    print(f"\n--- Experience distribution ---")
    bins = [0, 1, 3, 5, 10]
    labels = ["0-1 yr", "1-3 yrs", "3-5 yrs", "5+ yrs"]
    df["exp_band"] = pd.cut(df["years_experience"], bins=bins, labels=labels, right=False)
    print(df["exp_band"].value_counts().sort_index().to_string())

    print(f"\n{'='*55}\n")


def get_candidates_for_role(df: pd.DataFrame, role: str) -> pd.DataFrame:
    return df[df["role_applied"] == role].reset_index(drop=True)
