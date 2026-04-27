# main.py (Render Entry Point - redirects to app/main.py)

"""
Render deployment entry point.
This file imports and exposes the FastAPI app from app/main.py
to ensure correct module structure for cloud deployment.
"""

from app.main import app

# Expose the app for Render
__all__ = ["app"]