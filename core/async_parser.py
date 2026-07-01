"""
ResumeRadar — Async Parser
File: core/async_parser.py

Parses multiple resume files concurrently using asyncio.
Used inside /screen-dynamic to extract text from all uploads simultaneously.
"""

import asyncio
from core.file_parser import extract_text


async def parse_file_async(filename: str, file_bytes: bytes) -> dict:
    """Parse a single file asynchronously — runs in a thread to avoid blocking."""
    loop = asyncio.get_event_loop()
    text = await loop.run_in_executor(None, extract_text, filename, file_bytes)
    return {"filename": filename, "text": text}


async def parse_all_async(files: list[dict]) -> list[dict]:
    """
    Parse all resume files concurrently.
    Each file dict: {"filename": str, "bytes": bytes}
    Returns list of {"filename": str, "text": str}
    """
    tasks = [parse_file_async(f["filename"], f["bytes"]) for f in files]
    return await asyncio.gather(*tasks)
