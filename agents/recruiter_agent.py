"""
ResumeRadar — Layer 8: ADK Agents
File: agents/recruiter_agent.py

Recruiter Agent — screens a batch of resumes by calling
the /screen API endpoint and returns ranked candidates.
"""

import os
import json
import requests
from google.adk.agents import Agent
from google.adk.tools import FunctionTool


API_BASE = "http://127.0.0.1:8000"
API_KEY  = os.environ.get("RADAR_API_KEY", "radar-key-2024")


def screen_candidates(resumes_json: str) -> str:
    """
    Screen a batch of resumes through the ResumeRadar API.

    Args:
        resumes_json: JSON string with list of resumes. Each resume needs:
                      candidate_id, role_applied, resume_text, is_senior (bool)

    Returns:
        JSON string with ranked candidates and shortlist status.
    """
    try:
        resumes = json.loads(resumes_json)
        response = requests.post(
            f"{API_BASE}/screen",
            json={"resumes": resumes},
            headers={"x-api-key": API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_available_roles() -> str:
    """
    Fetch the list of roles the system can screen for.

    Returns:
        JSON string listing available roles and their requirements.
    """
    try:
        response = requests.get(f"{API_BASE}/roles", timeout=10)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


recruiter_agent = Agent(
    name="recruiter_agent",
    model="gemini-2.0-flash-lite",
    description="Screens resumes by calling the ResumeRadar API and returns a ranked shortlist.",
    instruction="""
        You are a technical recruiter assistant. Your job is to screen candidates
        for engineering roles using the ResumeRadar screening API.

        When asked to screen candidates:
        1. First call get_available_roles() to confirm the role exists
        2. Format the resumes as a JSON array and call screen_candidates()
        3. Return the ranked results clearly, highlighting who is shortlisted
           and why (score, skills matched, experience)

        Always be concise and professional. Focus on the data.
    """,
    tools=[
        FunctionTool(screen_candidates),
        FunctionTool(get_available_roles),
    ],
)
