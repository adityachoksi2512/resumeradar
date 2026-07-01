"""
ResumeRadar — Layer 8: ADK Agents
File: agents/orchestrator.py

Orchestrates the recruiter and summarizer agents in sequence:
  1. Recruiter agent screens the resumes via API
  2. Summarizer agent writes briefs on shortlisted candidates

Run with:
    python -m agents.orchestrator
"""

import os
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agents.recruiter_agent import recruiter_agent
from agents.summarizer_agent import summarizer_agent


RESUMES = [
    {
        "candidate_id": "C001",
        "role_applied": "ml_engineer",
        "resume_text": "6 years experience in python, machine learning, docker, gcp. Master degree in CS.",
        "is_senior": True,
    },
    {
        "candidate_id": "C002",
        "role_applied": "ml_engineer",
        "resume_text": "2 years experience in python, sql. Bachelor degree in Statistics.",
        "is_senior": False,
    },
    {
        "candidate_id": "C003",
        "role_applied": "ml_engineer",
        "resume_text": "4 years experience in python, machine learning, docker, kubernetes, pytorch. No degree.",
        "is_senior": False,
    },
    {
        "candidate_id": "C004",
        "role_applied": "ml_engineer",
        "resume_text": "7 years experience in python, machine learning, gcp, docker, spark, scala. Master degree.",
        "is_senior": True,
    },
]


async def run_agent(agent, session_service, app_name, user_id, session_id, message):
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
    )
    content = Content(role="user", parts=[Part(text=message)])
    final_response = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text
    return final_response


async def main():
    import json
    session_service = InMemorySessionService()

    print("\n" + "="*55)
    print("  ResumeRadar — Agent Pipeline")
    print("="*55)

    # ── Step 1: Recruiter Agent screens the resumes ──
    print("\n[Step 1] Recruiter Agent — screening candidates...\n")

    await session_service.create_session(
        app_name="resumeradar", user_id="hiring_team", session_id="session_recruiter"
    )

    screening_request = (
        f"Please screen these candidates for the ml_engineer role:\n"
        f"{json.dumps(RESUMES, indent=2)}"
    )

    screening_results = await run_agent(
        recruiter_agent, session_service,
        "resumeradar", "hiring_team", "session_recruiter",
        screening_request,
    )

    print("Recruiter Agent response:")
    print(screening_results)

    # wait for rate limit window to reset
    import time
    print("\n[waiting 15s for rate limit reset...]")
    time.sleep(15)

    # ── Step 2: Summarizer Agent writes briefs ──
    print("\n[Step 2] Summarizer Agent — writing candidate briefs...\n")

    await session_service.create_session(
        app_name="resumeradar", user_id="hiring_team", session_id="session_summarizer"
    )

    summary_request = (
        f"Here are the screening results. Please write briefs for shortlisted candidates:\n\n"
        f"{screening_results}"
    )

    candidate_briefs = await run_agent(
        summarizer_agent, session_service,
        "resumeradar", "hiring_team", "session_summarizer",
        summary_request,
    )

    print("Summarizer Agent response:")
    print(candidate_briefs)
    print("\n" + "="*55 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
