"""
File-based persistent storage.
Every project is stored as a folder of JSON files on disk.
Survives backend restarts. No database required.

Folder structure:
  projects/
    {project_id}/
      project.json          — metadata + status
      requirements.json     — requirements pool + glossary
      conflicts.json        — conflicts + gaps + coverage
      sections.json         — generated section content
      inputs/
        transcript.txt
        user_stories.txt

The final .docx is stored in:
  outputs/BRD_{name}_{id}.docx
"""

import os
import json
import threading
import shutil
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.project import Project, Requirement

# Root folder for all project data — sits next to backend/
PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "../../projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)


def _project_dir(project_id: str) -> str:
    return os.path.join(PROJECTS_DIR, project_id)


def _ensure_dir(project_id: str):
    d = _project_dir(project_id)
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "inputs"), exist_ok=True)


def _read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


# ── Project metadata serialisation ─────────────────────────────────────────

def _project_to_dict(project: Project) -> Dict[str, Any]:
    """Serialise only the lightweight metadata fields — NOT the heavy data."""
    return {
        "id": project.id,
        "project_name": project.project_name,
        "client_name": project.client_name,
        "industry": project.industry,
        "description": project.description,
        "team_members": project.team_members,
        "status": project.status,
        "progress": project.progress,
        "progress_message": project.progress_message,
        "created_at": project.created_at,
        "selected_sections": project.selected_sections,
        "suggested_sections": project.suggested_sections,
        "document_path": project.document_path,
        "version": project.version,
        "previous_versions": project.previous_versions,
    }


def _project_from_dict(d: Dict[str, Any]) -> Project:
    return Project(
        id=d["id"],
        project_name=d["project_name"],
        client_name=d["client_name"],
        industry=d.get("industry", ""),
        description=d.get("description", ""),
        team_members=d.get("team_members", []),
        status=d.get("status", "created"),
        progress=d.get("progress", 0),
        progress_message=d.get("progress_message", ""),
        created_at=d.get("created_at", datetime.now().isoformat()),
        selected_sections=d.get("selected_sections", []),
        suggested_sections=d.get("suggested_sections", []),
        document_path=d.get("document_path"),
        version=d.get("version", 1),
        previous_versions=d.get("previous_versions", []),
    )


# ── Public storage API ──────────────────────────────────────────────────────

class FileProjectStore:
    """
    Thread-safe file-based project store.
    Loads projects from disk on demand.
    Writes are split into separate JSON files to avoid rewriting
    large requirement arrays every time status changes.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: Dict[str, Project] = {}
        self._load_all_from_disk()

    def _load_all_from_disk(self):
        """Load all existing projects from disk at startup."""
        if not os.path.exists(PROJECTS_DIR):
            return
        for pid in os.listdir(PROJECTS_DIR):
            p = self._load_project(pid)
            if p:
                self._cache[pid] = p

    def _load_project(self, project_id: str) -> Optional[Project]:
        """Load a single project from disk including all data files."""
        d = _project_dir(project_id)
        meta_path = os.path.join(d, "project.json")
        if not os.path.exists(meta_path):
            return None

        meta = _read_json(meta_path)
        if not meta:
            return None

        project = _project_from_dict(meta)

        # Load inputs
        t_path = os.path.join(d, "inputs", "transcript.txt")
        s_path = os.path.join(d, "inputs", "user_stories.txt")
        if os.path.exists(t_path):
            with open(t_path, "r", encoding="utf-8") as f:
                project.transcript_raw = f.read()
        if os.path.exists(s_path):
            with open(s_path, "r", encoding="utf-8") as f:
                project.user_stories_raw = f.read()

        # Load requirements pool
        req_data = _read_json(os.path.join(d, "requirements.json"), {})
        if req_data:
            reqs = req_data.get("requirements", [])
            project.requirements_pool = []
            for r in reqs:
                try:
                    project.requirements_pool.append(Requirement(**r))
                except Exception:
                    pass
            project.glossary = req_data.get("glossary", {})
            project.stakeholders = req_data.get("stakeholders", [])

        # Load conflicts
        conf_data = _read_json(os.path.join(d, "conflicts.json"), {})
        if conf_data:
            project.conflicts = conf_data.get("conflicts", [])
            project.gaps = conf_data.get("gaps", [])
            project.section_coverage = conf_data.get("coverage", {})

        # Load sections
        sec_data = _read_json(os.path.join(d, "sections.json"), {})
        if sec_data:
            project.generated_sections = sec_data.get("sections", [])

        return project

    def save(self, project: Project):
        with self._lock:
            self._cache[project.id] = project
            self._persist(project)

    def _persist(self, project: Project):
        """Write project to disk in split files."""
        _ensure_dir(project.id)
        d = _project_dir(project.id)

        # Always write metadata (small, changes frequently)
        _write_json(os.path.join(d, "project.json"), _project_to_dict(project))

        # Write inputs only if present
        if project.transcript_raw:
            t_path = os.path.join(d, "inputs", "transcript.txt")
            with open(t_path, "w", encoding="utf-8") as f:
                f.write(project.transcript_raw)
        if project.user_stories_raw:
            s_path = os.path.join(d, "inputs", "user_stories.txt")
            with open(s_path, "w", encoding="utf-8") as f:
                f.write(project.user_stories_raw)

        # Write requirements pool only if non-empty
        if project.requirements_pool:
            _write_json(os.path.join(d, "requirements.json"), {
                "requirements": [r.dict() for r in project.requirements_pool],
                "glossary": project.glossary,
                "stakeholders": project.stakeholders,
            })

        # Write conflicts only if present
        if project.conflicts or project.gaps or project.section_coverage:
            _write_json(os.path.join(d, "conflicts.json"), {
                "conflicts": project.conflicts,
                "gaps": project.gaps,
                "coverage": project.section_coverage,
            })

        # Write sections only if present
        if project.generated_sections:
            _write_json(os.path.join(d, "sections.json"), {
                "sections": project.generated_sections,
            })

    def get(self, project_id: str) -> Optional[Project]:
        with self._lock:
            return self._cache.get(project_id)

    def list_all(self) -> List[Project]:
        with self._lock:
            return list(self._cache.values())

    def delete(self, project_id: str):
        with self._lock:
            self._cache.pop(project_id, None)
            d = _project_dir(project_id)
            if os.path.exists(d):
                shutil.rmtree(d)

    def save_input_files(self, project_id: str, transcript: Optional[str], user_stories: Optional[str]):
        """Explicitly persist raw input files — called after upload."""
        _ensure_dir(project_id)
        d = _project_dir(project_id)
        if transcript:
            with open(os.path.join(d, "inputs", "transcript.txt"), "w", encoding="utf-8") as f:
                f.write(transcript)
        if user_stories:
            with open(os.path.join(d, "inputs", "user_stories.txt"), "w", encoding="utf-8") as f:
                f.write(user_stories)
