"""
ResumeRadar — Layer 4 Demo
Run: paste into a Jupyter notebook inside resumeradar/ folder

Shows the difference between:
  - Sequential parsing  (one by one, with simulated I/O delay)
  - Async parsing       (all at once with asyncio.gather)
  - Parallel scoring    (ThreadPoolExecutor across workers)
"""

import asyncio
import time
from models.resume import Resume
from models.candidate import Candidate
from core.async_parser import parse_all_resumes
from core.parallel_scorer import score_all_parallel

# --- Sample inputs ---
resume_inputs = [
    {"candidate_id": "C001", "role": "ml_engineer",
     "text": "6 years experience. python, machine learning, docker, gcp. Master degree."},
    {"candidate_id": "C002", "role": "ml_engineer",
     "text": "2 years experience. python, sql. Bachelor degree."},
    {"candidate_id": "C003", "role": "ml_engineer",
     "text": "4 years experience. python, machine learning, docker, kubernetes, pytorch."},
    {"candidate_id": "C004", "role": "ml_engineer",
     "text": "7 years experience. python, machine learning, gcp, docker, spark, scala. Master degree."},
    {"candidate_id": "C005", "role": "ml_engineer",
     "text": "3 years experience. python, machine learning, aws. Bachelor degree."},
]

# ─────────────────────────────────────────────
# 1. Sequential parsing (simulates I/O delay per resume)
# ─────────────────────────────────────────────
print("\n--- Sequential parsing (0.1s I/O delay per resume) ---")
start = time.time()
sequential_resumes = []
for r in resume_inputs:
    time.sleep(0.1)   # simulate reading from disk / PDF parser
    sequential_resumes.append(Resume(r["candidate_id"], r["text"], r["role"]).parse())
seq_time = time.time() - start
print(f"Parsed {len(sequential_resumes)} resumes in {seq_time:.2f}s")

# ─────────────────────────────────────────────
# 2. Async parsing (all resumes parsed concurrently)
# ─────────────────────────────────────────────
print("\n--- Async parsing (asyncio.gather — all concurrent) ---")
start = time.time()
async_resumes = asyncio.run(parse_all_resumes(resume_inputs))
async_time = time.time() - start
print(f"Parsed {len(async_resumes)} resumes in {async_time:.2f}s")
print(f"Speedup: {seq_time / async_time:.1f}x faster than sequential")

# ─────────────────────────────────────────────
# 3. Parallel scoring (ThreadPoolExecutor)
# ─────────────────────────────────────────────
print("\n--- Parallel scoring (ThreadPoolExecutor, 4 workers) ---")
candidates = [Candidate(r) for r in async_resumes]

start = time.time()
ranked = score_all_parallel(candidates, role="ml_engineer", max_workers=4)
par_time = time.time() - start
print(f"Scored {len(ranked)} candidates in {par_time:.4f}s across 4 workers")

# ─────────────────────────────────────────────
# 4. Results
# ─────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  Ranked Shortlist")
print(f"{'='*55}")
for i, c in enumerate(ranked, 1):
    p = c.profile()
    flag = "✓ SHORTLISTED" if p["shortlisted"] else "✗ not shortlisted"
    print(f"#{i}  {p['candidate_id']}  score={p['score']}  {flag}")
print(f"{'='*55}\n")
