"""
ResumeRadar — Layer 1 Demo
Run: python demo_oop.py

Creates 3 sample candidates, scores them for the ml_engineer role,
and prints a ranked shortlist.
"""

from models.resume import Resume
from models.candidate import Candidate, SeniorCandidate
from models.scorer import Scorer

# --- Sample resume texts (simplified) ---
resumes_raw = [
    {
        "id": "C001",
        "role": "ml_engineer",
        "text": """
            Senior ML Engineer with 6 years experience in python, machine learning,
            deep learning, docker, and gcp. Master's degree in Computer Science.
            Built end-to-end pipelines on AWS and GCP.
        """,
        "senior": True,
    },
    {
        "id": "C002",
        "role": "ml_engineer",
        "text": """
            Data scientist with 2 years experience. Proficient in python and sql.
            Bachelor's degree in Statistics. Some exposure to tensorflow.
        """,
        "senior": False,
    },
    {
        "id": "C003",
        "role": "ml_engineer",
        "text": """
            ML Engineer, 4 years experience. Skills: python, machine learning,
            docker, kubernetes, pytorch. No formal degree — self-taught.
        """,
        "senior": False,
    },
]

# --- Build, parse, and score ---
scorer = Scorer(role="ml_engineer")
candidates = []

for r in resumes_raw:
    resume = Resume(r["id"], r["text"], r["role"]).parse()
    candidate = SeniorCandidate(resume) if r["senior"] else Candidate(resume)
    candidates.append(candidate)

ranked = scorer.rank(candidates)

# --- Print results ---
print(f"\n{'='*55}")
print(f"  ResumeRadar — ML Engineer Shortlist")
print(f"{'='*55}")
for i, c in enumerate(ranked, 1):
    p = c.profile()
    flag = "✓ SHORTLISTED" if p["shortlisted"] else "✗ not shortlisted"
    print(f"\n#{i}  {p['candidate_id']}  [{p['level']}]  {flag}")
    print(f"    Score      : {p['score']}")
    print(f"    Skills     : {', '.join(p['skills']) or 'none matched'}")
    print(f"    Experience : {p['years_experience']} yrs")
    print(f"    Degree     : {'yes' if p['has_degree'] else 'no'}")
print(f"\n{'='*55}\n")
