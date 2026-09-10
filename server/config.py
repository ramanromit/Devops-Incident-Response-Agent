"""
Server Configuration
Loads environment variables and sets runtime defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if present
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
DEFAULT_PROVIDER = os.environ.get("DEFAULT_PROVIDER", "mock")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
STATIC_FRONTEND_DIR = ROOT_DIR / "frontend"
