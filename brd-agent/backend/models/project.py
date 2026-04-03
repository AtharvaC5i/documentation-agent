"""
Project data models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import threading


class Requirement(BaseModel):
    req_id: str
    type: str
    description: str
    source: str
    speaker: Optional[str] = None
    confidence: float = 1.0
    priority: Optional[str] = None
    module_tag: Optional[str] = None
    user_story_id: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    source_location: Optional[str] = None
    added_in_version: Optional[int] = 1
    ambiguity_flag: Optional[bool] = False
    ambiguity_suggestion: Optional[str] = None


class Project(BaseModel):
    id: str
    project_name: str
    client_name: str
    industry: str
    description: str
    team_members: List[str] = []
    status: str = "created"
    progress: int = 0
    progress_message: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Raw inputs
    transcript_raw: Optional[str] = None
    user_stories_raw: Optional[str] = None

    # Extracted data
    requirements_pool: List[Requirement] = []
    glossary: Dict[str, str] = {}
    stakeholders: List[Dict[str, Any]] = []

    # Conflict & gap analysis
    conflicts: List[Dict[str, Any]] = []
    gaps: List[Dict[str, Any]] = []
    section_coverage: Dict[str, str] = {}

    # Section management
    suggested_sections: List[Dict[str, Any]] = []
    selected_sections: List[str] = []
    generated_sections: List[Dict[str, Any]] = []

    # Output
    document_path: Optional[str] = None

    # Living BRD versioning
    version: int = 1
    previous_versions: List[Dict[str, Any]] = []

    # Change detection
    pending_changes: List[Dict[str, Any]] = []
    change_report: Optional[str] = None

    # Follow-up email
    followup_email_draft: Optional[str] = None

    # Traceability
    traceability_matrix: List[Dict[str, Any]] = []
    traceability_doc_path: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class ProjectStore:
    """Thread-safe in-memory store (legacy — FileProjectStore preferred)."""

    def __init__(self):
        self._store: Dict[str, Project] = {}
        self._lock = threading.Lock()

    def save(self, project: Project):
        with self._lock:
            self._store[project.id] = project

    def get(self, project_id: str) -> Optional[Project]:
        with self._lock:
            return self._store.get(project_id)

    def list_all(self) -> List[Project]:
        with self._lock:
            return list(self._store.values())

    def delete(self, project_id: str):
        with self._lock:
            self._store.pop(project_id, None)
