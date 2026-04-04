# core/analysis/analysis_models.py

import json
import os
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join("..", "storage"))


class AnalysisResult(BaseModel):
    languages:           List[str] = []
    frameworks:          List[str] = []
    databases:           List[str] = []
    test_frameworks:     List[str] = []
    has_dockerfile:      bool      = False
    has_cicd:            bool      = False
    has_kubernetes:      bool      = False
    has_terraform:       bool      = False
    has_ansible:         bool      = False
    api_endpoints_count: int       = 0
    total_loc:           int       = 0


def save_analysis(project_id: str, result: AnalysisResult):
    path = Path(STORAGE_DIR) / "projects" / project_id / "analysis.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(result.model_dump_json(indent=2))


def load_analysis(project_id: str) -> Optional[AnalysisResult]:
    path = Path(STORAGE_DIR) / "projects" / project_id / "analysis.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    return AnalysisResult(**data)