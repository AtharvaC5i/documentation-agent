from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from core.assembler.document_builder import build_document

router = APIRouter()


class SectionItem(BaseModel):
    name: str
    content: str
    order: int
    quality_score: Optional[float] = None


class AssembleRequest(BaseModel):
    project_id: str
    metadata: Dict[str, Any]
    sections: List[SectionItem]


@router.post("/assemble/{project_id}")
async def assemble_document(project_id: str, req: AssembleRequest):
    if not req.sections:
        raise HTTPException(status_code=400, detail="No sections provided.")

    try:
        result = build_document(
            project_id=project_id,
            metadata=req.metadata,
            sections=[s.model_dump() for s in req.sections],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "project_id": project_id,
        "file_path": result["file_path"],
        "word_count": result["word_count"],
        "page_estimate": result["page_estimate"],
        "section_count": result["section_count"],
        "status": "assembled",
    }
