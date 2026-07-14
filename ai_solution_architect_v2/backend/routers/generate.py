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
import traceback
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import Response


from models.response_models import GenerateRequest
from models.request_models import ReviewRequest
from services.orchestrator import OrchestratorService
from agents.prompt_builder import CUSTOM_SLIDE_VISUAL_PROMPT, build_user_message
from services.pptx_service import PptxService
from services.file_extractor import extract_text
from services.metrics_tracker import MetricsTracker, classify_error
from services.metrics_helpers import (
    extract_diagram_metrics,
    calculate_quality_scores,
    extract_slide_metrics,
    extract_token_usage,
    extract_architecture_justification,
    detect_diagram_selected,
    extract_sections,
)


router = APIRouter()


def get_metrics_file_path(run_id: str) -> Path:
    """Get the path to the metrics file, falling back to local backend/metrics if D: is not writable."""
    try:
        metrics_dir = Path(r"D:\documentation_agent_metrics_json\ppt-agent")
        metrics_dir.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = metrics_dir / f".test_{run_id}"
        test_file.touch()
        test_file.unlink()
        return metrics_dir / f"{run_id}.json"
    except Exception:
        # Fallback to local directory inside backend
        local_dir = Path(__file__).parent.parent / "metrics"
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir / f"{run_id}.json"



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
    # ← NEW: Initialize metrics tracker (non-intrusive)
    tracker = MetricsTracker()
    
    try:
        if not brd_text.strip() and not tech_doc_text.strip():
            raise HTTPException(
                status_code=400,
                detail="At least one of BRD text or Technical Documentation is required"
            )


        print("[generate.py] ════════════════════════════════════════════════════════════")
        print(f"[generate.py] Starting PPT generation (BRD: {len(brd_text)} chars, TechDoc: {len(tech_doc_text)} chars)")


        payload = GenerateRequest(brd_text=brd_text, tech_doc_text=tech_doc_text)
        
        # Track core generation phase via orchestrator
        result = await orchestrator.run(payload, tracker=tracker)
        
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
                    "- Select the visual layout that best explains this topic, then use its exact schema.\n"
                    "- Return 3 to 5 concise, evidence-based items; do not return a bullets array.\n"
                    "- Do NOT write generic content. Reference actual details from the BRD/tech doc.\n"
                    "- Return ONLY the JSON object required by the system prompt."
                )


                try:
                    print(f"[generate.py] Enriching slide {idx + 1}/{len(cs_list)}: '{title}'")
                    generated_obj = await orchestrator.client.invoke(CUSTOM_SLIDE_VISUAL_PROMPT, user_msg)
                    
                    # Accumulate token usage for custom slide enrichment under core_generation
                    try:
                        custom_usage = orchestrator.client.get_last_usage()
                        if custom_usage:
                            tracker.add_token_usage("core_generation", custom_usage)
                    except Exception as tok_err:
                        print(f"[Metrics] Warning: failed to accumulate tokens: {tok_err}")

                    if isinstance(generated_obj, dict):
                        if "content" in generated_obj or "layout" in generated_obj:
                            gtitle = str(generated_obj.get("title") or title).strip()
                            layout = str(generated_obj.get("layout") or "key_messages").strip().lower().replace(" ", "_")
                            allowed_layouts = {"timeline", "comparison", "people", "metrics", "flow", "financials", "benefits", "key_messages"}
                            if layout not in allowed_layouts:
                                print(f"[generate.py] Warning: unsupported custom-slide layout '{layout}' for '{title}'; using key_messages")
                                layout = "key_messages"

                            content = generated_obj.get("content")
                            if not isinstance(content, list):
                                content = generated_obj.get("bullets") or []
                            content = content[:5]
                            structured_layouts = {"comparison", "people", "metrics", "financials"}
                            if layout in structured_layouts and any(not isinstance(item, dict) for item in content):
                                print(f"[generate.py] Warning: malformed {layout} content for '{title}'; using key_messages")
                                layout = "key_messages"
                            if len(content) < 3:
                                print(f"[generate.py] Warning: LLM returned only {len(content)} content item(s) for '{title}'")

                            expanded.append({
                                "title": gtitle,
                                "type": "llm-layout",
                                "layout": layout,
                                "subtitle": generated_obj.get("subtitle") or "",
                                "content": content,
                                "left_label": generated_obj.get("left_label") or "Current State",
                                "right_label": generated_obj.get("right_label") or "Target State",
                                "bullets": [str(item.get("description") or item.get("title") or item) if isinstance(item, dict) else str(item) for item in content],
                            })
                            continue

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


        # ← NEW: Extract and store token usage from LLM calls (after result_dict is created)
        try:
            token_usage = result.get_token_usage()
            print(f"[Metrics] DEBUG - extracted token_usage: {token_usage}")
            
            # Parse selected slides to check for explicit diagram selection
            selected_slides_list = []
            try:
                if selected_slides:
                    selected_slides_list = json.loads(selected_slides)
                    if not isinstance(selected_slides_list, list):
                        selected_slides_list = [s.strip() for s in str(selected_slides).split(",") if s.strip()]
            except:
                pass
            
            # Check if diagram was explicitly selected by the user
            diagram_explicitly_selected = any(
                "diagram" in str(s).lower() or "architecture" in str(s).lower() 
                for s in selected_slides_list
            )
            
            if token_usage:
                # Set token usage for each phase
                for phase, usage in token_usage.items():
                    total = usage.get('total_tokens', 0)
                    print(f"[Metrics] DEBUG - phase '{phase}': {total} total_tokens")
                    
                    # ✅ FIX #1: Skip diagram_generation tokens entirely if user did NOT select diagram
                    if phase == "diagram_generation" or phase == "diagram":
                        if not diagram_explicitly_selected:
                            print(f"[Metrics] Skipping {phase} tokens - diagram not selected by user")
                            continue
                        if total == 0:
                            print(f"[Metrics] Skipping {phase} - has 0 tokens")
                            continue
                    
                    if total > 0:
                        tracker.set_token_usage(phase, usage)
                        print(f"[Metrics] ✓ Set token usage for {phase}: {usage}")
                print(f"[Metrics] ✓ Token usage captured from LLM calls")
            else:
                print(f"[Metrics] WARNING - token_usage is empty or None")
        except Exception as e:
            print(f"[Metrics] Warning: failed to extract token usage: {e}")
            import traceback
            traceback.print_exc()


        # Record total retry count from Databricks client
        try:
            tracker.set_total_retry_count(orchestrator.client.retry_count)
        except Exception as retry_err:
            print(f"[Metrics] Warning: failed to record retry count: {retry_err}")

        # Track PPTX generation phase
        with tracker.phase("pptx_generation"):
            pptx_bytes = pptx_service.generate(result_dict, tracker=tracker)
        
        print(f"[generate.py] ✓ PPTX generated: {len(pptx_bytes)} bytes")
        print("[generate.py] ════════════════════════════════════════════════════════════")
        
        # ← NEW: Extract and populate all metrics (safe - failures won't break response)
        try:
            # Parse selected slides for metrics (reparse to be consistent)
            selected_slides_list = []
            try:
                if selected_slides:
                    selected_slides_list = json.loads(selected_slides)
                    if not isinstance(selected_slides_list, list):
                        selected_slides_list = [s.strip() for s in str(selected_slides).split(",") if s.strip()]
            except:
                pass
            
            # ✅ FIX #2: Only use explicit user selection — remove diagram_has_components fallback
            diagram_selected = any(
                "diagram" in str(s).lower() or "architecture" in str(s).lower() 
                for s in selected_slides_list
            )
            
            # Extract diagram metrics only if diagram was selected
            diagram_metrics = extract_diagram_metrics(result, diagram_selected=diagram_selected)
            diagram_success = diagram_metrics["success"]
            
            tracker.update_diagram_metrics(
                attempted=diagram_metrics["attempted"],
                success=diagram_metrics["success"],
                components_count=diagram_metrics["components_count"],
                connections_count=diagram_metrics["connections_count"],
                expected_components=diagram_metrics["expected_components"],
                expected_connections=diagram_metrics["expected_connections"],
            )
            
            # Extract and update sections metrics
            sections_data = extract_sections(result_dict, selected_slides_list)
            tracker.update_sections_metrics(
                selected_count=sections_data["selected_count"],
                selected_list=sections_data["selected_list"],
                custom_sections_count=sections_data["custom_sections_count"],
                custom_sections=sections_data["custom_sections"],
            )
            
            # Calculate quality scores
            quality_scores = calculate_quality_scores(result, brd_text, tech_doc_text, diagram_selected=diagram_selected)
            tracker.update_quality_scores(
                content_quality=quality_scores["content_quality"],
                diagram_quality=quality_scores["diagram_quality"],
                architecture_alignment=quality_scores["architecture_alignment"],
                output_validity=quality_scores["output_validity"],
            )
            
            # Extract slide metrics based on user selections and diagram success state
            slide_metrics = extract_slide_metrics(
                result_dict, 
                selected_slides=selected_slides_list, 
                diagram_success=diagram_success
            )
            tracker.update_slide_metrics(
                attempted=slide_metrics["attempted"],
                successful=slide_metrics["successful"],
                failed=slide_metrics["failed"],
                retry_count=orchestrator.client.retry_count,
            )
            
            # Extract architecture justification metrics
            decisions_identified, decisions_justified, brd_citations, constraint_references = extract_architecture_justification(result)
            tracker.update_architecture_justification(
                decisions_identified=decisions_identified,
                decisions_justified=decisions_justified,
                brd_citations=brd_citations,
                constraint_references=constraint_references,
            )
            
            # Validate PPTX and update validation metrics
            # Use relative path for Windows compatibility
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            temp_pptx_path = os.path.join(temp_dir, "architecture_temp.pptx")
            with open(temp_pptx_path, 'wb') as f:
                f.write(pptx_bytes)
                
            # Wrap validation in its own phase context manager
            with tracker.phase("validation"):
                tracker.validate_pptx(temp_pptx_path)
            
            # Update output validity based on PPTX validation
            if tracker.metrics.pptx_validation.health_score >= 1.0:
                quality_scores["output_validity"] = 1.0
                tracker.update_quality_scores(
                    content_quality=quality_scores["content_quality"],
                    diagram_quality=quality_scores["diagram_quality"],
                    architecture_alignment=quality_scores["architecture_alignment"],
                    output_validity=1.0,
                )
            
            print(f"[Metrics] ✓ Metrics extracted: {diagram_metrics['components_count']} components, {slide_metrics['attempted']} slides")
            
        except Exception as e:
            print(f"[Metrics] Warning: failed to extract metrics: {e}")
        
        # ← NEW: Finalize metrics (safe - metrics failures won't break response)
        try:
            tracker.finalize(success=True)
            metrics_dict = tracker.get_metrics_dict()
            
            metrics_file = get_metrics_file_path(tracker.run_id)
            with open(metrics_file, 'w') as f:
                json.dump(metrics_dict, f, indent=2)
            print(f"[Metrics] Saved to {metrics_file}")
        except Exception as e:
            print(f"[Metrics] Warning: failed to save metrics: {e}")
        
        return _pptx_response(pptx_bytes)


    except Exception as e:
        # Record error in metrics (safely)
        try:
            if not tracker.metrics.error_details.occurred:
                active_phase = getattr(tracker, "active_phase", None) or "generate_pptx"
                stage, category = classify_error(e, context=active_phase)
                tracker.set_error(stage, category, str(e), traceback.format_exc())
            
            # Try to extract partial metrics even on error
            try:
                if 'result' in locals():
                    diagram_metrics = extract_diagram_metrics(result)
                    tracker.update_diagram_metrics(
                        attempted=diagram_metrics["attempted"],
                        success=False,
                        components_count=diagram_metrics["components_count"],
                        connections_count=diagram_metrics["connections_count"],
                    )
            except:
                pass
            
            tracker.finalize(success=False)
            metrics_dict = tracker.get_metrics_dict()
            
            metrics_file = get_metrics_file_path(tracker.run_id)
            with open(metrics_file, 'w') as f:
                json.dump(metrics_dict, f, indent=2)
            print(f"[Metrics] Error metrics saved to {metrics_file}")
        except Exception as metrics_error:
            print(f"[Metrics] Warning: failed to save error metrics: {metrics_error}")
        
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


@router.post(
    "/review",
    summary="Submit review feedback / acceptance status for a generated presentation",
)
def submit_review(body: ReviewRequest):
    """
    Load a run's saved metrics, update the acceptance status, increment the review cycle count,
    and save the metrics payload back to disk.
    """
    metrics_file = get_metrics_file_path(body.run_id)
    
    if not metrics_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No metrics payload found for run_id {body.run_id}"
        )
        
    try:
        with open(metrics_file, 'r') as f:
            metrics_dict = json.load(f)
            
        # Update fields
        metrics_dict["acceptance_status"] = body.acceptance_status.value
        metrics_dict["review_cycle_count"] = metrics_dict.get("review_cycle_count", 0) + 1
        
        # Write back
        with open(metrics_file, 'w') as f:
            json.dump(metrics_dict, f, indent=2)
            
        return {
            "status": "success",
            "run_id": body.run_id,
            "acceptance_status": metrics_dict["acceptance_status"],
            "review_cycle_count": metrics_dict["review_cycle_count"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update review metrics: {str(e)}"
        )
