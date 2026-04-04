from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

from core.assembler.document_builder import build_document
from core.review.review_manager import get_summary, get_final_sections
from core.state_store import get_project, update_project   # ✅ add update_project

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

    try:
        review_summary = get_summary(project_id)
        if review_summary["total"] > 0:
            reviewed_sections = get_final_sections(project_id)
            sections_to_assemble = reviewed_sections
        else:
            sections_to_assemble = [s.model_dump() for s in req.sections]
    except Exception:
        sections_to_assemble = [s.model_dump() for s in req.sections]

    try:
        result = build_document(
            project_id=project_id,
            metadata=req.metadata,
            sections=sections_to_assemble,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # ✅ Persist file_path so download route can find it
    update_project(project_id, "assembled_file_path", result["file_path"])

    return {
        "project_id":    project_id,
        "file_path":     result["file_path"],
        "word_count":    result["word_count"],
        "page_estimate": result["page_estimate"],
        "section_count": result["section_count"],
        "status":        "assembled",
    }


# ✅ New download route
@router.get("/assemble/{project_id}/download")
async def download_document(project_id: str):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    file_path = project.get("assembled_file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Assembled document not found. Run assembly first."
        )

    project_name = project.get("metadata", {}).get("project_name", "documentation")
    filename = f"{project_name}_docagent.docx".replace(" ", "_").lower()

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )