"""
BRD Generation Agent — FastAPI Backend
"""

from utils.env_loader import load_env
load_env()

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import uuid
import os
import json
from typing import Optional, List
from pydantic import BaseModel

from pipelines.extraction_pipeline import ExtractionPipeline
from pipelines.generation_pipeline import GenerationPipeline
from pipelines.document_pipeline import DocumentPipeline
from models.project import Project
from storage.file_store import FileProjectStore
from utils.file_utils import load_synthetic_data
from features.living_brd import detect_changes, generate_change_report, apply_approved_changes
from features.followup_email import generate_followup_email
from features.traceability import build_traceability_matrix, generate_traceability_document
from utils.logger import info, success, warn, divider

app = FastAPI(title="BRD Generation Agent API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File-based persistent store — survives restarts
project_store = FileProjectStore()
divider("BRD AGENT STARTED")
info("STARTUP", f"Loaded {len(project_store.list_all())} existing projects from disk")

# ─── Request Models ────────────────────────────────────────────────────────

class ProjectCreateRequest(BaseModel):
    project_name: str
    client_name: str
    industry: str
    description: str
    team_members: List[str]

class SectionSelectionRequest(BaseModel):
    project_id: str
    selected_sections: List[str]
    custom_sections: List[str] = []

class SectionFeedbackRequest(BaseModel):
    project_id: str
    section_id: str
    feedback: str

class SectionApprovalRequest(BaseModel):
    project_id: str
    section_id: str
    approved: bool

class ConflictResolutionRequest(BaseModel):
    project_id: str
    conflict_id: str
    chosen_version: str
    custom_text: Optional[str] = None

class ApplyChangesRequest(BaseModel):
    project_id: str
    approved_change_ids: List[str]

# ─── Core Routes ───────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "BRD Agent API running", "version": "2.0.0"}


@app.get("/api/question-bank")
def get_question_bank():
    qb_path = os.path.join(os.path.dirname(__file__), "../synthetic_data/question_bank.json")
    with open(qb_path, "r") as f:
        return json.load(f)


@app.post("/api/projects/create")
async def create_project(request: ProjectCreateRequest):
    project_id = str(uuid.uuid4())
    project = Project(
        id=project_id,
        project_name=request.project_name,
        client_name=request.client_name,
        industry=request.industry,
        description=request.description,
        team_members=request.team_members,
        status="created"
    )
    project_store.save(project)
    info("API", f"Project created: {request.project_name} [{project_id[:8]}]")
    return {"project_id": project_id, "status": "created"}


@app.post("/api/projects/{project_id}/upload-transcript")
async def upload_transcript(project_id: str, file: UploadFile = File(...)):
    project = _get_or_404(project_id)
    content = await file.read()
    transcript_text = content.decode("utf-8", errors="ignore")
    project.transcript_raw = transcript_text
    project.status = "transcript_uploaded"
    project_store.save(project)
    project_store.save_input_files(project_id, transcript_text, None)
    info("API", f"Transcript uploaded: {len(transcript_text)} chars")
    return {"status": "uploaded", "chars": len(transcript_text)}


@app.post("/api/projects/{project_id}/upload-user-stories")
async def upload_user_stories(project_id: str, file: UploadFile = File(...)):
    project = _get_or_404(project_id)
    content = await file.read()
    stories_text = content.decode("utf-8", errors="ignore")
    project.user_stories_raw = stories_text
    project_store.save(project)
    project_store.save_input_files(project_id, None, stories_text)
    info("API", f"User stories uploaded: {len(stories_text)} chars")
    return {"status": "uploaded", "chars": len(stories_text)}


@app.post("/api/projects/{project_id}/load-synthetic")
async def load_synthetic(project_id: str):
    project = _get_or_404(project_id)
    data = load_synthetic_data()
    project.transcript_raw = data["transcript"]
    project.user_stories_raw = data["user_stories"]
    project.status = "transcript_uploaded"
    project_store.save(project)
    project_store.save_input_files(project_id, data["transcript"], data["user_stories"])
    info("API", "Synthetic data loaded")
    return {"status": "synthetic_loaded"}


@app.post("/api/projects/{project_id}/extract")
async def extract_requirements(project_id: str, background_tasks: BackgroundTasks):
    project = _get_or_404(project_id)
    if not project.transcript_raw and not project.user_stories_raw:
        raise HTTPException(status_code=400, detail="No input data. Upload files first.")
    project.status = "extracting"
    project_store.save(project)
    background_tasks.add_task(run_extraction, project_id)
    return {"status": "extraction_started"}


@app.get("/api/projects/{project_id}/status")
def get_project_status(project_id: str):
    project = _get_or_404(project_id)
    return {
        "status": project.status,
        "progress": project.progress,
        "progress_message": project.progress_message,
        "version": project.version,
    }


@app.get("/api/projects/{project_id}/requirements")
def get_requirements(project_id: str):
    project = _get_or_404(project_id)
    return {
        "requirements": [r.dict() for r in project.requirements_pool],
        "glossary": project.glossary,
    }


@app.get("/api/projects/{project_id}/conflicts")
def get_conflicts(project_id: str):
    project = _get_or_404(project_id)
    return {
        "conflicts": project.conflicts,
        "gaps": project.gaps,
        "coverage": project.section_coverage,
    }


@app.post("/api/projects/{project_id}/resolve-conflict")
def resolve_conflict(request: ConflictResolutionRequest):
    project = _get_or_404(request.project_id)
    for c in project.conflicts:
        if c["id"] == request.conflict_id:
            c["resolved"] = True
            c["chosen"] = request.chosen_version
            c["custom_text"] = request.custom_text
            break
    project_store.save(project)
    return {"status": "resolved"}


@app.get("/api/projects/{project_id}/suggested-sections")
def get_suggested_sections(project_id: str):
    project = _get_or_404(project_id)
    return {"suggested_sections": project.suggested_sections}


@app.post("/api/projects/{project_id}/select-sections")
async def select_sections(request: SectionSelectionRequest, background_tasks: BackgroundTasks):
    project = _get_or_404(request.project_id)
    project.selected_sections = request.selected_sections + request.custom_sections
    project.status = "generating"
    project.progress = 0
    project_store.save(project)
    background_tasks.add_task(run_generation, request.project_id)
    return {"status": "generation_started", "sections": project.selected_sections}


@app.get("/api/projects/{project_id}/sections")
def get_sections(project_id: str):
    project = _get_or_404(project_id)
    return {"sections": project.generated_sections}


@app.post("/api/projects/{project_id}/approve-section")
def approve_section(request: SectionApprovalRequest):
    project = _get_or_404(request.project_id)
    for s in project.generated_sections:
        if s["id"] == request.section_id:
            s["approved"] = request.approved
            s["status"] = "approved" if request.approved else "needs_revision"
            break
    project_store.save(project)
    return {"status": "updated"}


@app.post("/api/projects/{project_id}/regenerate-section")
async def regenerate_section(request: SectionFeedbackRequest, background_tasks: BackgroundTasks):
    _get_or_404(request.project_id)
    background_tasks.add_task(run_section_regeneration, request.project_id, request.section_id, request.feedback)
    return {"status": "regeneration_started"}


class SaveSectionContentRequest(BaseModel):
    project_id: str
    section_id: str
    content: str

@app.post("/api/projects/{project_id}/save-section-content")
def save_section_content(request: SaveSectionContentRequest):
    """Save directly edited section content from the review page."""
    project = _get_or_404(request.project_id)
    for section in project.generated_sections:
        if section["id"] == request.section_id:
            section["content"] = request.content
            section["status"] = "edited"
            break
    project_store.save(project)
    info("API", f"Section content saved: {request.section_id[:8]}")
    return {"status": "saved"}


@app.post("/api/projects/{project_id}/generate-document")
async def generate_document(project_id: str, background_tasks: BackgroundTasks):
    _get_or_404(project_id)
    background_tasks.add_task(run_document_generation, project_id)
    return {"status": "document_generation_started"}


@app.get("/api/projects/{project_id}/download")
def download_document(project_id: str):
    project = _get_or_404(project_id)
    if not project.document_path or not os.path.exists(project.document_path):
        raise HTTPException(status_code=404, detail="Document not yet generated")
    safe_name = project.project_name.replace(" ", "_").replace("/", "_")
    filename = f"BRD_{safe_name}_v{project.version}.docx"
    return FileResponse(
        path=project.document_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        }
    )


