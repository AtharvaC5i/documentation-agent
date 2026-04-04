import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join("..", "storage"))


def _review_path(project_id: str) -> Path:
    return Path(STORAGE_DIR) / "projects" / project_id / "review_state.json"


def _load_state(project_id: str) -> Dict[str, Any]:
    path = _review_path(project_id)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_state(project_id: str, state: Dict[str, Any]):
    path = _review_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def initialise_review(project_id: str, sections: List[Dict[str, Any]]):
    """
    Called once after generation completes.
    Seeds the review state with all sections set to 'pending'.
    Does not overwrite existing decisions.
    """
    state = _load_state(project_id)
    for sec in sections:
        name = sec["name"]
        if name not in state:
            state[name] = {
                "status":          "pending",   # pending | approved | rejected
                "original_content": sec.get("content", ""),
                "edited_content":   None,        # set when human edits
                "note":             None,
                "quality_score":    sec.get("quality_score", 0.0),
                "word_count":       len(sec.get("content", "").split()),
                "order":            sec.get("order", 0),
                "reviewed_at":      None,
            }
    _save_state(project_id, state)


def get_review_state(project_id: str) -> Dict[str, Any]:
    return _load_state(project_id)


def apply_decision(
    project_id:      str,
    section_name:    str,
    action:          str,            # "approve" | "reject"
    edited_content:  Optional[str],
    note:            Optional[str],
) -> Dict[str, Any]:
    state = _load_state(project_id)

    if section_name not in state:
        raise KeyError(f"Section '{section_name}' not found in review state.")

    entry = state[section_name]
    entry["status"]      = "approved" if action == "approve" else "rejected"
    entry["note"]        = note
    entry["reviewed_at"] = datetime.now(timezone.utc).isoformat()

    if edited_content and edited_content.strip():
        entry["edited_content"] = edited_content.strip()
        entry["word_count"]     = len(edited_content.strip().split())

    state[section_name] = entry
    _save_state(project_id, state)
    return entry


def reset_section_for_regen(project_id: str, section_name: str):
    """Mark a section pending again after a regeneration is triggered."""
    state = _load_state(project_id)
    if section_name in state:
        state[section_name]["status"]         = "pending"
        state[section_name]["reviewed_at"]    = None
        state[section_name]["note"]           = None
        state[section_name]["edited_content"] = None
    _save_state(project_id, state)


def get_final_sections(project_id: str) -> List[Dict[str, Any]]:
    """
    Returns sections in order, using edited_content where available,
    falling back to original_content. Used by assembly.
    """
    state = _load_state(project_id)
    result = []
    for name, entry in sorted(state.items(), key=lambda x: x[1].get("order", 0)):
        content = entry.get("edited_content") or entry.get("original_content", "")
        result.append({
            "name":          name,
            "content":       content,
            "order":         entry.get("order", 0),
            "quality_score": entry.get("quality_score", 0.0),
            "status":        entry.get("status", "pending"),
        })
    return result


def get_summary(project_id: str) -> Dict[str, Any]:
    state = _load_state(project_id)
    total    = len(state)
    approved = sum(1 for e in state.values() if e["status"] == "approved")
    rejected = sum(1 for e in state.values() if e["status"] == "rejected")
    pending  = sum(1 for e in state.values() if e["status"] == "pending")
    edited   = sum(1 for e in state.values() if e.get("edited_content"))
    return {
        "total":    total,
        "approved": approved,
        "rejected": rejected,
        "pending":  pending,
        "edited":   edited,
        "ready":    (pending == 0 and rejected == 0),
    }