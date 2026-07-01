"""
ResumeRadar — Layer 3: FastAPI
File: api/auth.py

Simple API key authentication via request header.
"""

from fastapi import Header, HTTPException

VALID_API_KEYS = {"radar-key-2024"}


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
