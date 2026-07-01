"""
ResumeRadar — JD Parser
File: core/jd_parser.py

Uses Claude (Anthropic) to extract structured requirements from a job description.
"""

import os
import json
import anthropic


def parse_jd(jd_text: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set.")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Extract the key requirements from this job description.

Return ONLY a valid JSON object with these exact fields:
{{
  "role": "<short role title, lowercase with underscores, e.g. ml_engineer>",
  "required_skills": ["skill1", "skill2"],
  "min_experience": <integer years, 0 if not specified>,
  "degree_required": <true or false>,
  "weights": {{"skills": 0.5, "experience": 0.3, "degree": 0.2}}
}}

Rules:
- required_skills: lowercase technical skills only (languages, tools, frameworks, platforms)
- Return ONLY the JSON, no explanation, no markdown fences

Job Description:
{jd_text}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
