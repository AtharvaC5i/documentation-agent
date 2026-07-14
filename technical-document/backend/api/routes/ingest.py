import uuid
import json
import os
import time

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from api.schemas.ingest_schema import GithubIngestRequest, IngestResponse
from core.ingestion.github_cloner import clone_github_repo
from core.ingestion.zip_extractor import extract_zip
from core.ingestion.file_filter import filter_codebase
from core.analysis.tree_sitter_analyzer import analyze_codebase
from core.analysis.tech_stack_detector import detect_tech_stack, build_tech_stack_comparison
from core.state_store import set_project, get_project, reset_collector

from dotenv import load_dotenv
load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join("..", "storage"))
REPOS_DIR = os.path.join(STORAGE_DIR, "repos")

router = APIRouter()


def _record_input_profile(collector, analysis_dict: dict, repo_path: str):
    try:
        langs = analysis_dict.get("languages", [])
        primary_language = langs[0] if langs else "unknown"

        repo_size_bytes = sum(
            os.path.getsize(os.path.join(dp, f))
            for dp, _, files in os.walk(repo_path)
            for f in files
        )

        collector.record_input_profile(
            total_loc=analysis_dict.get("total_loc", 0),
            primary_language=primary_language,
            language_breakdown={lang: 1 for lang in langs},
            repo_size_kb=repo_size_bytes / 1024,
        )
    except Exception as e:
        print(f"⚠️ [ingest.py] Could not record input profile: {e}")


@router.post("/github", response_model=IngestResponse)
async def ingest_github(request: GithubIngestRequest):
    project_id = str(uuid.uuid4())
    repo_path = os.path.join(REPOS_DIR, project_id)
    collector = reset_collector(project_id)

    t_start = time.perf_counter()
    try:
        clone_github_repo(url=request.github_url, token=request.github_token, dest=repo_path)
    except Exception as e:
        collector.record_error(
            stage="ingestion",
            message=str(e),
            error_type="api",
            exception_type=type(e).__name__,
        )
        collector.record_ingestion("github", 0, 0, time.perf_counter() - t_start, False)
        raise HTTPException(status_code=500, detail=f"Clone failed: {str(e)}")

    try:
        filtered_files = filter_codebase(repo_path)
        analysis = analyze_codebase(filtered_files)
        duration = time.perf_counter() - t_start
        total_files_found = sum(len(files) for _, _, files in os.walk(repo_path))

        collector.record_ingestion(
            source_type="github",
            total_files_found=total_files_found,
            files_after_filter=len(filtered_files),
            duration_seconds=duration,
            success=True,
        )
        _record_input_profile(collector, analysis.model_dump(), repo_path)

        collector.record_tech_stack(
            detected_stack=analysis.detected_stack,
            actual_stack=analysis.actual_stack,
            correct_matches=analysis.correct_matches,
            missed_items=analysis.missed_items,
            false_positives=analysis.false_positives,
            accuracy_score=analysis.tech_stack_accuracy_score,
        )
    except Exception as e:
        collector.record_error(
            stage="ingestion",
            message=str(e),
            error_type="ingestion" if "filter" in str(e).lower() or "find" in str(e).lower() else "parsing",
            exception_type=type(e).__name__,
        )
        collector.record_ingestion("github", 0, 0, time.perf_counter() - t_start, False)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    set_project(project_id, {
        "metadata": request.metadata.model_dump(),
        "repo_path": repo_path,
        "filtered_files": filtered_files,
        "analysis": analysis.model_dump(),
    })

    return IngestResponse(
        project_id=project_id,
        message="Repository cloned, filtered, and analyzed successfully.",
        filtered_file_count=len(filtered_files),
        total_loc=analysis.total_loc,
        analysis=analysis.model_dump(),
    )


@router.post("/zip", response_model=IngestResponse)
async def ingest_zip(
    file: UploadFile = File(...),
    project_name: str = Form(...),
    client_name: str = Form(...),
    team_members: str = Form(default="[]"),
    description: str = Form(default=""),
):
    project_id = str(uuid.uuid4())
    repo_path = os.path.join("storage", "repos", project_id)
    collector = reset_collector(project_id)

    try:
        members = json.loads(team_members)
    except json.JSONDecodeError:
        members = []

    t_start = time.perf_counter()
    try:
        await extract_zip(upload_file=file, dest=repo_path)
    except Exception as e:
        collector.record_error(
            stage="ingestion",
            message=str(e),
            error_type="parsing",
            exception_type=type(e).__name__,
        )
        collector.record_ingestion("zip", 0, 0, time.perf_counter() - t_start, False)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    try:
        filtered_files = filter_codebase(repo_path)
        analysis = analyze_codebase(filtered_files)
        duration = time.perf_counter() - t_start
        total_files_found = sum(len(files) for _, _, files in os.walk(repo_path))

        collector.record_ingestion(
            source_type="zip",
            total_files_found=total_files_found,
            files_after_filter=len(filtered_files),
            duration_seconds=duration,
            success=True,
        )
        _record_input_profile(collector, analysis.model_dump(), repo_path)

        collector.record_tech_stack(
            detected_stack=analysis.detected_stack,
            actual_stack=analysis.actual_stack,
            correct_matches=analysis.correct_matches,
            missed_items=analysis.missed_items,
            false_positives=analysis.false_positives,
            accuracy_score=analysis.tech_stack_accuracy_score,
        )
    except Exception as e:
        collector.record_error(
            stage="ingestion",
            message=str(e),
            error_type="ingestion" if "filter" in str(e).lower() or "find" in str(e).lower() else "parsing",
            exception_type=type(e).__name__,
        )
        collector.record_ingestion("zip", 0, 0, time.perf_counter() - t_start, False)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    set_project(project_id, {
        "metadata": {
            "project_name": project_name,
            "client_name": client_name,
            "team_members": members,
            "description": description,
        },
        "repo_path": repo_path,
        "filtered_files": filtered_files,
        "analysis": analysis.model_dump(),
    })

    return IngestResponse(
        project_id=project_id,
        message="Zip extracted, filtered, and analyzed successfully.",
        filtered_file_count=len(filtered_files),
        total_loc=analysis.total_loc,
        analysis=analysis.model_dump(),
    )


@router.get("/debug/{project_id}")
def debug_project(project_id: str):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {
        "analysis": project["analysis"],
        "filtered_files": project["filtered_files"][:30],
        "total_files": len(project["filtered_files"]),
        "metadata": project["metadata"],
    }