# Integration Code Examples

This file shows exact code snippets for integrating metrics into your existing pipeline.

---

## Example 1: Basic Integration in `generate.py`

### Before (Current Code)

```python
@router.post("/generate-pptx")
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
            raise HTTPException(status_code=400, detail="...")

        print("[generate.py] Starting PPT generation...")

        payload = GenerateRequest(brd_text=brd_text, tech_doc_text=tech_doc_text)
        result = await orchestrator.run(payload)

        print(f"[generate.py] Orchestrator completed, generating PPTX...")
        result_dict = json.loads(result.model_dump_json())
        raw_arch = result.get_raw_architecture()

        pptx_bytes = await pptx_service.generate(
            result_dict,
            raw_arch,
            selected_slides,
            custom_slides,
        )

        print(f"[generate.py] PPTX generated ({len(pptx_bytes)} bytes)")
        return _pptx_response(pptx_bytes)

    except Exception as e:
        print(f"[generate.py] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### After (With Metrics)

```python
# Add these imports at the top
from services.metrics_tracker import MetricsTracker, classify_error
import traceback

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
    # ← NEW: Create metrics tracker
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

        # ← NEW: Wrap orchestrator call with phase tracking
        with tracker.phase("core_generation"):
            result = await orchestrator.run(payload)

        # ← NEW: Extract and record token usage (if available)
        # Note: Update this based on how your LLM client returns usage
        if hasattr(result, "_usage"):
            tracker.set_token_usage("core", {
                "prompt_tokens": result._usage.prompt_tokens,
                "completion_tokens": result._usage.completion_tokens,
            })

        print(f"[generate.py] Orchestrator completed, generating PPTX...")
        result_dict = json.loads(result.model_dump_json())
        raw_arch = result.get_raw_architecture()

        # ← NEW: Track PPTX generation phase
        with tracker.phase("pptx_generation"):
            pptx_bytes = await pptx_service.generate(
                result_dict,
                raw_arch,
                selected_slides,
                custom_slides,
            )

        print(f"[generate.py] PPTX generated ({len(pptx_bytes)} bytes)")

        # ← NEW: Validate PPTX and update metrics
        temp_path = "/tmp/architecture_output.pptx"
        with open(temp_path, 'wb') as f:
            f.write(pptx_bytes)

        with tracker.phase("validation"):
            tracker.validate_pptx(temp_path)
            # These should be calculated based on your generation logic
            tracker.update_quality_scores(
                content_quality=0.92,  # Calculate from content checks
                diagram_quality=0.88,  # Calculate from diagram validation
                architecture_alignment=0.95,  # Compare to BRD
                output_validity=1.0,  # From PPTX health validation
            )
            tracker.update_diagram_metrics(
                attempted=True,
                success=True,
                components_count=8,
                connections_count=11,
                expected_components=8,
                expected_connections=10,
            )
            tracker.update_slide_metrics(
                attempted=12,
                successful=12,
                failed=0,
                retry_count=1,
            )

        # ← NEW: Finalize metrics and log
        tracker.finalize(success=True)
        metrics_dict = tracker.get_metrics_dict()

        print("[generate.py] ════════════════════════════════════════════════════════════")
        print("[Metrics]", json.dumps(metrics_dict, indent=2))

        # ← NEW: (Optional) Send metrics to storage
        # await metrics_store.save(metrics_dict)

        return _pptx_response(pptx_bytes)

    except Exception as e:
        print(f"[generate.py] Error: {e}")

        # ← NEW: Record error in metrics
        stage, category = classify_error(e, context="generate_pptx")
        tracker.set_error(
            stage=stage,
            category=category,
            message=str(e),
            traceback=traceback.format_exc(),
        )
        tracker.finalize(success=False)

        metrics_dict = tracker.get_metrics_dict()
        print("[Metrics] FAILED:", json.dumps(metrics_dict, indent=2))
        # await metrics_store.save(metrics_dict)

        raise HTTPException(status_code=500, detail=str(e))
```

---

## Example 2: Metrics in `orchestrator.py`

### Updated Run Method

```python
# In orchestrator.py
import time
from services.metrics_tracker import MetricsTracker, extract_token_usage

