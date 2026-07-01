"""
ResumeRadar — Layer 2 Demo
Run: paste into a Jupyter notebook inside resumeradar/ folder
"""

import pandas as pd
from etl.data_processor import load_resumes, eda_summary, get_candidates_for_role
from models.resume import Resume
from models.candidate import Candidate
from models.scorer import Scorer

# --- Load & inspect ---
df = load_resumes("data/sample_resumes.csv")
eda_summary(df)

# --- Filter to ml_engineer and score using Layer 1 classes ---
role = "ml_engineer"
role_df = get_candidates_for_role(df, role)

scorer = Scorer(role=role)
candidates = []

for _, row in role_df.iterrows():
    raw_text = f"{row['years_experience']} years experience. skills: {row['skills_raw']}. "
    raw_text += "bachelor degree." if row["has_degree"] else ""
    resume = Resume(row["candidate_id"], raw_text, role).parse()
    candidates.append(Candidate(resume))

ranked = scorer.rank(candidates)

print(f"{'='*55}")
print(f"  Scored & Ranked — {role.replace('_', ' ').title()}")
print(f"{'='*55}")
for i, c in enumerate(ranked, 1):
    p = c.profile()
    flag = "✓" if p["shortlisted"] else "✗"
    print(f"{flag} #{i}  {p['candidate_id']}  score={p['score']}  exp={p['years_experience']}yrs  skills={len(p['skills'])}")
print(f"{'='*55}\n")
