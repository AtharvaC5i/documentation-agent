import time
import re

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional

from core.state_store import get_project, update_project, get_collector
from core.analysis.analysis_models import AnalysisResult
from core.generation.section_generator import generate_section

router = APIRouter()

_generation_state: Dict[str, Dict] = {}


class GenerationStatusResponse(BaseModel):
    project_id: str
    total_sections: int
    completed: int
    in_progress: Optional[str]
    sections: Dict[str, dict]
    finished: bool


def _count_documented_elements(sections: Dict[str, dict]) -> Dict[str, int]:
    documented_apis = 0
    documented_classes = 0
    documented_functions = 0

    api_patterns = [r"@app\.", r"@router\.", r"route\(", r"\bendpoint\b", r"\bapi\b"]
    class_patterns = [r"\bclass\s+\w+", r"\bstruct\s+\w+", r"\binterface\s+\w+", r"\benum\s+\w+"]
    func_patterns = [r"\bdef\s+\w+", r"\bfunction\s+\w+", r"\b\w+\s*=>", r"\bfn\s+\w+"]

    for sec in sections.values():
        content = sec.get("content", "") or ""
        lowered = content.lower()

        for p in api_patterns:
            documented_apis += len(re.findall(p, lowered))
        for p in class_patterns:
            documented_classes += len(re.findall(p, lowered))
        for p in func_patterns:
            documented_functions += len(re.findall(p, lowered))

    return {
        "documented_apis": documented_apis,
        "documented_classes": documented_classes,
        "documented_functions": documented_functions,
    }


def _run_generation(project_id: str, sections: List[str], analysis_dict: dict):
    analysis = AnalysisResult(**analysis_dict)
    collector = get_collector(project_id)
    _generation_state[project_id]["finished"] = False

    t_gen_start = time.perf_counter()
    llm_retries = 0
    sections_succeeded = 0
    sections_failed = 0
    per_section_scores: Dict[str, Optional[float]] = {}
    per_section_word_counts: Dict[str, int] = {}

    for section_name in sections:
        _generation_state[project_id]["in_progress"] = section_name
        _generation_state[project_id]["sections"][section_name] = {
            "status": "in_progress",
            "content": "",
            "quality_score": None,
            "regenerated": False,
        }

        try:
            result = generate_section(project_id, section_name, analysis)
            _generation_state[project_id]["sections"][section_name] = {
                "status": result["status"],
                "content": result["content"],
                "quality_score": result["quality_score"],
                "regenerated": result["regenerated"],
            }

            per_section_scores[section_name] = result.get("quality_score")
            per_section_word_counts[section_name] = len(result.get("content", "").split())

            if result["regenerated"]:
                llm_retries += 1
            if result["status"] in ("success", "low_quality"):
                sections_succeeded += 1
            else:
                sections_failed += 1

            usage = result.get("usage")
            if usage:
                collector.record_llm_call(
                    section_name=section_name,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                )

        except Exception as e:
            print(f"❌ [Generation Route] Failed on '{section_name}': {e}")
            collector.record_error(
                stage="generation",
                message=f"Section '{section_name}' failed: {str(e)}",
                error_type="timeout" if "timeout" in str(e).lower() else
                           "llm_rate_limit" if "rate" in str(e).lower() else
                           "empty_output" if "empty" in str(e).lower() else
                           "runtime",
                exception_type=type(e).__name__,
            )
            _generation_state[project_id]["sections"][section_name] = {
                "status": "failed",
                "content": "",
                "quality_score": 0.0,
                "regenerated": False,
            }
            per_section_scores[section_name] = 0.0
            per_section_word_counts[section_name] = 0
            sections_failed += 1

    total_gen_duration = time.perf_counter() - t_gen_start

    collector.record_generation(
        sections_attempted=len(sections),
        sections_succeeded=sections_succeeded,
        sections_failed=sections_failed,
        per_section_scores=per_section_scores,
        total_duration_seconds=total_gen_duration,
        llm_retries=llm_retries,
        per_section_word_counts=per_section_word_counts,
    )

    generated_sections = _generation_state[project_id]["sections"]
    doc_counts = _count_documented_elements(generated_sections)

    collector.record_codebase_coverage(
        discovered_apis=analysis.discovered_apis,
        documented_apis=doc_counts["documented_apis"],
        discovered_classes=analysis.discovered_classes,
        documented_classes=doc_counts["documented_classes"],
        discovered_functions=analysis.discovered_functions,
        documented_functions=doc_counts["documented_functions"],
    )

    _generation_state[project_id]["in_progress"] = None
    _generation_state[project_id]["finished"] = True

    update_project(project_id, "generated_sections", generated_sections)
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

    _generation_state[project_id] = {
        "sections": {
            s: {"status": "pending", "content": "", "quality_score": None, "regenerated": False}
            for s in confirmed_sections
        },
        "in_progress": None,
        "finished": False,
    }

    background_tasks.add_task(
        _run_generation,
        project_id,
        confirmed_sections,
        project["analysis"],
    )

    return {
        "message": f"Generation started for {len(confirmed_sections)} sections.",
        "project_id": project_id,
        "sections": confirmed_sections,
    }


@router.get("/status/{project_id}", response_model=GenerationStatusResponse)
def get_generation_status(project_id: str):
    if project_id not in _generation_state:
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
        raise HTTPException(status_code=404, detail="No generation job found for this project.")

    state = _generation_state[project_id]
    sections = state["sections"]
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
    if project_id in _generation_state:
        state = _generation_state[project_id]
        if not state.get("finished"):
            raise HTTPException(status_code=400, detail="Generation not finished yet.")
        sections_raw = state["sections"]
    else:
        project = get_project(project_id)
        if not project or not project.get("generated_sections"):
            raise HTTPException(status_code=404, detail="No generation results found for this project.")
        sections_raw = project["generated_sections"]

    sections = [
        {
            "name": name,
            "content": sec.get("content", ""),
            "order": i,
            "quality_score": sec.get("quality_score", 0),
            "status": sec.get("status", "success"),
            "regenerated": sec.get("regenerated", False),
        }
        for i, (name, sec) in enumerate(sections_raw.items())
    ]

    return {"project_id": project_id, "sections": sections}