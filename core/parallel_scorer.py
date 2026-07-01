"""
ResumeRadar — Layer 4: Parallel Processing
File: core/parallel_scorer.py

Demonstrates multiprocessing — scores candidates across
multiple CPU cores simultaneously. Useful when scoring
logic is CPU-bound (e.g. running an ML model per candidate).
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from models.candidate import Candidate
from models.scorer import Scorer


def score_one(candidate: Candidate, role: str) -> Candidate:
    """Score a single candidate — runs in its own thread."""
    scorer = Scorer(role=role)
    return scorer.score(candidate)


def score_all_parallel(candidates: list[Candidate], role: str, max_workers: int = 4) -> list[Candidate]:
    """
    Score all candidates in parallel using ThreadPoolExecutor.
    Returns candidates sorted by score descending.
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(score_one, c, role): c
            for c in candidates
        }
        for future in as_completed(futures):
            results.append(future.result())

    return sorted(results, key=lambda c: c.score, reverse=True)
