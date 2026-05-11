"""Vercel serverless entry — re-exports the Flask app from backend/."""

import os
import sys

_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _backend not in sys.path:
    sys.path.insert(0, _backend)
os.chdir(_backend)

from app import app  # noqa: E402

__all__ = ["app"]