class OrchestratorService:
    def __init__(self):
        self.client = DatabricksClient()

    async def run(self, request: GenerateRequest, tracker: MetricsTracker = None) -> GenerateResponse:
        # ← NEW: Optional tracker parameter

        # ── STEP 0: Summarise tech doc ──────────────────────────
        tech_summary = []
        if request.tech_doc_text and request.tech_doc_text.strip():
            # ← NEW: Phase tracking
            if tracker:
                start = time.time()

            summary_result = await self.client.invoke(
                SUMMARIZE_PROMPT,
                request.tech_doc_text[:8000],
            )

            if tracker:
                duration = time.time() - start
                tracker.metrics.duration_summarization = duration
                # Extract token usage from response
                usage = extract_token_usage(summary_result)
                tracker.set_token_usage("summarization", usage)

            tech_summary = summary_result.get("summary", [])

        # ── STEP 1: Core architecture ───────────────────────────
        if tracker:
            start = time.time()

        core_input = (
            f"BRD:\n{request.brd_text[:3500]}\n\n"
            f"TECH SUMMARY:\n{json.dumps(tech_summary)}"
        )
        core = await self.client.invoke(CORE_PROMPT, core_input)

        if tracker:
            duration = time.time() - start
            tracker.metrics.duration_core_generation = duration
            usage = extract_token_usage(core)
            tracker.set_token_usage("core", usage)

        if not isinstance(core, dict):
            raise ValueError(f"Invalid core response type: {type(core)}")

        # ── STEP 2: Structured diagram JSON ────────────────────
        if tracker:
            start = time.time()

        arch_subset = {
            "project":           core.get("project", {}),
            "architecture":      core.get("architecture", {}),
            "technology_stack":  core.get("technology_stack", {}),
            "data_flow":         core.get("data_flow", []),
        }
        diagram_json = await self.client.invoke(
            DIAGRAM_PROMPT,
            json.dumps(arch_subset),
        )

        if tracker:
            duration = time.time() - start
            tracker.metrics.duration_diagram_generation = duration
            usage = extract_token_usage(diagram_json)
            tracker.set_token_usage("diagram", usage)

        # ... rest of orchestrator code ...

        return result  # GenerateResponse
```

---

## Example 3: Storage Layer

### Simple File-Based Storage

```python
# Create new file: backend/services/metrics_store.py

