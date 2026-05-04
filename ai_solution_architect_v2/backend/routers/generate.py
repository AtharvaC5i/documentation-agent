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
    summary="Full pipeline: BRD and/or Tech Doc → architecture JSON → PowerPoint",
)
async def generate_pptx(
    brd_text: str = Form(default=""),
    tech_doc_text: str = Form(default=""),
    selected_slides: str = Form(default=""),
    custom_slides: str = Form(default=""),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
    pptx_service: PptxService = Depends(get_pptx_service),
):
    try:
        if not brd_text.strip() and not tech_doc_text.strip():
            raise HTTPException(
                status_code=400,
                detail="At least one of BRD text or Technical Documentation is required"
            )

        print("[generate.py] ════════════════════════════════════════════════════════════")
        print(f"[generate.py] Starting PPT generation (BRD: {len(brd_text)} chars, TechDoc: {len(tech_doc_text)} chars)")

        payload = GenerateRequest(brd_text=brd_text, tech_doc_text=tech_doc_text)
        result  = await orchestrator.run(payload)
        print(f"[generate.py] Orchestrator completed, generating PPTX...")

        result_dict = json.loads(result.model_dump_json())
        raw_arch = result.get_raw_architecture()

        print(f"[generate.py] Raw architecture present: {bool(raw_arch)}")
        if raw_arch and isinstance(raw_arch, dict):
            arch_data = raw_arch.get("architecture", {})
            comps = arch_data.get("diagram_components") or arch_data.get("components") or []
            conns = arch_data.get("diagram_connections") or arch_data.get("connections") or []
            print(f"[generate.py] Architecture data: {len(comps)} components, {len(conns)} connections")
            result_dict["architecture"] = raw_arch

        # ── Parse selected_slides and custom_slides ───────────────────────
        try:
            if selected_slides:
                try:
                    sel = json.loads(selected_slides)
                except Exception:
                    sel = [s.strip() for s in selected_slides.split(",") if s.strip()]
                result_dict["selected_slides"] = sel

            if custom_slides:
                try:
                    # Try parsing as JSON first (in case frontend sends JSON array)
                    cs = json.loads(custom_slides)
                except Exception:
                    # Plain text — one topic per line
                    cs = []
                    for line in custom_slides.splitlines():
                        if not line or not line.strip():
                            continue
                        # Every line is a topic — LLM will always expand it
                        cs.append({"title": line.strip()})
                result_dict["custom_slides"] = cs
                print(f"[generate.py] Parsed {len(cs)} custom slide topic(s)")

        except Exception as e:
            print(f"[generate.py] Warning: failed to parse slide selection/custom slides: {e}")

        # ── LLM enrichment: expand every custom slide topic into bullets ──
        try:
            cs_list = result_dict.get("custom_slides") or []
            expanded = []

            print(f"[generate.py] Enriching {len(cs_list)} custom slide(s) via LLM...")

            for idx, cs in enumerate(cs_list):
                title = (cs.get("title") or "").strip() if isinstance(cs, dict) else str(cs).strip()
                if not title:
                    print(f"[generate.py] Skipping custom slide {idx + 1} — empty title")
                    continue

                user_msg = build_user_message(brd_text, tech_doc_text)
                user_msg += (
                    "\n\n=== CUSTOM SLIDE TOPIC ===\n"
                    f"{title}\n\n"
                    "INSTRUCTIONS:\n"
                    "- Generate EXACTLY 3 to 6 bullet points for this slide topic.\n"
                    "- Each bullet must be 10-20 words, specific to the BRD and technical documentation above.\n"
                    "- Do NOT write generic bullets. Reference actual details from the BRD/tech doc.\n"
                    "- Return ONLY valid JSON in this exact format:\n"
                    '  {"title": "<slide title>", "bullets": ["bullet 1", "bullet 2", ...]}\n'
                    "- The bullets array MUST have at least 3 items."
                )

                try:
                    print(f"[generate.py] Enriching slide {idx + 1}/{len(cs_list)}: '{title}'")
                    generated_obj = await orchestrator.client.invoke(CUSTOM_SLIDE_PROMPT, user_msg)

                    if isinstance(generated_obj, dict):
                        gtitle  = generated_obj.get("title") or title
                        bullets = generated_obj.get("bullets") or []
                        if not isinstance(bullets, list):
                            print(f"[generate.py] Warning: bullets is not a list for '{title}', got: {type(bullets)}")
                            bullets = [str(bullets)]
                        if len(bullets) < 3:
                            print(f"[generate.py] Warning: LLM returned only {len(bullets)} bullet(s) for '{title}' — expected 3+. Response: {generated_obj}")
                        expanded.append({"title": gtitle, "bullets": bullets})
                    else:
                        print(f"[generate.py] Warning: LLM returned non-dict for '{title}': {type(generated_obj)} — {str(generated_obj)[:200]}")
                        expanded.append({"title": title, "bullets": [f"Content generation pending for: {title}"]})

                except Exception as e:
                    print(f"[generate.py] ERROR: LLM enrichment failed for '{title}': {e}")
                    expanded.append({"title": title, "bullets": [f"Content generation pending for: {title}"]})

            if expanded:
                result_dict["custom_slides"] = expanded
                print(f"[generate.py] ✓ Enriched {len(expanded)} custom slide(s)")

        except Exception as e:
            print(f"[generate.py] Warning: custom slide processing failed: {e}")

        # ── Diagnostic log ────────────────────────────────────────────────
        try:
            cs_preview = result_dict.get("custom_slides")
            sel_preview = result_dict.get("selected_slides")
            print(f"[generate.py] selected_slides -> {sel_preview}")
            print(f"[generate.py] custom_slides -> {json.dumps(cs_preview) if cs_preview is not None else cs_preview}")
        except Exception:
            pass

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