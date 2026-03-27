from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from core.assembler.document_builder import build_document
from core.review.review_manager import get_summary, get_final_sections

router = APIRouter()


class SectionItem(BaseModel):
    name:          str
    content:       str
    order:         int
    quality_score: Optional[float] = None


class AssembleRequest(BaseModel):
    project_id: str
    metadata:   Dict[str, Any]
    sections:   List[SectionItem]


@router.post("/assemble/{project_id}")
async def assemble_document(project_id: str, req: AssembleRequest):
    if not req.sections:
        raise HTTPException(status_code=400, detail="No sections provided.")

    # ── BUG FIX: Use reviewed + edited content if review has been completed ──
    # If review state exists and all sections have been actioned, pull the
    # final (potentially human-edited) content from review state instead of
    # the raw generation payload. Falls back to raw payload if review was skipped.
    try:
        review_summary = get_summary(project_id)
        if review_summary["total"] > 0:
            reviewed_sections = get_final_sections(project_id)
            sections_to_assemble = reviewed_sections
        else:
            sections_to_assemble = [s.model_dump() for s in req.sections]
    except Exception:
        # If review state is missing or unreadable, fall back to raw sections
        sections_to_assemble = [s.model_dump() for s in req.sections]

    try:
        result = build_document(
            project_id=project_id,
            metadata=req.metadata,
            sections=sections_to_assemble,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "project_id":    project_id,
        "file_path":     result["file_path"],
        "word_count":    result["word_count"],
        "page_estimate": result["page_estimate"],
        "section_count": result["section_count"],
        "status":        "assembled",
    }