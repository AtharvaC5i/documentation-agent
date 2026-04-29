"""
Document Generation Pipeline — v4 (docx.js backend).

Uses Node.js + docx.js for document generation instead of python-docx.
This eliminates ALL python-docx rendering bugs:
  - No table container signature issues
  - No font inheritance problems
  - No heading style override issues
  - Inline ## headings from LLM output are split and rendered correctly
  - Proper tab-stop header/footer (no table-in-header bug)
  - Explicit WidthType.DXA on every table and cell

Python side: serialises project data to JSON, calls Node.js subprocess,
moves output file to the correct location.
"""

import os
import re
import json
import uuid
import subprocess
from datetime import datetime
from typing import List, Dict, Any

from models.project import Project, ProjectStore
from utils.logger import info, success, warn, error, divider


# Path to the JS builder script
_JS_BUILDER = os.path.join(os.path.dirname(__file__), "../doc_builder/build_brd.js")
_TMP_DIR    = os.path.join(os.path.dirname(__file__), "../../outputs")


def _get_output_path(project_name: str, version: int) -> str:
    os.makedirs(_TMP_DIR, exist_ok=True)
    safe = re.sub(r"[^\w\-]", "_", project_name)
    return os.path.join(_TMP_DIR, f"BRD_{safe}_v{version}.docx")


def _build_metadata(project: Project) -> Dict[str, Any]:
    return {
        "project_name": project.project_name,
        "client_name":  project.client_name,
        "industry":     project.industry,
        "description":  project.description,
        "team":         ", ".join(project.team_members) if project.team_members else "Project Team",
        "version":      project.version,
        "date":         datetime.now().strftime("%B %d, %Y"),
    }


def _build_sections_payload(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Serialise generated sections for the JS builder."""
    result = []
    for sec in sections:
        result.append({
            "name":        sec.get("name", "Section"),
            "content":     sec.get("content", ""),
            "quality_pct": sec.get("quality_pct", ""),
            "req_count":   sec.get("req_count", 0),
            "status":      sec.get("status", ""),
        })
    return result


class DocumentPipeline:

    def __init__(self, project: Project, store: ProjectStore):
        self.project = project
        self.store   = store

    async def run(self):
        self.project.status           = "generating_document"
        self.project.progress_message = "Generating Word document..."
        self.store.save(self.project)
        divider(f"DOCUMENT PIPELINE — {self.project.project_name}")

        # Decide which sections to include
        approved = [s for s in self.project.generated_sections if s.get("approved")]
        if not approved:
            approved = self.project.generated_sections

        if not approved:
            self.project.status           = "error"
            self.project.progress_message = "No sections to include in document."
            self.store.save(self.project)
            return

        info("DOC", f"Assembling {len(approved)} sections via docx.js")

        # Build JSON payload
        payload = {
            "metadata": _build_metadata(self.project),
            "sections": _build_sections_payload(approved),
        }

        # Write to temp JSON file
        tmp_id   = uuid.uuid4().hex[:8]
        tmp_json = os.path.join(_TMP_DIR, f"brd_payload_{tmp_id}.json")
        os.makedirs(_TMP_DIR, exist_ok=True)

        with open(tmp_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        output_path = _get_output_path(self.project.project_name, self.project.version)

        try:
            # Call Node.js builder
            info("DOC", f"Calling Node.js builder: {_JS_BUILDER}")
            result = subprocess.run(
                ["node", _JS_BUILDER, tmp_json, output_path],
                capture_output=True,
                text=True,
                timeout=120,
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode != 0:
                raise RuntimeError(f"Node.js exited {result.returncode}\nSTDOUT: {stdout}\nSTDERR: {stderr}")

            if not stdout.startswith("OK:"):
                raise RuntimeError(f"Unexpected output: {stdout}\nSTDERR: {stderr}")

            if not os.path.exists(output_path):
                raise RuntimeError(f"Output file not created: {output_path}")

            file_size_kb = os.path.getsize(output_path) // 1024
            success("DOC", f"Document created — {file_size_kb}KB → {output_path}")

            self.project.document_path    = output_path
            self.project.status           = "complete"
            self.project.progress_message = "Document ready for download."

        except subprocess.TimeoutExpired:
            error("DOC", "Node.js builder timed out after 120 seconds")
            self.project.status           = "error"
            self.project.progress_message = "Document generation timed out."

        except Exception as ex:
            error("DOC", f"Document generation failed: {ex}")
            self.project.status           = "error"
            self.project.progress_message = f"Document generation failed: {str(ex)[:200]}"

        finally:
            # Always clean up temp JSON
            if os.path.exists(tmp_json):
                os.remove(tmp_json)

        self.store.save(self.project)
