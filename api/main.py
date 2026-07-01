"""
ResumeRadar — FastAPI
File: api/main.py

Run with: uvicorn api.main:app --reload
"""

import asyncio
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from api.schemas import ScreeningRequest, ScreeningResponse, CandidateResult
from api.auth import verify_api_key
from models.resume import Resume
from models.candidate import Candidate, SeniorCandidate
from models.scorer import ROLE_CONFIGS, Scorer, RoleConfig
from core.file_parser import extract_text
from core.async_parser import parse_all_async

app = FastAPI(title="ResumeRadar API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "ResumeRadar"}


@app.get("/roles")
def list_roles():
    return {
        "roles": [
            {
                "role": name,
                "required_skills": cfg.required_skills,
                "min_experience": cfg.min_experience,
                "degree_required": cfg.degree_required,
            }
            for name, cfg in ROLE_CONFIGS.items()
            if not name.startswith("__")
        ]
    }


@app.post("/extract")
async def extract_file_text(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = extract_text(file.filename, content)
        return {"filename": file.filename, "text": text}
    except Exception as e:
        return {"filename": file.filename, "text": "", "error": str(e)}


@app.post("/parse-jd")
async def parse_jd_endpoint(file: UploadFile = File(...)):
    from core.jd_parser import parse_jd
    content = await file.read()
    text = extract_text(file.filename, content)
    criteria = parse_jd(text)
    return criteria


@app.post("/screen", response_model=ScreeningResponse, dependencies=[Depends(verify_api_key)])
def screen_resumes(request: ScreeningRequest):
    if not request.resumes:
        return ScreeningResponse(role="unknown", total_submitted=0, total_shortlisted=0, ranked=[])

    role = request.resumes[0].role_applied
    if role not in ROLE_CONFIGS:
        return {"error": f"Unknown role: {role}"}

    scorer = Scorer(role=role)
    candidates = []
    for r in request.resumes:
        resume = Resume(r.candidate_id, r.resume_text, r.role_applied).parse()
        candidate = SeniorCandidate(resume) if r.is_senior else Candidate(resume)
        candidates.append(candidate)

    ranked = scorer.rank(candidates)
    results = [CandidateResult(**c.profile()) for c in ranked]
    return ScreeningResponse(
        role=role,
        total_submitted=len(ranked),
        total_shortlisted=sum(1 for r in results if r.shortlisted),
        ranked=results,
    )


@app.post("/screen-dynamic")
async def screen_dynamic(
    jd_file: UploadFile = File(...),
    resumes: list[UploadFile] = File(...),
):
    from core.jd_parser import parse_jd

    # Step 1 — Parse JD with Claude
    jd_bytes = await jd_file.read()
    jd_text  = extract_text(jd_file.filename, jd_bytes)
    criteria = parse_jd(jd_text)

    # Step 2 — Parse all resume files concurrently
    resume_data = []
    for rf in resumes:
        rb = await rf.read()
        resume_data.append({"filename": rf.filename, "bytes": rb})

    parsed = await parse_all_async(resume_data)

    # Step 3 — Score with ML model
    dynamic_config = RoleConfig(
        role=criteria["role"],
        required_skills=criteria["required_skills"],
        min_experience=criteria["min_experience"],
        degree_required=criteria["degree_required"],
        weights=criteria["weights"],
    )
    ROLE_CONFIGS["__dynamic__"] = dynamic_config
    scorer = Scorer(role="__dynamic__")

    candidates = []
    for p in parsed:
        resume = Resume(
            candidate_id=p["filename"].rsplit(".", 1)[0],
            raw_text=p["text"],
            role_applied=criteria["role"],
            required_skills=criteria["required_skills"],
        ).parse()
        candidates.append(Candidate(resume))

    ranked = scorer.rank(candidates)

    def clean(profile):
        return {k: (bool(v) if hasattr(v, 'item') else v) for k, v in profile.items()}

    return {
        "jd_criteria": criteria,
        "total_submitted": len(ranked),
        "total_shortlisted": sum(1 for c in ranked if c.shortlisted),
        "ranked": [clean(c.profile()) for c in ranked],
    }


@app.post("/agent-summary")
async def agent_summary(payload: dict):
    from agents.summarizer_agent import summarize_candidates
    ranked = payload.get("ranked", [])
    role   = payload.get("role", "the role")
    briefs = summarize_candidates(ranked, role)
    return {"briefs": briefs}