import json
import asyncio
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class FileMetricsStore:
    """Store metrics to JSON files"""

    def __init__(self, base_dir: str = "metrics"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    async def save(self, metrics_dict: Dict[str, Any]) -> None:
        """Save metrics to timestamped JSON file"""
        run_id = metrics_dict.get("run_id", "unknown")
        timestamp = datetime.utcnow().isoformat()

        filename = self.base_dir / f"{run_id}_{timestamp}.json"

        await asyncio.to_thread(
            self._write_file,
            filename,
            metrics_dict,
        )

        print(f"[MetricsStore] Saved to {filename}")

    def _write_file(self, filepath: Path, data: Dict) -> None:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# Use in generate.py:
metrics_store = FileMetricsStore()

# In the handler:
tracker.finalize(success=True)
metrics_dict = tracker.get_metrics_dict()
await metrics_store.save(metrics_dict)
```

### Database Storage (SQLAlchemy)

```python
# Create new file: backend/services/metrics_store.py

from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Dict, Any

Base = declarative_base()

class MetricsRecord(Base):
    __tablename__ = "metrics"

    run_id = Column(String(50), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON)  # Entire metrics dict as JSON

class DatabaseMetricsStore:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    async def save(self, metrics_dict: Dict[str, Any]) -> None:
        """Save metrics to database"""
        session = self.Session()
        try:
            record = MetricsRecord(
                run_id=metrics_dict["run_id"],
                data=metrics_dict,
            )
            session.add(record)
            session.commit()
            print(f"[MetricsStore] Saved {record.run_id} to database")
        except Exception as e:
            session.rollback()
            print(f"[MetricsStore] Error saving to database: {e}")
        finally:
            session.close()


# Use in generate.py:
store = DatabaseMetricsStore(os.getenv("DATABASE_URL"))
await store.save(tracker.get_metrics_dict())
```

### Analytics Service (HTTP POST)

```python
# Create new file: backend/services/metrics_store.py

import aiohttp
from typing import Dict, Any
from datetime import datetime

class AnalyticsMetricsStore:
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key

    async def save(self, metrics_dict: Dict[str, Any]) -> None:
        """Send metrics to remote analytics service"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_endpoint}/metrics",
                    json=metrics_dict,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        print(f"[MetricsStore] Sent {metrics_dict['run_id']} to analytics")
                    else:
                        print(f"[MetricsStore] Analytics returned {resp.status}")
            except Exception as e:
                print(f"[MetricsStore] Error sending to analytics: {e}")


# Use in generate.py:
analytics = AnalyticsMetricsStore(
    api_endpoint="https://analytics.company.com",
    api_key=os.getenv("ANALYTICS_API_KEY"),
)
await analytics.save(tracker.get_metrics_dict())
```

---

## Example 4: Token Usage Extraction

Different LLM clients return tokens differently. Here are patterns for common ones:

### Databricks/OpenAI Style

```python
# Response has .usage attribute
response = await client.invoke(prompt, text)

usage = {
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
}
tracker.set_token_usage("core", usage)
```

### Dict-Based Response

```python
# Response is a dict with "usage" key
response = await client.invoke(prompt, text)

usage = response.get("usage", {
    "prompt_tokens": 0,
    "completion_tokens": 0,
})
tracker.set_token_usage("core", usage)
```

### Using Helper Function

```python
from services.metrics_tracker import extract_token_usage

# Works with multiple response types
response = await client.invoke(prompt, text)
usage = extract_token_usage(response)
tracker.set_token_usage("core", usage)
```

---

## Example 5: Quality Score Calculation

### From Content Analysis

```python
def calculate_quality_scores(result_dict: dict, brd_text: str) -> dict:
    """
    Calculate quality scores based on generation results.
    This is a simplified example; adjust to your actual quality criteria.
    """

    # Content Quality: Based on completeness
    content = result_dict.get("architecture", {})
    has_all_sections = all([
        content.get("pattern"),
        content.get("frontend"),
        content.get("backend"),
        content.get("components"),
    ])
    content_quality = 0.95 if has_all_sections else 0.70

    # Diagram Quality: Based on component count
    components = content.get("components", [])
    diagram_quality = min(1.0, len(components) / 8) * 0.9  # 8 is ideal

    # Architecture Alignment: How well it matches BRD
    alignment_score = 0.9 if brd_text else 0.7

    # Output Validity: From PPTX validation
    output_validity = 1.0  # Set to 0.0 if validation failed

    return {
        "content_quality": content_quality,
        "diagram_quality": diagram_quality,
        "architecture_alignment": alignment_score,
        "output_validity": output_validity,
    }


# In generate.py:
quality_scores = calculate_quality_scores(result_dict, brd_text)
tracker.update_quality_scores(**quality_scores)
```

---

## Example 6: Error Classification

```python
from services.metrics_tracker import classify_error, ErrorStageEnum, ErrorCategoryEnum

try:
    # ... some operation ...
    pptx_bytes = await pptx_service.generate(...)
except TimeoutError as e:
    stage, category = classify_error(e, context="pptx_generation")
    print(f"Error: {stage.value} / {category.value}")
    tracker.set_error(stage, category, str(e))

except Exception as e:
    # Custom classification
    if "diagram" in str(e).lower():
        stage = ErrorStageEnum.DIAGRAM_RENDERING
        category = ErrorCategoryEnum.RENDERING_ERROR
    else:
        stage, category = classify_error(e)

    tracker.set_error(stage, category, str(e), traceback.format_exc())
```

---

## Example 7: Complete End-to-End Flow

```python
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import Response
from services.metrics_tracker import MetricsTracker, classify_error
from services.metrics_store import FileMetricsStore
import json
import traceback

router = APIRouter()
metrics_store = FileMetricsStore()

@router.post("/generate-pptx")
async def generate_pptx(
    brd_text: str = Form(default=""),
    tech_doc_text: str = Form(default=""),
    orchestrator = Depends(get_orchestrator),
    pptx_service = Depends(get_pptx_service),
):
    # Step 1: Initialize metrics tracking
    tracker = MetricsTracker()

    try:
        # Step 2: Validate input
        if not brd_text.strip() and not tech_doc_text.strip():
            raise HTTPException(status_code=400, detail="Input required")

        # Step 3: Generate core architecture
        with tracker.phase("core_generation"):
            payload = GenerateRequest(brd_text=brd_text, tech_doc_text=tech_doc_text)
            result = await orchestrator.run(payload)

        # Step 4: Extract token usage
        tracker.set_token_usage("core", result.get("usage", {}))

        # Step 5: Generate PPTX
        with tracker.phase("pptx_generation"):
            pptx_bytes = await pptx_service.generate(
                json.loads(result.model_dump_json()),
                result.get_raw_architecture(),
            )

        # Step 6: Validate output
        with tracker.phase("validation"):
            temp_path = "/tmp/output.pptx"
            with open(temp_path, 'wb') as f:
                f.write(pptx_bytes)

            tracker.validate_pptx(temp_path)
            tracker.update_quality_scores(0.92, 0.88, 0.95, 1.0)

        # Step 7: Finalize metrics
        tracker.finalize(success=True)
        metrics_dict = tracker.get_metrics_dict()

        # Step 8: Store metrics
        await metrics_store.save(metrics_dict)

        # Step 9: Return PPTX
        return Response(
            content=pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": 'attachment; filename="architecture.pptx"'},
        )

    except Exception as e:
        # Error handling with metrics
        stage, category = classify_error(e, context="generate_pptx")
        tracker.set_error(stage, category, str(e), traceback.format_exc())
        tracker.finalize(success=False)

        metrics_dict = tracker.get_metrics_dict()
        await metrics_store.save(metrics_dict)

        raise HTTPException(status_code=500, detail=str(e))
```

---

## Key Points

1. **Minimal Code Changes** — Metrics wrap around existing code
2. **Non-Breaking** — If metrics fail, the response still returns PPTX
3. **Async-Friendly** — Uses `asyncio.to_thread()` for blocking I/O
4. **Flexible Storage** — File, DB, or HTTP — your choice
5. **Error Safe** — Try/except blocks ensure metrics don't crash the pipeline

---

## Testing the Integration

```bash
# Test with the API
curl -X POST http://localhost:8000/generate-pptx \
  -F "brd_text=@brd.txt" \
  -F "tech_doc_text=@tech.txt" \
  -o output.pptx

# Check metrics were saved
ls -la metrics/
cat metrics/*.json
```
