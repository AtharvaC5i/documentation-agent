from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from core.review.review_manager import (
    get_review_state,
    apply_decision,
    reset_section_for_regen,
    get_summary,
    initialise_review,
    _save_state,
)
from core.generation.section_generator import generate_section
from core.analysis.analysis_models import load_analysis

router = APIRouter(prefix="/review", tags=["review"])


# ─────────────────────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────────────────────

class SectionInit(BaseModel):
    name:          str
    content:       str
    order:         int
    quality_score: Optional[float] = None


class InitRequest(BaseModel):
    sections: List[SectionInit]


class DecisionRequest(BaseModel):
    section_name:   str
    action:         str           # "approve" | "reject"
    edited_content: Optional[str] = None
    note:           Optional[str] = None


class RegenRequest(BaseModel):
    section_name: str


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────

@router.post("/{project_id}/init")
def init_review(project_id: str, body: InitRequest):
    """
    Seeds the review state from generation output.
    Idempotent — does not overwrite sections that already have a decision.
    Called by the Streamlit page each time Step 06 loads.
    """
    sections = [s.model_dump() for s in body.sections]
    initialise_review(project_id, sections)
    return {
        "project_id": project_id,
        "initialised": len(sections),
        "summary": get_summary(project_id),
    }


@router.get("/{project_id}")
def get_review(project_id: str):
    """Returns full review state + summary for the project."""
    state = get_review_state(project_id)
    if not state:
        raise HTTPException(
            status_code=404,
            detail="No review state found. Run generation first.",
        )
    return {
        "project_id": project_id,
        "sections":   state,
        "summary":    get_summary(project_id),
    }


@router.post("/{project_id}/decide")
def post_decision(project_id: str, body: DecisionRequest):
    """Approve or reject a single section, with optional inline edit."""
    if body.action not in ("approve", "reject"):
        raise HTTPException(
            status_code=400,
            detail="action must be 'approve' or 'reject'.",
        )
    try:
        entry = apply_decision(
            project_id,
            body.section_name,
            body.action,
            body.edited_content,
            body.note,
        )
        return {
            "section_name": body.section_name,
            "entry":        entry,
            "summary":      get_summary(project_id),
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{project_id}/regenerate")
def regenerate_section(project_id: str, body: RegenRequest):
    """
    Triggers a fresh generation for a single rejected section.
    Resets its review status to 'pending' and writes the new
    content back into the review state.
    """
    analysis = load_analysis(project_id)
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found for project.",
        )

    # Mark section pending before regenerating
    reset_section_for_regen(project_id, body.section_name)

    # Re-generate
    try:
        result = generate_section(project_id, body.section_name, analysis)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Regeneration failed: {str(e)}",
        )

    # Push new content back into review state
    state = get_review_state(project_id)
    if body.section_name in state:
        state[body.section_name]["original_content"] = result.get("content", "")
        state[body.section_name]["word_count"]       = len(result.get("content", "").split())
        state[body.section_name]["quality_score"]    = result.get("quality_score", 0.0)
        state[body.section_name]["regenerated"]      = True   # tracked for reporting
        _save_state(project_id, state)

    return {
        "section_name": body.section_name,
        "result":       result,
        "summary":      get_summary(project_id),
    }