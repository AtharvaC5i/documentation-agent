# Metrics Quick Reference

## All 14 Metrics at a Glance

| #   | Metric                     | Type        | Priority    | Formula / Calculation                                                                                                                            |
| --- | -------------------------- | ----------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Run success/failure        | Boolean     | 🔴 Critical | `true` if complete, `false` if error                                                                                                             |
| 2   | Error stage                | Enum        | 🔴 Critical | `[summarization, core_generation, diagram_generation, diagram_building, diagram_rendering, pptx_generation, pptx_assembly, validation, unknown]` |
| 3   | Error category             | Enum        | 🔴 Critical | `[api_error, diagram_error, rendering_error, assembly_error, dependency_error, validation_error, timeout_error, memory_error, unknown_error]`    |
| 4   | End-to-end duration        | Float (sec) | 🔴 Critical | `timestamp_end - timestamp_start`                                                                                                                |
| 5   | LLM token usage            | Int, Int    | 🔴 Critical | `prompt_tokens + completion_tokens`                                                                                                              |
| 6   | Estimated cost/run         | Float (USD) | 🔴 Critical | `(prompt_tokens/1K)*$0.001 + (completion_tokens/1K)*$0.002`                                                                                      |
| 7   | Slide success rate         | Float (0-1) | 🟡 High     | `successful_slides / attempted_slides`                                                                                                           |
| 8   | Retry count                | Int         | 🟡 High     | Count of retry attempts                                                                                                                          |
| 9   | Basic quality score        | Float (0-1) | 🟡 High     | `avg(content, diagram, alignment, validity)`                                                                                                     |
| 10  | Diagram correctness        | Float (0-1) | 🔴 Critical | `(comp_coverage*0.6 + conn_coverage*0.4) * success`                                                                                              |
| 11  | Architecture justification | Float (0-1) | 🔴 Critical | `decisions_justified / decisions_identified`                                                                                                     |
| 12  | PPTX health                | Float (0-1) | 🔴 Critical | `passing_validations / total_validations`                                                                                                        |
| 13  | Review cycle count         | Int         | 🟡 High     | Number of feedback loops                                                                                                                         |
| 14  | Acceptance status          | Enum        | 🟡 High     | `[accepted_as_is, minor_edits, major_rework, rejected, pending_review]`                                                                          |

---

## Metrics by Priority

### 🔴 CRITICAL (Leadership KPIs)

- **Run success/failure** — Is the agent working?
- **Error stage + category** — Where/why did it fail?
- **End-to-end duration** — How long does generation take?
- **LLM token usage** — How much compute is consumed?
- **Estimated cost** — What's the unit economics?
- **Diagram correctness** — Is the architecture diagram right?
- **Architecture justification** — Are decisions grounded in inputs?
- **PPTX health** — Does the output actually work?

### 🟡 HIGH (Operational)

- **Slide success rate** — How complete is the output?
- **Retry count** — Is the service stable?
- **Basic quality score** — What's the overall quality?
- **Review cycle count** — How much rework is needed?
- **Acceptance status** — Was it actually usable?

---

## Quick Formula Reference

### Duration Breakdown

```
Total = Summarization + Core + Diagram Gen + Diagram Render + PPTX Gen + Assembly + Validation
Typical: 390-450 seconds (6-7.5 minutes)
```

### Token Usage Totals

```
Summarization:  2-4K tokens
Core:           8-12K tokens
Diagram:        4-8K tokens
─────────────────────────
TOTAL:          14-24K tokens typical
```

### Cost Calculation

```
Prompt Cost =     (prompt_tokens / 1000) × $0.001
Completion Cost = (completion_tokens / 1000) × $0.002
───────────────────────────────────────────────────
Total Cost =      Prompt Cost + Completion Cost

Example: 15.4K prompt, 8.2K completion
  = (15.4 × $0.001) + (8.2 × $0.002)
  = $0.0154 + $0.0164
  = $0.0318 per run
```

### Success Rate

```
success_rate = successful_slides / attempted_slides
Example: 12 successful, 12 attempted = 1.0 (100%)
```

### Quality Score

```
overall_score = (content_quality + diagram_quality +
                 architecture_alignment + output_validity) / 4

Interpretation:
  ≥ 0.90  → Excellent (production-ready)
  0.80-89 → Good (minor issues)
  0.70-79 → Acceptable (needs review)
  < 0.70  → Poor (major rework)
```

### Diagram Correctness

```
component_coverage = actual_components / expected_components
connection_coverage = actual_connections / expected_connections

diagram_score = (component_coverage × 0.6 +
                 connection_coverage × 0.4) × success_multiplier

Where success_multiplier = 1.0 if success else 0.0
```

### PPTX Health

```
health_score = passing_validations / 6

Validations: file_created, valid_xml, valid_relationships,
             opens_without_repair, all_slides_present, all_media_present

1.0 = perfect, 0.833 = 1 failure, 0.667 = 2 failures
```

### Architecture Justification

```
justification_score = decisions_justified / decisions_identified

Example: 6 decisions identified, 6 justified = 1.0 (100% justified)
```

---

## Typical Value Ranges

### ✅ Successful Run (Target Profile)

```
Duration:           360-420 seconds (6-7 min)
Tokens:             18-25K total
Cost:               $0.015-$0.035
Slides:             100% success rate
Quality Overall:    0.88-0.98
Diagram Score:      0.85-1.0
Justification:      0.90-1.0
PPTX Health:        0.95-1.0
Retries:            0-1
Review Cycles:      0
Acceptance:         "accepted_as_is"
```