@app.get("/api/projects")
def list_projects():
    return {"projects": [p.dict() for p in project_store.list_all()]}


# ─── Follow-Up Email ───────────────────────────────────────────────────────

@app.post("/api/projects/{project_id}/generate-followup-email")
async def gen_followup_email(project_id: str, background_tasks: BackgroundTasks):
    _get_or_404(project_id)
    background_tasks.add_task(run_followup_email, project_id)
    return {"status": "email_generation_started"}


@app.get("/api/projects/{project_id}/followup-email")
def get_followup_email(project_id: str):
    project = _get_or_404(project_id)
    return {
        "email_draft": project.followup_email_draft,
        "gap_count": len(project.gaps),
        "conflict_count": sum(1 for c in project.conflicts if not c.get("resolved")),
    }


# ─── Living BRD ────────────────────────────────────────────────────────────

@app.post("/api/projects/{project_id}/upload-new-transcript")
async def upload_new_transcript(project_id: str, file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a follow-up transcript to an existing completed project."""
    project = _get_or_404(project_id)
    if project.status not in ("complete", "review", "extracted"):
        raise HTTPException(status_code=400, detail="Project must be complete before uploading a new transcript.")
    content = await file.read()
    new_transcript = content.decode("utf-8", errors="ignore")
    project.transcript_raw = new_transcript
    project.status = "detecting_changes"
    project_store.save(project)
    background_tasks.add_task(run_change_detection, project_id, new_transcript)
    return {"status": "change_detection_started"}


@app.get("/api/projects/{project_id}/changes")
def get_changes(project_id: str):
    project = _get_or_404(project_id)
    return {
        "pending_changes": project.pending_changes,
        "change_report": project.change_report,
        "current_version": project.version,
    }


@app.post("/api/projects/{project_id}/apply-changes")
async def apply_changes(request: ApplyChangesRequest):
    project = _get_or_404(request.project_id)
    project = apply_approved_changes(project, request.approved_change_ids)
    project_store.save(project)
    return {
        "status": "changes_applied",
        "new_version": project.version,
        "requirements_count": len(project.requirements_pool),
    }


@app.get("/api/projects/{project_id}/version-history")
def get_version_history(project_id: str):
    project = _get_or_404(project_id)
    return {
        "current_version": project.version,
        "history": project.previous_versions,
    }


# ─── Traceability Matrix ───────────────────────────────────────────────────

@app.post("/api/projects/{project_id}/generate-traceability")
async def gen_traceability(project_id: str, background_tasks: BackgroundTasks):
    _get_or_404(project_id)
    background_tasks.add_task(run_traceability, project_id)
    return {"status": "traceability_generation_started"}


@app.get("/api/projects/{project_id}/traceability")
def get_traceability(project_id: str):
    project = _get_or_404(project_id)
    return {
        "matrix": project.traceability_matrix,
        "doc_ready": project.traceability_doc_path is not None and os.path.exists(project.traceability_doc_path or ""),
    }


@app.get("/api/projects/{project_id}/download-traceability")
def download_traceability(project_id: str):
    project = _get_or_404(project_id)
    if not project.traceability_doc_path or not os.path.exists(project.traceability_doc_path):
        raise HTTPException(status_code=404, detail="Traceability document not yet generated")
    safe_name = project.project_name.replace(" ", "_")
    filename = f"Traceability_{safe_name}_v{project.version}.docx"
    return FileResponse(
        path=project.traceability_doc_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── Helper ────────────────────────────────────────────────────────────────

def _get_or_404(project_id: str) -> Project:
    project = project_store.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ─── Background Tasks ──────────────────────────────────────────────────────

async def run_extraction(project_id: str):
    project = project_store.get(project_id)
    try:
        await ExtractionPipeline(project, project_store).run()
    except Exception as e:
        project.status = "error"
        project.progress_message = f"Extraction failed: {str(e)[:200]}"
        project_store.save(project)


async def run_generation(project_id: str):
    project = project_store.get(project_id)
    try:
        await GenerationPipeline(project, project_store).run()
    except Exception as e:
        project.status = "error"
        project.progress_message = f"Generation failed: {str(e)[:200]}"
        project_store.save(project)


async def run_section_regeneration(project_id: str, section_id: str, feedback: str):
    project = project_store.get(project_id)
    try:
        await GenerationPipeline(project, project_store).regenerate_section(section_id, feedback)
    except Exception as e:
        project.status = "error"
        project.progress_message = f"Regeneration failed: {str(e)[:200]}"
        project_store.save(project)


async def run_document_generation(project_id: str):
    project = project_store.get(project_id)
    try:
        pipeline = DocumentPipeline(project, project_store)
        await pipeline.run()
        # Auto-generate traceability matrix after BRD is complete
        matrix = build_traceability_matrix(project)
        project.traceability_matrix = matrix
        project_store.save(project)
        info("BG", "Traceability matrix built automatically after BRD generation")
    except Exception as e:
        project.status = "error"
        project.progress_message = f"Document generation failed: {str(e)[:200]}"
        project_store.save(project)


async def run_followup_email(project_id: str):
    project = project_store.get(project_id)
    try:
        draft = await generate_followup_email(project)
        project.followup_email_draft = draft
        project_store.save(project)
        success("BG", "Follow-up email draft ready")
    except Exception as e:
        warn("BG", f"Follow-up email failed: {e}")


async def run_change_detection(project_id: str, new_transcript: str):
    project = project_store.get(project_id)
    try:
        from pipelines.extraction_pipeline import ExtractionPipeline, clean_transcript
        cleaned = clean_transcript(new_transcript)
        pipeline = ExtractionPipeline(project, project_store)
        new_requirements = await pipeline._extract_from_transcript(cleaned)

        changes = await detect_changes(project, new_requirements)
        report = await generate_change_report(project, changes)

        project.pending_changes = changes
        project.change_report = report
        project.status = "changes_detected"
        project_store.save(project)
        success("BG", f"Change detection complete: {len(changes)} changes found")
    except Exception as e:
        project.status = "error"
        project.progress_message = f"Change detection failed: {str(e)[:200]}"
        project_store.save(project)


async def run_traceability(project_id: str):
    project = project_store.get(project_id)
    try:
        matrix = build_traceability_matrix(project)
        doc_path = generate_traceability_document(project, matrix)
        project.traceability_matrix = matrix
        project.traceability_doc_path = doc_path
        project_store.save(project)
        success("BG", "Traceability document ready")
    except Exception as e:
        warn("BG", f"Traceability generation failed: {e}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
