# Metrics Implementation Guide

## Overview

This document explains the comprehensive metrics system for the AI Solution Architect PPT generation agent. All metrics are designed to be tracked non-intrusively without disrupting the existing pipeline.

---

## Key Metrics by Category

### 1. **Run Success / Failure** (CRITICAL)

**Why**: Basic health signal; tells if the agent completed successfully

**Calculation**:

```
run_success = boolean (true/false)
```

**Example**:

```json
"run_success": true
```

---

### 2. **Error Stage** (CRITICAL)

**Why**: Identify WHERE failures occur — helps with debugging and recovery

**Possible Values**:

- `summarization` — Tech doc summarization phase
- `core_generation` — Core architecture JSON generation
- `diagram_generation` — Diagram JSON structure generation
- `diagram_building` — Diagram component assembly
- `diagram_rendering` — PNG export from diagram
- `pptx_generation` — PPTX template creation
- `pptx_assembly` — Merging slides into final PPTX
- `validation` — Final output validation
- `unknown` — Stage couldn't be determined

**Example**:

```json
"error_details": {
  "stage": "diagram_rendering",
  "occurred": true
}
```

---

### 3. **Error Category** (CRITICAL)

**Why**: Classify error types for trend analysis and root cause

**Possible Values**:

- `api_error` — LLM API failures, network timeouts
- `diagram_error` — Diagram structure/generation issues
- `rendering_error` — PNG rendering, image processing failures
- `assembly_error` — PPTX merge, ZIP corruption
- `dependency_error` — Missing libraries, Node modules
- `validation_error` — Output fails quality checks
- `timeout_error` — Execution exceeded time limit
- `memory_error` — Out of memory or resource exhaustion
- `unknown_error` — Unclassified

**Example**:

```json
"error_details": {
  "category": "rendering_error",
  "message": "Failed to render diagram PNG: drawio timeout"
}
```

---

### 4. **End-to-End Duration** (CRITICAL)

**Why**: Core latency metric; leadership cares about generation speed

**Calculation**:

```
duration_total = timestamp_end - timestamp_start (in seconds)

Breakdown by phase:
- duration_summarization
- duration_core_generation
- duration_diagram_generation
- duration_diagram_rendering
- duration_pptx_generation
- duration_pptx_assembly
- duration_validation
```

**Example** (6 min 33 sec total):

```json
"duration": {
  "total_seconds": 392.53,
  "summarization_seconds": 8.47,
  "core_generation_seconds": 42.18,
  "diagram_generation_seconds": 18.92,
  "diagram_rendering_seconds": 54.63,
  "pptx_generation_seconds": 12.35,
  "pptx_assembly_seconds": 6.84,
  "validation_seconds": 3.14
}
```

**Interpretation**:

- Diagram rendering took the most time (54.63s) — potential optimization target
- Core generation was second (42.18s) — LLM inference
- Total < 10 min is good; < 5 min is excellent

---

### 5. **LLM Token Usage** (CRITICAL)

**Why**: Essential for cost tracking and usage monitoring

**Calculation**:

```
For each phase (summarization, core_generation, diagram_generation):
  - prompt_tokens = tokens sent to LLM
  - completion_tokens = tokens returned from LLM
  - total_tokens = prompt_tokens + completion_tokens

Total = sum across all phases
```

**Example**:

```json
"llm_tokens": {
  "summarization": {
    "prompt_tokens": 2450,
    "completion_tokens": 890,
    "total_tokens": 3340
  },
  "core_generation": {
    "prompt_tokens": 8750,
    "completion_tokens": 5230,
    "total_tokens": 13980
  },
  "diagram_generation": {
    "prompt_tokens": 4200,
    "completion_tokens": 2105,
    "total_tokens": 6305
  },
  "total": {
    "prompt_tokens": 15400,
    "completion_tokens": 8225,
    "total_tokens": 23625
  }
}
```

**Realistic Ranges**:

- Summarization: 2-4K tokens (depending on doc size)
- Core generation: 8-12K tokens (complex architecture)
- Diagram generation: 4-8K tokens (component details)
- **Total: 15-25K tokens typical for a full run**

---

### 6. **Estimated Cost Per Run** (CRITICAL)

**Why**: Direct business metric; understanding cost per output

**Calculation**:

```
Assuming Databricks pricing:
  prompt_cost_rate = $0.001 per 1K tokens
  completion_cost_rate = $0.002 per 1K tokens

estimated_cost =
  (prompt_tokens / 1000) * $0.001 +
  (completion_tokens / 1000) * $0.002

Example:
  prompt_tokens = 15400
  completion_tokens = 8225

  prompt_cost = (15400 / 1000) * 0.001 = $0.0154
  completion_cost = (8225 / 1000) * 0.002 = $0.01645
  total_cost = $0.03185 ≈ $0.0319
```

