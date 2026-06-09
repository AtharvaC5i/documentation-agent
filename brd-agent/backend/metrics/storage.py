"""
Metrics storage — persists the final metrics JSON alongside the project data.

Metrics are saved to:
    projects/{project_id}/metrics.json
"""

import os
import json
from typing import Optional

# The projects root is two levels above this file (backend/metrics/ → backend/ → brd-agent/ → projects/)
_PROJECTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "projects"
)


def save_metrics(project_id: str, metrics_dict: dict) -> str:
    """
    Persist metrics for a project run as JSON.

    Returns the absolute path of the written file.
    """
    project_dir = os.path.join(_PROJECTS_DIR, project_id)
    os.makedirs(project_dir, exist_ok=True)
    path = os.path.join(project_dir, "metrics.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics_dict, f, ensure_ascii=False, indent=2, default=str)
    return os.path.abspath(path)


def load_metrics(project_id: str) -> Optional[dict]:
    """
    Load persisted metrics for a project run.

    Returns None if not found.
    """
    path = os.path.join(_PROJECTS_DIR, project_id, "metrics.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
