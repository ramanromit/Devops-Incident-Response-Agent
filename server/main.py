"""
Main FastAPI Server Application
Mounts API endpoints and serves the frontend dashboard.
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct execution (e.g. `python server/main.py`)
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from server.config import HOST, PORT, STATIC_FRONTEND_DIR, GEMINI_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL, OPENAI_API_KEY
from server.routes_scenarios import router as router_scenarios
from server.routes_agent import router as router_agent
from server.routes_evaluation import router as router_evaluation

app = FastAPI(
    title="DevOps Incident-Response Agent API",
    description="Autonomous SRE Agent with a Deterministic Evaluation Harness",
    version="1.0.0",
)

# Enable CORS for local and web dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router_scenarios)
app.include_router(router_agent)
app.include_router(router_evaluation)


@app.get("/api/health")
def health_check():
    """Returns system status and active providers."""
    current_gemini_key = os.environ.get("GEMINI_API_KEY", "").strip() or GEMINI_API_KEY
    current_gemini_model = os.environ.get("GEMINI_MODEL", "").strip() or GEMINI_MODEL
    current_groq_key = os.environ.get("GROQ_API_KEY", "").strip() or GROQ_API_KEY
    current_groq_model = os.environ.get("GROQ_MODEL", "").strip() or GROQ_MODEL
    current_openai_key = os.environ.get("OPENAI_API_KEY", "").strip() or OPENAI_API_KEY
    return {
        "status": "online",
        "service": "DevOps Incident-Response Agent Core",
        "has_gemini_key": bool(current_gemini_key),
        "gemini_model": current_gemini_model,
        "has_groq_key": bool(current_groq_key),
        "groq_model": current_groq_model,
        "has_openai_key": bool(current_openai_key),
    }


# Mount frontend static directory if exists
if STATIC_FRONTEND_DIR.exists():
    @app.get("/")
    def serve_index():
        return FileResponse(
            str(STATIC_FRONTEND_DIR / "index.html"),
            media_type="text/html",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    @app.get("/app.js")
    def serve_js():
        return FileResponse(
            str(STATIC_FRONTEND_DIR / "app.js"),
            media_type="application/javascript",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    @app.get("/index.css")
    def serve_css():
        return FileResponse(
            str(STATIC_FRONTEND_DIR / "index.css"),
            media_type="text/css",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    app.mount("/static", StaticFiles(directory=str(STATIC_FRONTEND_DIR)), name="static")
    app.mount("/", StaticFiles(directory=str(STATIC_FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print(f"Starting DevOps Incident-Response Agent Server on http://{HOST}:{PORT}")
    uvicorn.run("server.main:app", host=HOST, port=PORT, reload=True)