**Example**:

```json
"estimated_cost_usd": 0.0213
```

**Realistic Ranges**:

- **Typical run**: $0.018 - $0.035 per generation
- **Complex architecture**: up to $0.05
- **100 runs/month**: ~$2.00 - $3.50 monthly cost

**Pricing Adjustment**: Update the pricing constants in `metrics_models.py` if your actual rates differ from Databricks defaults.

---

### 7. **Slide/Section Success Rate** (HIGH)

**Why**: Did all intended slides generate successfully?

**Calculation**:

```
success_rate = successful_slides / attempted_slides

Example:
  attempted = 12 slides
  successful = 12 slides
  failed = 0 slides

  success_rate = 12 / 12 = 1.0 (100%)
```

**Example**:

```json
"slides": {
  "attempted": 12,
  "successful": 12,
  "failed": 0,
  "retry_count": 1,
  "success_rate": 1.0
}
```

**Interpretation**:

- `1.0` = Perfect (all slides generated)
- `0.9` = 90% success (1 failure)
- `< 0.8` = Concerning pattern

---

### 8. **Retry Count** (HIGH)

**Why**: Exposes instability hidden behind eventual success

**Calculation**:

```
retry_count = total retries for specific generation step or entire run

Example:
  - First attempt at generating core: fails
  - Retry 1: succeeds
  - total_retry_count = 1
```

**Example**:

```json
"total_retry_count": 1
```

**Interpretation**:

- `0` = First attempt succeeded (best)
- `1` = One retry needed (acceptable)
- `2+` = Multiple retries (service may be unstable)

---

### 9. **Basic Quality Score** (HIGH)

**Why**: Quick overall quality signal before advanced evaluation

**Calculation**:

```
overall_score = average of four dimensions:
  1. content_quality (0.0-1.0) — accuracy, completeness, relevance
  2. diagram_quality (0.0-1.0) — visual clarity, correctness
  3. architecture_alignment (0.0-1.0) — follows BRD/constraints
  4. output_validity (0.0-1.0) — PPTX opens without errors

overall_score =
  (content_quality + diagram_quality +
   architecture_alignment + output_validity) / 4

Example:
  content_quality = 0.92
  diagram_quality = 0.88
  architecture_alignment = 0.95
  output_validity = 1.0

  overall_score = (0.92 + 0.88 + 0.95 + 1.0) / 4 = 0.9375
```

**Example**:

```json
"quality": {
  "content_quality": 0.92,
  "diagram_quality": 0.88,
  "architecture_alignment": 0.95,
  "output_validity": 1.0,
  "overall_score": 0.9375
}
```

**Interpretation**:

- `>= 0.9` = Excellent (production-ready)
- `0.8-0.89` = Good (minor issues)
- `0.7-0.79` = Acceptable (needs review)
- `< 0.7` = Poor (major rework needed)

---

### 10. **Diagram Correctness & Completeness** (CRITICAL)

**Why**: Most important Architect-specific metric

**Calculation**:

```
component_coverage = actual_components / expected_components
connection_coverage = actual_connections / expected_connections

diagram_correctness_score =
  (component_coverage * 0.6 + connection_coverage * 0.4) * success_multiplier

Where:
  - component_coverage weighted at 60% (more critical)
  - connection_coverage weighted at 40%
  - success_multiplier = 1.0 if success else 0.0

Example:
  components_count = 8
  expected_components = 8
  connections_count = 11
  expected_connections = 10
  success = true

  component_coverage = 8 / 8 = 1.0
  connection_coverage = min(1.0, 11 / 10) = 1.0

  correctness_score = (1.0 * 0.6 + 1.0 * 0.4) * 1.0 = 1.0 (perfect)
```

**Example**:

```json
"diagram": {
  "attempted": true,
  "success": true,
  "components_count": 8,
  "connections_count": 11,
  "expected_components": 8,
  "expected_connections": 10,
  "component_coverage": 1.0,
  "connection_coverage": 1.0,
  "correctness_score": 1.0
}
```

**Interpretation**:

- `1.0` = Perfect (all components and connections)
- `0.8-0.99` = Very good (minor additions or slight misalignment)
- `0.6-0.79` = Adequate (missing some components or connections)
- `< 0.6` = Poor (significant structural issues)

---

### 11. **Architecture Decision Justification** (CRITICAL)

**Why**: Shows whether architecture choices are grounded in real inputs

