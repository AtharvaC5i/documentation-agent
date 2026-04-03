"""
Load environment variables — place this at top of backend/main.py
This file is imported by main.py automatically via the line below.
Add this import at the very top of main.py:
    from utils.env_loader import load_env
    load_env()
"""
import os
from pathlib import Path


def load_env():
    """Load .env file if python-dotenv is available"""
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Try .env.example as fallback hint
            print("[BRD Agent] No .env file found. Copy backend/.env.example to backend/.env and fill in your Databricks credentials.")
    except ImportError:
        pass  # dotenv not installed, rely on system env vars
