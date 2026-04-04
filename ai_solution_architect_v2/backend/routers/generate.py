"""
generate.py  —  API routes for AI Solution Architect

Routes:
  POST /generate-pptx          — Full pipeline: BRD + tech doc → .pptx download
  POST /generate-pptx-from-json — Re-generate .pptx from existing architecture JSON
  POST /extract-text           — Extract text from uploaded PDF/DOCX/TXT/MD
"""

from dotenv import load_dotenv
load_dotenv()

import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import Response

from models.response_models import GenerateRequest
from services.orchestrator import OrchestratorService
from agents.prompt_builder import CUSTOM_SLIDE_PROMPT, build_user_message
from services.pptx_service import PptxService
from services.file_extractor import extract_text

router = APIRouter()


# ── Dependency factories ──────────────────────────────────────

def get_orchestrator():
    return OrchestratorService()

def get_pptx_service():
    return PptxService()


# ── Helper: build PPTX response ──────────────────────────────

def _pptx_response(pptx_bytes: bytes) -> Response:
    return Response(
        content=pptx_bytes,
        media_type=(
            "application/vnd.openxmlformats-officedocument"
            ".presentationml.presentation"
        ),
        headers={"Content-Disposition": 'attachment; filename="architecture.pptx"'},
    )


# ── Routes ────────────────────────────────────────────────────

@router.post(
    "/generate-pptx",
    response_class=Response,
    summary="Full pipeline: BRD → architecture JSON → PowerPoint",
)
async def generate_pptx(
    brd_text: str = Form(...),
    tech_doc_text: str = Form(default=""),
    selected_slides: str = Form(default=""),
    custom_slides: str = Form(default=""),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    pptx_service: PptxService = Depends(get_pptx_service),
):
    try:
        print("[generate.py] ════════════════════════════════════════════════════════════")
        print(f"[generate.py] Starting PPT generation (BRD: {len(brd_text)} chars)")
        
        payload = GenerateRequest(brd_text=brd_text, tech_doc_text=tech_doc_text)
        result  = await orchestrator.run(payload)
        print(f"[generate.py] Orchestrator completed, generating PPTX...")

        # model_dump_json() serialises all public Pydantic fields.
        # _raw_arch is set via model_post_init/set_raw_architecture, invisible to Pydantic serialisation.
        # We restore it here so the JS generator gets id/label components
        # and connections for the draw.io diagram render.
        result_dict = json.loads(result.model_dump_json())
        raw_arch = result.get_raw_architecture()
        
        print(f"[generate.py] Raw architecture present: {bool(raw_arch)}")
        if raw_arch and isinstance(raw_arch, dict):
            arch_data = raw_arch.get("architecture", {})
            comps = arch_data.get("diagram_components") or arch_data.get("components") or []
            conns = arch_data.get("diagram_connections") or arch_data.get("connections") or []
            print(f"[generate.py] Architecture data: {len(comps)} components, {len(conns)} connections")
            result_dict["architecture"] = raw_arch

        # Pass slide selection and custom slides through to JS generator
        try:
            if selected_slides:
                # expected comma-separated values or JSON array
                try:
                    sel = json.loads(selected_slides)
                except Exception:
                    sel = [s.strip() for s in selected_slides.split(",") if s.strip()]
                result_dict["selected_slides"] = sel
            if custom_slides:
                try:
                    cs = json.loads(custom_slides)
                except Exception:
                    # expect lines like Title|Content OR single-line titles
                    cs = []
                    for line in custom_slides.splitlines():
                        if not line or not line.strip():
                            continue
                        if "|" in line:
                            t, c = line.split("|", 1)
                            cs.append({"title": t.strip(), "content": c.strip()})
                        else:
                            # Accept a single word/phrase — use it as title and as simple content
                            txt = line.strip()
                            cs.append({"title": txt, "content": txt})
                result_dict["custom_slides"] = cs
        except Exception as e:
            print(f"[generate.py] Warning: failed to parse slide selection/custom slides: {e}")

        # If user provided short custom-slide prompts (single-line titles),
        # expand them via the orchestrator's LLM client using the BRD and tech doc.
        try:
            cs_list = result_dict.get("custom_slides") or []
            expanded = []
            for cs in cs_list:
                title = (cs.get("title") or "").strip() if isinstance(cs, dict) else str(cs).strip()
                content = (cs.get("content") or "").strip() if isinstance(cs, dict) else ""
                if title and (not content or content == title):
                    # Build user message with BRD + tech doc for context
                    user_msg = build_user_message(brd_text, tech_doc_text)
                    user_msg += "\n\n=== CUSTOM SLIDE TOPIC ===\n" + title
                    try:
                        # Request structured JSON (title + bullets) from the model
                        generated_obj = await orchestrator.client.invoke(CUSTOM_SLIDE_PROMPT, user_msg)
                        # Expect a dict like {title:..., bullets:[...]}
                        if isinstance(generated_obj, dict):
                            gtitle = generated_obj.get("title") or title
                            bullets = generated_obj.get("bullets") or []
                            expanded.append({"title": gtitle, "bullets": bullets})
                        else:
                            # Fallback to plain string
                            gen_text = str(generated_obj).strip()
                            expanded.append({"title": title, "bullets": [gen_text]})
                    except Exception as e:
                        print(f"[generate.py] Warning: custom slide generation failed for '{title}': {e}")
                        expanded.append({"title": title, "bullets": [title]})
                else:
                    # Already structured or has explicit content
                    # Normalize to {title, bullets}
                    if content and isinstance(content, list):
                        bullets = content
                    elif content and isinstance(content, str):
                        bullets = [content]
                    else:
                        bullets = [title] if title else []
                    expanded.append({"title": title or "Custom", "bullets": bullets})
            if expanded:
                result_dict["custom_slides"] = expanded

            # Diagnostic logging: show what we are passing to the JS generator for custom slides
            try:
                cs_preview = result_dict.get("custom_slides")
                sel_preview = result_dict.get("selected_slides")
                print(f"[generate.py] selected_slides -> {sel_preview}")
                print(f"[generate.py] custom_slides -> {json.dumps(cs_preview) if cs_preview is not None else cs_preview}")
            except Exception:
                pass
        except Exception as e:
            print(f"[generate.py] Warning: custom slide processing failed: {e}")

        pptx_bytes = pptx_service.generate(result_dict)
        print(f"[generate.py] ✓ PPTX generated: {len(pptx_bytes)} bytes")
        print("[generate.py] ════════════════════════════════════════════════════════════")
        return _pptx_response(pptx_bytes)
    except Exception as e:
        print(f"[generate.py] FATAL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/generate-pptx-from-json",
    response_class=Response,
    summary="Re-generate PPTX from an existing architecture JSON string",
)
async def generate_pptx_from_json(
    architecture_json: str = Form(...),
    pptx_service: PptxService = Depends(get_pptx_service),
):
    """
    Skip the AI call — pass a previously-generated architecture JSON string
    and receive a fresh .pptx without re-running the model.

    The JSON must include architecture.components (with id + label fields)
    and architecture.connections for the draw.io diagram to render.
    """
    try:
        data = json.loads(architecture_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    try:
        pptx_bytes = pptx_service.generate(data)
        return _pptx_response(pptx_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/extract-text",
    summary="Extract plain text from an uploaded PDF, DOCX, TXT, or MD file",
)
async def extract_text_from_file(
    file: UploadFile = File(...),
):
    try:
        file_bytes = await file.read()
        text, warning = extract_text(file.filename, file_bytes)
        return {
            "filename": file.filename,
            "extracted_text": text,
            "char_count": len(text),
            "warning": warning,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")