**Calculation**:

```
justification_score = decisions_justified / decisions_identified

Example:
  decisions_identified = 6
    (e.g., microservices, event-driven, containerization, DB choice, etc.)
  decisions_justified = 6
    (all have explicit references to BRD/TechDoc)
  brd_citations = 12
    (multiple citations backing each decision)
  constraint_references = 8
    (references to specific constraints)

  justification_score = 6 / 6 = 1.0 (100% justified)
```

**Example**:

```json
"architecture_justification": {
  "decisions_identified": 6,
  "decisions_justified": 6,
  "brd_citations": 12,
  "constraint_references": 8,
  "justification_score": 1.0
}
```

**Interpretation**:

- `1.0` = All decisions justified with citations
- `0.8-0.99` = Most decisions justified
- `0.5-0.79` = Some decisions lack justification
- `< 0.5` = Many unjustified decisions (risky)

---

### 12. **PPTX Generation Health** (CRITICAL)

**Why**: Essential output-validity metric

**Calculation**:

```
health_score = passing_validations / total_validations

Validations checked:
  1. file_created (file exists and has size)
  2. valid_xml (all XML files are well-formed)
  3. valid_relationships (relationship files are valid)
  4. opens_without_repair (PowerPoint won't prompt for repair)
  5. all_slides_present (expected slides are in PPTX)
  6. all_media_present (diagrams/images are embedded)

Example (all passing):
  health_score = 6 / 6 = 1.0 (100%)

Example (one failure):
  health_score = 5 / 6 = 0.833 (83.3%)
```

**Example**:

```json
"pptx_validation": {
  "file_created": true,
  "file_size_bytes": 8547392,
  "valid_xml": true,
  "valid_relationships": true,
  "opens_without_repair": true,
  "all_slides_present": true,
  "all_media_present": true,
  "health_score": 1.0
}
```

**Interpretation**:

- `1.0` = Perfect PPTX (no corruption, all content present)
- `0.8-0.99` = Minor issues (possibly recoverable)
- `< 0.8` = Significant problems (likely needs regeneration)

---

### 13. **Review Cycle Count** (HIGH)

**Why**: Signal for how much refinement was needed

**Calculation**:

```
review_cycle_count = number of feedback → regeneration cycles

Example:
  - First generation
  - User review → marked for minor edits
  - Cycle 1: Regenerate with feedback
  - User approves

  review_cycle_count = 1
```

**Example**:

```json
"review_cycle_count": 0
```

**Interpretation**:

- `0` = Accepted on first generation (excellent)
- `1` = One refinement cycle (good)
- `2+` = Multiple cycles (content instability)

---

### 14. **Acceptance / Rework Flag** (HIGH)

**Why**: Did the generated presentation actually get used?

**Possible Values**:

- `accepted_as_is` — No changes needed
- `minor_edits` — Small cosmetic/content tweaks
- `major_rework` — Significant restructuring or regeneration
- `rejected` — Output not acceptable, starting over
- `pending_review` — Awaiting decision

**Example**:

```json
"acceptance_status": "accepted_as_is"
```

**Interpretation**:

- `accepted_as_is` or `minor_edits` = Successful run
- `major_rework` = Generation quality issues
- `rejected` = Critical failures

---

## Integration Guide

### Step 1: Add to generate.py Router

```python
from services.metrics_tracker import MetricsTracker, extract_token_usage, classify_error

@router.post("/generate-pptx")
async def generate_pptx(...):
    tracker = MetricsTracker()

    try:
        # Phase 1: Summarization
        with tracker.phase("summarization"):
            tech_summary = []
            if request.tech_doc_text.strip():
                summary_result = await client.invoke(SUMMARIZE_PROMPT, ...)
                tracker.set_token_usage("summarization", summary_result.get("usage"))

        # Phase 2: Core generation
        with tracker.phase("core_generation"):
            core = await orchestrator.run(payload)
            tracker.set_token_usage("core", core_response.get("usage"))

        # Phase 3-4: Diagram generation and rendering (inside orchestrator or here)

        # Finalize PPTX
        pptx_bytes = await pptx_service.generate(...)

        # Validate output
        with tracker.phase("validation"):
            temp_pptx_path = "/tmp/output.pptx"
            tracker.validate_pptx(temp_pptx_path)
            tracker.update_quality_scores(
                content_quality=0.92,
                diagram_quality=0.88,
                architecture_alignment=0.95,
                output_validity=1.0,
            )

        # Success!
        tracker.finalize(success=True)

        # Log or store metrics
        metrics_dict = tracker.get_metrics_dict()
        print("[Metrics]", json.dumps(metrics_dict, indent=2))

        return _pptx_response(pptx_bytes)

    except Exception as e:
        stage, category = classify_error(e, context="generate_pptx")
        tracker.set_error(stage, category, str(e), traceback.format_exc())
        tracker.finalize(success=False)
        metrics_dict = tracker.get_metrics_dict()
        print("[Metrics] FAILED:", json.dumps(metrics_dict, indent=2))
        raise
```

