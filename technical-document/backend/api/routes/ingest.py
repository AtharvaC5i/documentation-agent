import uuid
import json
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from api.schemas.ingest_schema import GithubIngestRequest, IngestResponse, ProjectMetadata
from core.ingestion.github_cloner import clone_github_repo
from core.ingestion.zip_extractor import extract_zip
from core.ingestion.file_filter import filter_codebase
from core.analysis.tree_sitter_analyzer import analyze_codebase
from core.state_store import set_project, get_project

from dotenv import load_dotenv
load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join("..", "storage"))
REPOS_DIR   = os.path.join(STORAGE_DIR, "repos")

router = APIRouter()


@router.post("/github", response_model=IngestResponse)
async def ingest_github(request: GithubIngestRequest):
    project_id = str(uuid.uuid4())
    repo_path = os.path.join(REPOS_DIR, project_id)

    try:
        clone_github_repo(url=request.github_url, token=request.github_token, dest=repo_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clone failed: {str(e)}")

    filtered_files = filter_codebase(repo_path)
    analysis       = analyze_codebase(filtered_files)

    set_project(project_id, {
        "metadata":       request.metadata.model_dump(),
        "repo_path":      repo_path,
        "filtered_files": filtered_files,
        "analysis":       analysis.model_dump(),
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
    file:         UploadFile = File(...),
    project_name: str = Form(...),
    client_name:  str = Form(...),
    team_members: str = Form(default="[]"),
    description:  str = Form(default=""),
):
    project_id = str(uuid.uuid4())
    repo_path  = os.path.join("storage", "repos", project_id)

    try:
        members = json.loads(team_members)
    except json.JSONDecodeError:
        members = []

    try:
        await extract_zip(upload_file=file, dest=repo_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

    filtered_files = filter_codebase(repo_path)
    analysis       = analyze_codebase(filtered_files)

    set_project(project_id, {
        "metadata": {
            "project_name": project_name,
            "client_name":  client_name,
            "team_members": members,
            "description":  description,
        },
        "repo_path":      repo_path,
        "filtered_files": filtered_files,
        "analysis":       analysis.model_dump(),
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
    from core.state_store import get_project
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {
        "analysis":        project["analysis"],
        "filtered_files":  project["filtered_files"][:30],  # first 30 only
        "total_files":     len(project["filtered_files"]),
        "metadata":        project["metadata"],
    }
