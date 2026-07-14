import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join("..", "storage"))


class TechStackSnapshot(BaseModel):
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    test_frameworks: List[str] = Field(default_factory=list)
    has_dockerfile: bool = False
    has_cicd: bool = False
    has_kubernetes: bool = False
    has_terraform: bool = False
    has_ansible: bool = False
    detected_language_hints: List[str] = Field(default_factory=list)
    detected_framework_hints: List[str] = Field(default_factory=list)
    detected_database_hints: List[str] = Field(default_factory=list)
    detected_test_hints: List[str] = Field(default_factory=list)


class TechStackComparison(BaseModel):
    detected: Dict[str, Any] = Field(default_factory=dict)
    actual: Dict[str, Any] = Field(default_factory=dict)
    correct_matches: List[str] = Field(default_factory=list)
    missed_items: List[str] = Field(default_factory=list)
    false_positives: List[str] = Field(default_factory=list)
    accuracy_score: float = 0.0


class AnalysisResult(BaseModel):
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    test_frameworks: List[str] = Field(default_factory=list)
    has_dockerfile: bool = False
    has_cicd: bool = False
    has_kubernetes: bool = False
    has_terraform: bool = False
    has_ansible: bool = False
    api_endpoints_count: int = 0
    total_loc: int = 0

    discovered_apis: int = 0
    discovered_classes: int = 0
    discovered_functions: int = 0

    discovered_api_list: List[str] = Field(default_factory=list)
    discovered_class_list: List[str] = Field(default_factory=list)
    discovered_function_list: List[str] = Field(default_factory=list)

    documented_apis: int = 0
    documented_classes: int = 0
    documented_functions: int = 0

    codebase_coverage_percent: float = 0.0

    detected_stack: Dict[str, Any] = Field(default_factory=dict)
    actual_stack: Dict[str, Any] = Field(default_factory=dict)
    tech_stack_comparison: Dict[str, Any] = Field(default_factory=dict)

    correct_matches: List[str] = Field(default_factory=list)
    missed_items: List[str] = Field(default_factory=list)
    false_positives: List[str] = Field(default_factory=list)
    tech_stack_accuracy_score: float = 0.0

    code_examples_total: int = 0
    code_examples_valid: int = 0
    code_examples_invalid: int = 0
    code_example_validity_score: float = 0.0
    code_example_validation_method: str = "not_run"

    acceptance_flag: str = "not_reviewed"
    review_cycle_source: str = "not_reviewed"

    quality_scoring_method: str = "heuristic_length_structure_keyword"
    quality_score_scale: str = "0_to_1"


def save_analysis(project_id: str, result: AnalysisResult):
    path = Path(STORAGE_DIR) / "projects" / project_id / "analysis.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))


def load_analysis(project_id: str) -> Optional[AnalysisResult]:
    path = Path(STORAGE_DIR) / "projects" / project_id / "analysis.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return AnalysisResult(**data)