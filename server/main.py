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

from server.config import HOST, PORT, STATIC_FRONTEND_DIR
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
    return {
        "status": "online",
        "service": "DevOps Incident-Response Agent Core",
        "has_gemini_key": bool(os.environ.get("GEMINI_API_KEY")),
        "has_openai_key": bool(os.environ.get("OPENAI_API_KEY")),
    }


# Mount frontend static directory if exists
if STATIC_FRONTEND_DIR.exists():
    @app.get("/app.js")
    def serve_js():
        return FileResponse(str(STATIC_FRONTEND_DIR / "app.js"), media_type="application/javascript")

    @app.get("/index.css")
    def serve_css():
        return FileResponse(str(STATIC_FRONTEND_DIR / "index.css"), media_type="text/css")

    app.mount("/static", StaticFiles(directory=str(STATIC_FRONTEND_DIR)), name="static")
    app.mount("/", StaticFiles(directory=str(STATIC_FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print(f"Starting DevOps Incident-Response Agent Server on http://{HOST}:{PORT}")
    uvicorn.run("server.main:app", host=HOST, port=PORT, reload=True)
