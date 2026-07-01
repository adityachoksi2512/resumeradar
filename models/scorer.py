"""
ResumeRadar — Scorer
File: models/scorer.py

Fully dynamic, role-agnostic scorer.
No ML model, no hardcoded role configs.
Scores are driven entirely by the JD criteria extracted by Claude.
"""

from dataclasses import dataclass
from models.candidate import Candidate


@dataclass
class RoleConfig:
    role: str
    required_skills: list[str]
    min_experience: int
    degree_required: bool
    weights: dict


# Static configs for the /screen endpoint (used when no JD is uploaded)
ROLE_CONFIGS: dict[str, RoleConfig] = {
    "ml_engineer": RoleConfig(
        role="ml_engineer",
        required_skills=["python", "machine learning", "docker", "gcp"],
        min_experience=3,
        degree_required=True,
        weights={"skills": 0.5, "experience": 0.3, "degree": 0.2},
    ),
    "data_analyst": RoleConfig(
        role="data_analyst",
        required_skills=["python", "sql", "spark"],
        min_experience=1,
        degree_required=False,
        weights={"skills": 0.6, "experience": 0.3, "degree": 0.1},
    ),
}


class Scorer:
    def __init__(self, role: str):
        if role not in ROLE_CONFIGS:
            raise ValueError(f"Unknown role '{role}'. Available: {list(ROLE_CONFIGS.keys())}")
        self._config = ROLE_CONFIGS[role]

    def score(self, candidate: Candidate) -> Candidate:
        summary = candidate.resume.summary()
        w = self._config.weights

        skill_score  = self._score_skills(summary["skills"])
        exp_score    = self._score_experience(summary["years_experience"])
        degree_score = 100.0 if summary["has_degree"] else (0.0 if self._config.degree_required else 60.0)

        total = (
            w["skills"]     * skill_score +
            w["experience"] * exp_score +
            w["degree"]     * degree_score
        )
        candidate.set_score(round(total, 2))
        return candidate

    def _score_skills(self, candidate_skills: list[str]) -> float:
        if not self._config.required_skills:
            return 100.0
        matched = set(s.lower() for s in candidate_skills) & set(s.lower() for s in self._config.required_skills)
        return (len(matched) / len(self._config.required_skills)) * 100

    def _score_experience(self, years: int) -> float:
        min_exp = self._config.min_experience
        if min_exp == 0:
            return 100.0
        return min(years / (min_exp * 2), 1.0) * 100

    def rank(self, candidates: list[Candidate]) -> list[Candidate]:
        for c in candidates:
            self.score(c)
        return sorted(candidates, key=lambda c: c.score, reverse=True)
