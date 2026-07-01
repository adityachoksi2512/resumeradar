"""
ResumeRadar — Demo UI
File: demo_ui.py

Run with:
    streamlit run demo_ui.py

Requires FastAPI running in another terminal:
    uvicorn api.main:app --reload

Requires GOOGLE_API_KEY set in environment or .env
"""

import os
import json
import requests
import streamlit as st
from core.file_parser import extract_text
from core.jd_parser import parse_jd
from models.resume import Resume
from models.candidate import Candidate, SeniorCandidate
from models.scorer import Scorer, RoleConfig, ROLE_CONFIGS

API_BASE = "http://127.0.0.1:8000"
API_KEY  = "radar-key-2024"

st.set_page_config(
    page_title="ResumeRadar",
    page_icon="🎯",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding: 2rem 3rem; max-width: 1100px; }
.radar-title { font-size: 2rem; font-weight: 600; letter-spacing: -0.03em; color: #0f172a; margin: 0; }
.radar-sub { font-size: 0.9rem; color: #64748b; margin-top: 0.3rem; }
.section-label { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: #94a3b8; margin-bottom: 0.5rem; }
.candidate-card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem; }
.candidate-card.shortlisted { border-left: 3px solid #2563eb; }
.candidate-card.rejected { opacity: 0.6; }
.card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.6rem; }
.candidate-id { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #0f172a; font-weight: 500; }
.score-pill { font-size: 0.8rem; font-weight: 600; padding: 0.2rem 0.75rem; border-radius: 20px; font-family: 'JetBrains Mono', monospace; }
.score-high { background: #dbeafe; color: #1d4ed8; }
.score-mid  { background: #fef3c7; color: #92400e; }
.score-low  { background: #f1f5f9; color: #475569; }
.shortlist-badge { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; padding: 0.15rem 0.6rem; border-radius: 4px; background: #2563eb; color: white; margin-left: 0.5rem; }
.senior-badge { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; padding: 0.15rem 0.6rem; border-radius: 4px; background: #7c3aed; color: white; margin-left: 0.5rem; }
.skills-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
.skill-tag { font-size: 0.72rem; padding: 0.15rem 0.55rem; border-radius: 4px; background: #f8fafc; color: #475569; border: 1px solid #e2e8f0; font-family: 'JetBrains Mono', monospace; }
.skill-tag.matched { background: #dbeafe; color: #1d4ed8; border-color: #bfdbfe; }
.meta-row { display: flex; gap: 1.5rem; margin-top: 0.4rem; }
.meta-item { font-size: 0.8rem; color: #64748b; }
.meta-item strong { color: #0f172a; font-weight: 500; }
.stat-card { background: #f8fafc; border-radius: 8px; padding: 1rem 1.25rem; text-align: center; }
.stat-num { font-size: 1.75rem; font-weight: 600; color: #0f172a; letter-spacing: -0.03em; }
.stat-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.2rem; }
.jd-box { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem 1.25rem; margin-top: 0.75rem; font-size: 0.82rem; color: #334155; line-height: 1.6; }
.jd-box code { background: #e2e8f0; padding: 0.1rem 0.4rem; border-radius: 3px; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; }
</style>
""", unsafe_allow_html=True)


# ── Header ──────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:2.5rem; padding-bottom:1.5rem; border-bottom:1px solid #e5e7eb;">
    <p class="radar-title">ResumeRadar</p>
    <p class="radar-sub">Upload a job description and candidate resumes — get a ranked shortlist instantly.</p>
</div>
""", unsafe_allow_html=True)


# ── Layout ───────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

with left:
    # JD upload
    st.markdown('<p class="section-label">Job description</p>', unsafe_allow_html=True)
    jd_file = st.file_uploader(
        "Upload JD", type=["pdf", "docx"],
        label_visibility="collapsed", key="jd"
    )

    # Resume uploads
    st.markdown('<p class="section-label" style="margin-top:1.5rem">Resumes</p>', unsafe_allow_html=True)
    resume_files = st.file_uploader(
        "Upload resumes", type=["pdf", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed", key="resumes"
    )

    # Senior toggle per resume
    senior_map = {}
    if resume_files:
        st.markdown('<p class="section-label" style="margin-top:1rem">Senior candidates</p>', unsafe_allow_html=True)
        for f in resume_files:
            senior_map[f.name] = st.checkbox(f.name, key=f"senior_{f.name}")

    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)
    screen_btn = st.button("Screen candidates →", use_container_width=True, type="primary",
                           disabled=not (jd_file and resume_files))


# ── Results ──────────────────────────────────────────────
with right:
    if not jd_file or not resume_files:
        st.markdown("""
        <div style="margin-top:4rem; text-align:center; color:#94a3b8;">
            <p style="font-size:0.9rem;">Upload a job description and at least one resume on the left,<br>then click <strong>Screen candidates</strong>.</p>
        </div>
        """, unsafe_allow_html=True)

    elif screen_btn:
        # ── Step 1: Parse JD ──
        with st.spinner("Parsing job description with Gemini..."):
            try:
                jd_text = extract_text(jd_file.name, jd_file.read())
                jd_criteria = parse_jd(jd_text)
            except Exception as e:
                st.error(f"Failed to parse JD: {e}")
                st.stop()

        # Show parsed JD criteria
        st.markdown('<p class="section-label">Extracted from JD</p>', unsafe_allow_html=True)
        skills_str = ", ".join(f"`{s}`" for s in jd_criteria["required_skills"])
        st.markdown(f"""
        <div class="jd-box">
            <strong>Role:</strong> {jd_criteria["role"].replace("_", " ").title()}<br>
            <strong>Required skills:</strong> {", ".join([f'<code>{s}</code>' for s in jd_criteria["required_skills"]])}<br>
            <strong>Min experience:</strong> {jd_criteria["min_experience"]} years<br>
            <strong>Degree required:</strong> {"yes" if jd_criteria["degree_required"] else "no"}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

        # ── Step 2: Build dynamic RoleConfig from JD ──
        dynamic_config = RoleConfig(
            role=jd_criteria["role"],
            required_skills=jd_criteria["required_skills"],
            min_experience=jd_criteria["min_experience"],
            degree_required=jd_criteria["degree_required"],
            weights=jd_criteria["weights"],
        )
        ROLE_CONFIGS["__dynamic__"] = dynamic_config
        scorer = Scorer(role="__dynamic__")

        # ── Step 3: Parse resumes and score ──
        with st.spinner(f"Screening {len(resume_files)} candidate(s)..."):
            candidates = []
            parse_errors = []

            for f in resume_files:
                try:
                    text = extract_text(f.name, f.read())
                    resume = Resume(
                        candidate_id=f.name.rsplit(".", 1)[0],
                        raw_text=text,
                        role_applied=jd_criteria["role"],
                    ).parse()
                    is_senior = senior_map.get(f.name, False)
                    candidate = SeniorCandidate(resume) if is_senior else Candidate(resume)
                    candidates.append(candidate)
                except Exception as e:
                    parse_errors.append(f"{f.name}: {e}")

            if parse_errors:
                for err in parse_errors:
                    st.warning(f"Could not parse {err}")

            ranked = scorer.rank(candidates)

        # ── Step 4: Display results ──
        shortlisted = [c for c in ranked if c.shortlisted]
        not_shortlisted = [c for c in ranked if not c.shortlisted]

        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stat-card"><div class="stat-num">{len(ranked)}</div><div class="stat-label">Submitted</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#2563eb">{len(shortlisted)}</div><div class="stat-label">Shortlisted</div></div>', unsafe_allow_html=True)
        with col3:
            top = ranked[0].score if ranked else 0
            st.markdown(f'<div class="stat-card"><div class="stat-num">{top}</div><div class="stat-label">Top score</div></div>', unsafe_allow_html=True)
        with col4:
            rate = round(len(shortlisted) / len(ranked) * 100) if ranked else 0
            st.markdown(f'<div class="stat-card"><div class="stat-num">{rate}%</div><div class="stat-label">Pass rate</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

        required_skills = set(jd_criteria["required_skills"])

        def render_card(c, shortlisted_flag):
            p = c.profile()
            score_class = "score-high" if p["score"] >= 75 else ("score-mid" if p["score"] >= 50 else "score-low")
            card_class = "shortlisted" if shortlisted_flag else "rejected"
            level_badge = '<span class="senior-badge">senior</span>' if p["level"] == "senior" else ""
            sl_badge = '<span class="shortlist-badge">shortlisted</span>' if shortlisted_flag else ""

            skills_html = ""
            for s in p["skills"]:
                cls = "skill-tag matched" if s in required_skills else "skill-tag"
                skills_html += f'<span class="{cls}">{s}</span>'
            if not skills_html:
                skills_html = '<span class="skill-tag">no skills matched</span>'

            st.markdown(f"""
            <div class="candidate-card {card_class}">
                <div class="card-top">
                    <span class="candidate-id">{p["candidate_id"]}{level_badge}{sl_badge}</span>
                    <span class="score-pill {score_class}">{p["score"]}</span>
                </div>
                <div class="meta-row">
                    <span class="meta-item"><strong>{p["years_experience"]} yrs</strong> exp</span>
                    <span class="meta-item">Degree: <strong>{"yes" if p["has_degree"] else "no"}</strong></span>
                </div>
                <div class="skills-row">{skills_html}</div>
            </div>
            """, unsafe_allow_html=True)

        if shortlisted:
            st.markdown('<p class="section-label">Shortlisted</p>', unsafe_allow_html=True)
            for c in shortlisted:
                render_card(c, True)

        if not_shortlisted:
            st.markdown('<p class="section-label" style="margin-top:1.25rem">Not shortlisted</p>', unsafe_allow_html=True)
            for c in not_shortlisted:
                render_card(c, False)
