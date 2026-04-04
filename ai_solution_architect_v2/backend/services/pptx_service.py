"""
pptx_service.py

Python wrapper that calls generate_pptx.js via subprocess.
Accepts the full architecture JSON dict and returns the .pptx as bytes.

The JS generator (generate_pptx.js) uses:
  - drawioGenerator.js  — converts architecture.components + .connections → draw.io XML
  - drawioRenderer.js   — renders draw.io XML → PNG via local Puppeteer (no external API)

No Mermaid dependency remains.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

# Resolve the JS script path relative to this file
_SCRIPT_DIR = Path(__file__).parent / "pptx_gen"
_JS_SCRIPT   = _SCRIPT_DIR / "generate_pptx.js"
_NODE_BIN    = "node"


class PptxService:
    def generate(self, architecture_json: dict) -> bytes:
        """
        Takes the full architecture response dict, runs the Node.js generator,
        and returns the resulting .pptx file as bytes.

        The architecture_json MUST contain architecture.components (with id/label)
        and architecture.connections for the draw.io diagram to render correctly.

        Raises RuntimeError if Node.js process fails.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path  = os.path.join(tmpdir, "input.json")
            output_path = os.path.join(tmpdir, "output.pptx")

            with open(input_path, "w", encoding="utf-8") as f:
                json.dump(architecture_json, f, ensure_ascii=False)

            result = subprocess.run(
                [_NODE_BIN, str(_JS_SCRIPT), input_path, output_path],
                capture_output=True,
                timeout=180,   # increased for Puppeteer startup time
                cwd=str(_SCRIPT_DIR),
            )

            # Decode output with UTF-8 and error handling (not CP1252)
            stdout_text = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
            stderr_text = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""

            if result.returncode != 0:
                raise RuntimeError(
                    f"PPTX generation failed (exit {result.returncode}):\n"
                    f"STDOUT: {stdout_text}\nSTDERR: {stderr_text}"
                )

            if not os.path.exists(output_path):
                raise RuntimeError(
                    f"Node process exited 0 but output file not found.\n"
                    f"STDERR: {result.stderr}"
                )

            with open(output_path, "rb") as f:
                return f.read()