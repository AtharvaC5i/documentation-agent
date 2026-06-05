import os
import time
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from core.assembler.document_builder import build_document
from core.review.review_manager import get_summary, get_final_sections
from core.state_store import get_project, update_project, get_collector

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


def _scan_code_examples(sections: List[Dict[str, Any]]) -> Dict[str, int]:
    total_examples = 0
    valid_examples = 0

    for sec in sections:
        content = sec.get("content", "") or ""
        fenced_blocks = re.findall(r"```[\s\S]*?```", content)
        total_examples += len(fenced_blocks)
        valid_examples += sum(1 for block in fenced_blocks if len(block.strip("`\n ")) > 0)

    invalid_examples = max(total_examples - valid_examples, 0)
    validity_score = round((valid_examples / total_examples * 100) if total_examples > 0 else 0.0, 1)

    return {
        "total_examples": total_examples,
        "valid_examples": valid_examples,
        "invalid_examples": invalid_examples,
        "validity_score": validity_score,
    }


@router.post("/assemble/{project_id}")
async def assemble_document(project_id: str, req: AssembleRequest):
    if not req.sections:
        raise HTTPException(status_code=400, detail="No sections provided.")

    collector = get_collector(project_id)

    try:
        review_summary = get_summary(project_id)
        review_cycles = review_summary.get("total", 0)
        if review_cycles > 0:
            sections_to_assemble = get_final_sections(project_id)
        else:
            sections_to_assemble = [s.model_dump() for s in req.sections]
    except Exception:
        review_cycles = 0
        sections_to_assemble = [s.model_dump() for s in req.sections]

    collector.record_review(
        review_cycles=review_cycles,
        review_cycle_source="manual" if review_cycles > 0 else "not_reviewed",
    )

    t_start = time.perf_counter()
    try:
        result = build_document(
            project_id=project_id,
            metadata=req.metadata,
            sections=sections_to_assemble,
        )
    except Exception as e:
        collector.record_error(
            stage="assembly",
            message=str(e),
            error_type="assembly",
            exception_type=type(e).__name__,
        )
        collector.record_assembly(
            output_file="",
            output_size_bytes=0,
            word_count=0,
            page_estimate=0,
            section_count=len(sections_to_assemble),
            duration_seconds=time.perf_counter() - t_start,
            success=False,
            output_validation_success=False,
            output_validation_error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))

    assembly_duration = time.perf_counter() - t_start

    output_size_bytes = 0
    if os.path.exists(result["file_path"]):
        output_size_bytes = os.path.getsize(result["file_path"])

    collector.record_assembly(
        output_file=os.path.basename(result["file_path"]),
        output_size_bytes=output_size_bytes,
        word_count=result.get("word_count", 0),
        page_estimate=result.get("page_estimate", 0),
        section_count=result.get("section_count", len(sections_to_assemble)),
        duration_seconds=assembly_duration,
        success=True,
        output_validation_success=result.get("output_validation_success", True),
        output_validation_error=result.get("output_validation_error"),
    )

    code_example_stats = _scan_code_examples(sections_to_assemble)
    collector.record_code_example_validity(
        total_examples=code_example_stats["total_examples"],
        valid_examples=code_example_stats["valid_examples"],
        invalid_examples=code_example_stats["invalid_examples"],
        validation_method="fenced_block_presence",
    )

    update_project(project_id, "assembled_file_path", result["file_path"])

    return {
        "project_id": project_id,
        "file_path": result["file_path"],
        "word_count": result["word_count"],
        "page_estimate": result["page_estimate"],
        "section_count": result["section_count"],
        "status": "assembled",
    }


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