### ⚠️ Degraded Run (Warning Signs)

```
Duration:           > 480 seconds (8+ min)
Tokens:             > 30K
Cost:               > $0.04
Slides:             < 90% success rate
Quality Overall:    0.70-0.87
Diagram Score:      0.60-0.84
Justification:      0.70-0.89
PPTX Health:        0.80-0.94
Retries:            2-3
Review Cycles:      1-2
Acceptance:         "minor_edits" or "major_rework"
```

### ❌ Failed Run (Failure Profile)

```
Duration:           Early termination (< 180 seconds)
Tokens:             Partial (10-18K)
Cost:               Partial cost incurred (no output)
Slides:             0% (aborted)
Quality Overall:    < 0.50
Diagram Score:      0.0 (failed)
Justification:      Variable (incomplete)
PPTX Health:        0.0 (no file)
Retries:            1+ with no success
Review Cycles:      N/A
Acceptance:         "rejected"
Error Stage:        One of: diagram_rendering, pptx_assembly, etc.
Error Category:     One of: rendering_error, assembly_error, etc.
```

---

## Code Integration Checklist

- [ ] Create `metrics_models.py` with all data classes
- [ ] Create `metrics_tracker.py` with tracking service
- [ ] Import `MetricsTracker` in `generate.py`
- [ ] Add `tracker = MetricsTracker()` before pipeline
- [ ] Wrap each phase with `with tracker.phase("name"):`
- [ ] Call `tracker.set_token_usage()` after each LLM call
- [ ] Call `tracker.validate_pptx()` before returning
- [ ] Call `tracker.finalize(success=True/False)` at end
- [ ] Call `tracker.get_metrics_dict()` to get full payload
- [ ] Store metrics to database/file/analytics service
- [ ] Add error handling to call `tracker.set_error()` on exceptions
- [ ] Test with example JSON files to verify calculations

---

## Example: Integration in One Code Block

```python
from services.metrics_tracker import MetricsTracker, classify_error

@router.post("/generate-pptx")
async def generate_pptx(brd_text: str, tech_doc_text: str, ...):
    tracker = MetricsTracker()

    try:
        # Phase 1
        with tracker.phase("summarization"):
            result = await summarize(tech_doc_text)
            tracker.set_token_usage("summarization", result["usage"])

        # Phase 2
        with tracker.phase("core_generation"):
            core = await orchestrator.run(payload)
            tracker.set_token_usage("core", core["usage"])

        # Phase 3-4 (inside orchestrator)
        # with tracker.phase("diagram_generation"): ...
        # with tracker.phase("diagram_rendering"): ...

        # Generate PPTX
        with tracker.phase("pptx_generation"):
            pptx_bytes = await pptx_service.generate(...)

        # Validate
        with tracker.phase("validation"):
            tracker.validate_pptx("/tmp/out.pptx")
            tracker.update_quality_scores(0.92, 0.88, 0.95, 1.0)
            tracker.update_diagram_metrics(True, True, 8, 11, 8, 10)
            tracker.update_slide_metrics(12, 12, 0, 1)

        # Success
        tracker.finalize(success=True)
        metrics = tracker.get_metrics_dict()

        # Log/store metrics
        await metrics_store.save(metrics)

        return _pptx_response(pptx_bytes)

    except Exception as e:
        stage, category = classify_error(e)
        tracker.set_error(stage, category, str(e))
        tracker.finalize(success=False)
        metrics = tracker.get_metrics_dict()
        await metrics_store.save(metrics)
        raise
```

---

## File Structure

```
backend/
├── models/
│   ├── metrics_models.py          ← NEW: All metric data classes
│   ├── request_models.py
│   └── response_models.py
├── services/
│   ├── metrics_tracker.py         ← NEW: Tracking service
│   ├── orchestrator.py            ← UPDATE: Add tracker phases
│   ├── pptx_service.py
│   └── ...
├── routers/
│   └── generate.py                ← UPDATE: Instantiate tracker
└── main.py
```

---

## Monitoring Dashboard Metrics

For your metrics dashboard, prioritize these KPIs:

### Operational Health

1. **Success Rate** — % of runs completing without errors
2. **Average Duration** — Latency trend
3. **PPTX Health Score** — Output validity percentage

### Cost & Efficiency

4. **Average Cost per Run** — Unit economics
5. **Tokens per Run** — Efficiency trend
6. **Cost per Slide** — Normalized unit metric

### Quality

7. **Average Quality Score** — Overall output quality
8. **Diagram Correctness** — Architecture accuracy
9. **Justification Score** — Decision grounding

### Stability

10. **Error Categories** — Where failures occur
11. **Retry Rate** — Service instability signal
12. **Review Cycle Count** — Rework needed

---

## Alerts & Thresholds

Consider alerting when:

| Metric         | Threshold | Action                                        |
| -------------- | --------- | --------------------------------------------- |
| Success rate   | < 95%     | Investigate errors                            |
| Avg duration   | > 480s    | Check bottlenecks (usually diagram rendering) |
| Error rate     | > 5%      | Review recent changes                         |
| Diagram score  | < 0.8     | Review LLM prompts                            |
| PPTX health    | < 0.95    | Check PPTX merge logic                        |
| Estimated cost | > $0.05   | Check token efficiency                        |
