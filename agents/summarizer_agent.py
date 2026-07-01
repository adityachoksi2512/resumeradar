"""
ResumeRadar — Summarizer Agent
File: agents/summarizer_agent.py

Uses Claude directly to write candidate briefs.
No ADK dependency — simpler and no Gemini quota needed.
"""

import os
import json
import anthropic


def summarize_candidates(ranked: list, role: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set.")

    client = anthropic.Anthropic(api_key=api_key)

    shortlisted = [c for c in ranked if c.get("shortlisted")]
    if not shortlisted:
        return "No candidates were shortlisted."

    prompt = f"""You are a hiring coordinator. Here are the shortlisted candidates for the {role.replace('_', ' ')} role.

Write a concise 3-4 sentence brief for each shortlisted candidate covering:
- Their key strengths (skills and experience)
- Why they are a good fit for the role
- Any notable gaps or considerations

Format as a numbered list. Be direct and professional.

Candidates:
{json.dumps(shortlisted, indent=2)}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()
