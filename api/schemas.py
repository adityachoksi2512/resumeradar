"""
ResumeRadar — Layer 3: FastAPI
File: api/schemas.py

Pydantic models for request and response validation.
"""

from pydantic import BaseModel


class ResumeRequest(BaseModel):
    candidate_id: str
    role_applied: str
    resume_text: str
    is_senior: bool = False


class CandidateResult(BaseModel):
    candidate_id: str
    role_applied: str
    score: float
    shortlisted: bool
    level: str
    skills: list[str]
    years_experience: int
    has_degree: bool


class ScreeningRequest(BaseModel):
    resumes: list[ResumeRequest]


class ScreeningResponse(BaseModel):
    role: str
    total_submitted: int
    total_shortlisted: int
    ranked: list[CandidateResult]
