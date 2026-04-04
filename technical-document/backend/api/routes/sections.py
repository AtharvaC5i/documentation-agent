from fastapi import APIRouter, HTTPException
from api.schemas.section_schema import (
    SectionSuggestionsResponse, SectionConfirmRequest, SectionConfirmResponse,
)
from core.section_selector.ai_suggester import suggest_sections_ai   # ← changed
from core.analysis.analysis_models import AnalysisResult
from core.state_store import get_project, update_project


router = APIRouter()


@router.get("/suggest/{project_id}", response_model=SectionSuggestionsResponse)
def get_section_suggestions(project_id: str):
    print("🔵 [sections.py] /suggest endpoint hit") 
    project = get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found. It may have been lost due to a server restart. Please re-ingest the codebase."
        )

    analysis    = AnalysisResult(**project["analysis"])
    print("🔵 [sections.py] Calling suggest_sections_ai...")
    suggestions = suggest_sections_ai(analysis)              # ← changed

    return SectionSuggestionsResponse(project_id=project_id, suggestions=suggestions)


@router.post("/confirm", response_model=SectionConfirmResponse)
def confirm_sections(request: SectionConfirmRequest):
    project = get_project(request.project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{request.project_id}' not found."
        )

    final_sections = request.confirmed_sections + request.custom_sections
    if not final_sections:
        raise HTTPException(status_code=400, detail="At least one section must be selected.")

    update_project(request.project_id, "confirmed_sections", final_sections)

    return SectionConfirmResponse(
        project_id=request.project_id,
        final_sections=final_sections,
        message=f"{len(final_sections)} sections confirmed and ready for context building.",
    )
