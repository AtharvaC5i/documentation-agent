"""
File handling utilities
"""

import os
import uuid
from typing import Dict


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../uploads")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../../outputs")
SYNTHETIC_DIR = os.path.join(os.path.dirname(__file__), "../../synthetic_data")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_upload(content: bytes, filename: str) -> str:
    """Save uploaded file and return path"""
    unique_name = f"{uuid.uuid4()}_{filename}"
    path = os.path.join(UPLOAD_DIR, unique_name)
    with open(path, "wb") as f:
        f.write(content)
    return path


def load_synthetic_data() -> Dict[str, str]:
    """Load synthetic transcript and user stories"""
    transcript_path = os.path.join(SYNTHETIC_DIR, "transcript.txt")
    stories_path = os.path.join(SYNTHETIC_DIR, "user_stories.txt")

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    with open(stories_path, "r", encoding="utf-8") as f:
        user_stories = f.read()

    return {
        "transcript": transcript,
        "user_stories": user_stories
    }


def get_output_path(project_name: str) -> str:
    """Get output file path for generated document"""
    safe_name = project_name.replace(" ", "_").replace("/", "_")
    return os.path.join(OUTPUT_DIR, f"BRD_{safe_name}_{uuid.uuid4().hex[:6]}.docx")
