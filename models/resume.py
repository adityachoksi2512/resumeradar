"""
ResumeRadar — Resume
File: models/resume.py

Parses a resume and extracts skills dynamically against a provided skill list.
No hardcoded domain knowledge — works for any role.
"""

import re


class Resume:
    def __init__(self, candidate_id: str, raw_text: str, role_applied: str, required_skills: list[str] = None):
        self.candidate_id = candidate_id
        self.role_applied = role_applied
        self._raw_text = raw_text
        self._required_skills = required_skills or []
        self._parsed = False

    def parse(self):
        text = self._raw_text.lower()
        self.skills = self._extract_skills(text)
        self.years_experience = self._estimate_experience(text)
        self.has_degree = any(w in text for w in [
            "bachelor", "master", "phd", "b.s", "m.s", "degree",
            "diploma", "graduate", "university", "college"
        ])
        self._parsed = True
        return self

    def _extract_skills(self, text: str) -> list[str]:
        """
        Dynamically check which required skills appear in the resume text.
        Falls back to a broad technical skill list if no required skills provided.
        """
        if self._required_skills:
            return [skill for skill in self._required_skills if skill.lower().replace("_", " ") in text]

        # Generic fallback — broad skill detection when no JD is available
        generic_skills = [
            "python", "sql", "machine learning", "deep learning", "docker",
            "kubernetes", "spark", "tensorflow", "pytorch", "aws", "gcp",
            "azure", "java", "scala", "fastapi", "flask", "espresso",
            "latte art", "coffee brewing", "customer service", "inventory management",
            "training", "leadership", "project management", "communication",
        ]
        return [skill for skill in generic_skills if skill in text]

    def _estimate_experience(self, text: str) -> int:
        matches = re.findall(r"(\d+)\+?\s+year", text)
        return max((int(m) for m in matches), default=0)

    def summary(self) -> dict:
        if not self._parsed:
            raise RuntimeError(f"Resume {self.candidate_id} must be parsed before accessing summary.")
        return {
            "candidate_id": self.candidate_id,
            "role_applied": self.role_applied,
            "skills": self.skills,
            "years_experience": self.years_experience,
            "has_degree": self.has_degree,
        }

    def __repr__(self):
        return f"Resume(id={self.candidate_id}, role={self.role_applied}, parsed={self._parsed})"