### Step 2: Add to Orchestrator

```python
# In orchestrator.py
from services.metrics_tracker import MetricsTracker, extract_token_usage

async def run(self, request, tracker: MetricsTracker = None) -> GenerateResponse:
    if tracker:
        with tracker.phase("core_generation"):
            # existing code...
            core = await self.client.invoke(CORE_PROMPT, core_input)
            # Get usage from response if available
            if hasattr(core, "_usage"):
                tracker.set_token_usage("core", {
                    "prompt_tokens": core._usage.prompt_tokens,
                    "completion_tokens": core._usage.completion_tokens,
                })
```

### Step 3: Store Metrics

Create a metrics storage layer (database, file, or service):

```python
import json
from datetime import datetime

class MetricsStore:
    def save(self, metrics_dict: dict) -> None:
        """Save metrics to file or database"""
        filename = f"metrics/{metrics_dict['run_id']}.json"
        with open(filename, 'w') as f:
            json.dump(metrics_dict, f, indent=2)
        print(f"[Metrics] Saved to {filename}")

# In generate.py
store = MetricsStore()
store.save(tracker.get_metrics_dict())
```

---

## Realistic Value Examples

### Successful Run (12-slide deck)

```
Duration: 6-7 minutes total
  - Summarization: 8-10s
  - Core generation: 40-45s
  - Diagram generation: 15-20s
  - Diagram rendering: 50-60s
  - PPTX generation: 12-15s
  - Assembly: 5-8s
  - Validation: 3-5s

Tokens:
  - Summarization: 2.5K total
  - Core: 14K total
  - Diagram: 6K total
  - Total: 22-25K tokens

Cost: $0.020 - $0.035

Quality:
  - Content: 0.85-0.98
  - Diagram: 0.80-0.95
  - Alignment: 0.90-0.99
  - Validity: 0.95-1.0
  - Overall: 0.88-0.98

Success Rates:
  - Slides: 100% (12/12)
  - Diagram: 100% coverage
  - PPTX Health: 100%
```

### Failed Run (Diagram Rendering Timeout)

```
Duration: 2.5-3 minutes (stopped early)
  - Summarization: 7-9s
  - Core generation: 38-42s
  - Diagram generation: 16-18s
  - Diagram rendering: 45s (TIMEOUT)
  - Rest: 0 (not attempted)

Tokens:
  - Summarization: 2.2K
  - Core: 13.3K
  - Diagram: 5.7K
  - Total: 21.2K

Cost: $0.018 (partial run)

Quality:
  - Content: 0.78 (incomplete)
  - Diagram: 0.0 (failed)
  - Alignment: 0.82
  - Validity: 0.0 (no PPTX)
  - Overall: 0.40

Success Rates:
  - Slides: 0% (0/12 — stopped)
  - Diagram: 0%
  - PPTX Health: 0%

Error: diagram_rendering / rendering_error
```

---

## FAQ

**Q: How do I calculate the expected components/connections for diagram correctness?**
A: Extract from the BRD during the core generation phase. Have the LLM identify the expected count, then compare during diagram generation.

**Q: Can I adjust the pricing model?**
A: Yes! In `metrics_models.py`, update the constants in `TokenUsageModel.estimated_cost_usd()`.

**Q: How are quality scores determined?**
A: These should be calculated during generation:

- `content_quality`: Based on content length, specificity, relevance
- `diagram_quality`: Based on visual completeness and accuracy
- `architecture_alignment`: Compare generated architecture against BRD
- `output_validity`: From PPTX validation checks

**Q: Can metrics be sent to an external service?**
A: Yes! Implement an HTTP POST in your metrics storage layer to send to your analytics backend.

**Q: Are metrics critical for the generation to work?**
A: No! The metrics are non-intrusive and won't break the pipeline if integration fails. Metrics are "nice to have" monitoring.

---

## Next Steps

1. Copy `metrics_models.py` and `metrics_tracker.py` to your backend
2. Update `generate.py` to instantiate `MetricsTracker`
3. Integrate phase tracking with context managers
4. Add token usage extraction after each LLM call
5. Call `finalize()` before returning response
6. Implement metrics storage/logging
7. Monitor metrics to identify performance patterns
