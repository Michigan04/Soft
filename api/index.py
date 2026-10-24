"""Vercel serverless entry point for the FastAPI backend.

Vercel's Python runtime picks up the ASGI `app` exported from this module.
vercel.json rewrites every /api/* request here, and the FastAPI routes already
live under /api/v1, so paths line up without any prefix stripping.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import app  # noqa: E402,F401
