"""
ResumeRadar — Layer 1: OOP
File: models/candidate.py

A Candidate wraps a Resume and adds a score after screening.
Demonstrates inheritance — SeniorCandidate overrides the scoring bonus.
"""

from models.resume import Resume


class Candidate:
    def __init__(self, resume: Resume):
        self.resume = resume
        self._score: float | None = None    # private until set by Scorer
        self.shortlisted: bool = False

    def set_score(self, score: float):
        """Called by Scorer — stores the result."""
        if not (0.0 <= score <= 100.0):
            raise ValueError(f"Score must be between 0 and 100, got {score}")
        self._score = score
        self.shortlisted = score >= self._threshold()

    def _threshold(self) -> float:
        """Private — subclasses can override the shortlist cutoff."""
        return 60.0

    @property
    def score(self) -> float:
        if self._score is None:
            raise RuntimeError("Candidate has not been scored yet.")
        return self._score

    def profile(self) -> dict:
        """Public — full candidate profile including score."""
        summary = self.resume.summary()
        return {
            "candidate_id": str(summary["candidate_id"]),
            "role_applied": str(summary["role_applied"]),
            "skills": list(summary["skills"]),
            "years_experience": int(summary["years_experience"]),
            "has_degree": bool(summary["has_degree"]),
            "score": float(round(self._score, 2)) if self._score is not None else None,
            "shortlisted": bool(self.shortlisted),
            "level": self._level(),
        }

    def _level(self) -> str:
        return "standard"

    def __repr__(self):
        return f"Candidate(id={self.resume.candidate_id}, score={self._score})"


class SeniorCandidate(Candidate):
    """
    Senior roles have a lower shortlist threshold —
    we cast a wider net since fewer candidates apply.
    Demonstrates inheritance + method override.
    """

    def _threshold(self) -> float:
        return 50.0

    def _level(self) -> str:
        return "senior"
