from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
from core.state_store import get_project, update_project
from core.analysis.analysis_models import AnalysisResult
from core.generation.section_generator import generate_section

router = APIRouter()

# In-memory generation state per project
# { project_id: { section_name: { status, content, quality_score, regenerated } } }
_generation_state: Dict[str, Dict] = {}


class GenerationStatusResponse(BaseModel):
    project_id:       str
    total_sections:   int
    completed:        int
    in_progress:      Optional[str]
    sections:         Dict[str, dict]
    finished:         bool


def _run_generation(project_id: str, sections: List[str], analysis_dict: dict):
    """
    Background task — generates all sections sequentially.
    Updates _generation_state as each section completes.
    """
    analysis = AnalysisResult(**analysis_dict)
    _generation_state[project_id]["finished"] = False

    for section_name in sections:
        _generation_state[project_id]["in_progress"] = section_name
        _generation_state[project_id]["sections"][section_name] = {
            "status":        "in_progress",
            "content":       "",
            "quality_score": None,
            "regenerated":   False,
        }

        try:
            result = generate_section(project_id, section_name, analysis)
            _generation_state[project_id]["sections"][section_name] = {
                "status":        result["status"],
                "content":       result["content"],
                "quality_score": result["quality_score"],
                "regenerated":   result["regenerated"],
            }
        except Exception as e:
            print(f"❌ [Generation Route] Failed on '{section_name}': {e}")
            _generation_state[project_id]["sections"][section_name] = {
                "status":        "failed",
                "content":       "",
                "quality_score": 0.0,
                "regenerated":   False,
            }

    _generation_state[project_id]["in_progress"] = None
    _generation_state[project_id]["finished"]    = True

    # Persist generated content to project state
    update_project(project_id, "generated_sections",
                   _generation_state[project_id]["sections"])

    print(f"✅ [Generation Route] All sections complete for project '{project_id}'")


@router.post("/start/{project_id}")
def start_generation(project_id: str, background_tasks: BackgroundTasks):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    confirmed_sections = project.get("confirmed_sections", [])
    if not confirmed_sections:
        raise HTTPException(status_code=400, detail="No confirmed sections found. Complete Phase 2 first.")

    if not project.get("context_built"):
        raise HTTPException(status_code=400, detail="Context not built yet. Complete Phase 3 first.")

    # Initialise state
    _generation_state[project_id] = {
        "sections":    {s: {"status": "pending", "content": "", "quality_score": None, "regenerated": False}
                        for s in confirmed_sections},
        "in_progress": None,
        "finished":    False,
    }

    background_tasks.add_task(
        _run_generation,
        project_id,
        confirmed_sections,
        project["analysis"],
    )

    return {
        "message":    f"Generation started for {len(confirmed_sections)} sections.",
        "project_id": project_id,
        "sections":   confirmed_sections,
    }


@router.get("/status/{project_id}", response_model=GenerationStatusResponse)
def get_generation_status(project_id: str):
    if project_id not in _generation_state:
        # Check if already persisted from a previous run
        project = get_project(project_id)
        if project and project.get("generated_sections"):
            sections = project["generated_sections"]
            return GenerationStatusResponse(
                project_id=project_id,
                total_sections=len(sections),
                completed=len(sections),
                in_progress=None,
                sections=sections,
                finished=True,
            )
        raise HTTPException(status_code=404, detail="No generation job found for this project. Start generation first.")

    state     = _generation_state[project_id]
    sections  = state["sections"]
    completed = sum(1 for s in sections.values() if s["status"] in ("success", "low_quality", "failed"))

    return GenerationStatusResponse(
        project_id=project_id,
        total_sections=len(sections),
        completed=completed,
        in_progress=state["in_progress"],
        sections=sections,
        finished=state["finished"],
    )


@router.get("/results/{project_id}")
def get_generation_results(project_id: str):
    """Returns full section contents for assembly."""

    # Try in-memory state first
    if project_id in _generation_state:
        state = _generation_state[project_id]
        if not state.get("finished"):
            raise HTTPException(status_code=400, detail="Generation not finished yet.")
        sections_raw = state["sections"]

    else:
        # Fall back to persisted state
        project = get_project(project_id)
        if not project or not project.get("generated_sections"):
            raise HTTPException(status_code=404, detail="No generation results found for this project.")
        sections_raw = project["generated_sections"]

    sections = [
        {
            "name":          name,
            "content":       sec.get("content", ""),
            "order":         i,
            "quality_score": sec.get("quality_score", 0),
        }
        for i, (name, sec) in enumerate(sections_raw.items())
    ]

    return {"project_id": project_id, "sections": sections}
