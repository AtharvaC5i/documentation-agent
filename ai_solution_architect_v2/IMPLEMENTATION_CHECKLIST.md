# Metrics Implementation Checklist

Use this checklist to ensure your metrics system is properly integrated.

---

## 📋 Setup Phase

- [ ] **Create `metrics_models.py`**
  - Location: `backend/models/metrics_models.py`
  - Contains: All metric data classes with formulas
  - Verify: Can import `from models.metrics_models import GenerationMetricsModel`

- [ ] **Create `metrics_tracker.py`**
  - Location: `backend/services/metrics_tracker.py`
  - Contains: Tracking service and helper functions
  - Verify: Can import `from services.metrics_tracker import MetricsTracker`

- [ ] **Create metrics storage layer** (choose one)
  - [ ] File-based: `backend/services/metrics_store.py` → `FileMetricsStore`
  - [ ] Database: Implement `DatabaseMetricsStore`
  - [ ] Analytics: Implement `AnalyticsMetricsStore`
  - [ ] Hybrid: Multiple storage backends

---

## 🔧 Integration Phase

### In `generate.py`

- [ ] **Add imports**

  ```python
  from services.metrics_tracker import MetricsTracker, classify_error
  import traceback
  ```

- [ ] **Create tracker at start**

  ```python
  tracker = MetricsTracker()
  ```

- [ ] **Wrap phases with tracking**
  - [ ] Summarization: `with tracker.phase("summarization"):`
  - [ ] Core generation: `with tracker.phase("core_generation"):`
  - [ ] PPTX generation: `with tracker.phase("pptx_generation"):`
  - [ ] Validation: `with tracker.phase("validation"):`

- [ ] **Set token usage**

  ```python
  tracker.set_token_usage("core", usage_dict)
  ```

- [ ] **Validate PPTX**

  ```python
  tracker.validate_pptx(pptx_file_path)
  ```

- [ ] **Update quality scores**

  ```python
  tracker.update_quality_scores(0.92, 0.88, 0.95, 1.0)
  ```

- [ ] **Update diagram metrics**

  ```python
  tracker.update_diagram_metrics(attempted, success, comp_count, conn_count, ...)
  ```

- [ ] **Update slide metrics**

  ```python
  tracker.update_slide_metrics(attempted, successful, failed, retry_count)
  ```

- [ ] **Finalize on success**

  ```python
  tracker.finalize(success=True)
  metrics_dict = tracker.get_metrics_dict()
  ```

- [ ] **Finalize on error**

  ```python
  except Exception as e:
      stage, category = classify_error(e)
      tracker.set_error(stage, category, str(e))
      tracker.finalize(success=False)
      metrics_dict = tracker.get_metrics_dict()
  ```

- [ ] **Store metrics**
  ```python
  await metrics_store.save(metrics_dict)
  ```

### In `orchestrator.py` (Optional)

- [ ] **Track phase durations** (if not using generate.py phases)
  - Use `time.time()` to measure each phase
  - Set `tracker.metrics.duration_phase_name = duration`

- [ ] **Extract token usage** from LLM responses
  - Use `extract_token_usage()` helper
  - Call `tracker.set_token_usage(phase, usage)`

---

## ✅ Verification Phase

### Code Quality

- [ ] **No syntax errors**

  ```bash
  python -m py_compile backend/models/metrics_models.py
  python -m py_compile backend/services/metrics_tracker.py
  ```

- [ ] **Imports work**

  ```python
  python -c "from models.metrics_models import GenerationMetricsModel; print('OK')"
  python -c "from services.metrics_tracker import MetricsTracker; print('OK')"
  ```

- [ ] **No breaking changes to existing code**
  - [ ] Orchestrator still works without tracker
  - [ ] PPTX service unchanged
  - [ ] All existing tests pass

### Metrics Content

- [ ] **All 14 metrics are present** in example JSON:
  - [ ] Run success/failure
  - [ ] Error stage
  - [ ] Error category
  - [ ] End-to-end duration
  - [ ] LLM token usage
  - [ ] Estimated cost
  - [ ] Slide success rate
  - [ ] Retry count
  - [ ] Basic quality score
  - [ ] Diagram correctness
  - [ ] Architecture justification
  - [ ] PPTX health
  - [ ] Review cycle count
  - [ ] Acceptance status

- [ ] **Calculate formulas are correct**
  - [ ] Cost: `(prompt_tokens/1K)*0.001 + (completion_tokens/1K)*0.002`
  - [ ] Quality: `(content + diagram + alignment + validity) / 4`
  - [ ] Diagram: `(comp_cov*0.6 + conn_cov*0.4) * success_mult`
  - [ ] PPTX Health: `passing_validations / 6`
  - [ ] Justification: `decisions_justified / decisions_identified`

- [ ] **Realistic value ranges** (for successful run):
  - [ ] Duration: 360-450 seconds
  - [ ] Tokens: 14-25K
  - [ ] Cost: $0.015-$0.035
  - [ ] Quality: 0.88-0.98
  - [ ] Diagram: 0.85-1.0
  - [ ] Success Rate: 1.0 (100%)

### Test Run

- [ ] **Execute a test generation**

  ```bash
  curl -X POST http://localhost:8000/generate-pptx \
    -F "brd_text=Test BRD" \
    -F "tech_doc_text=Test Tech Doc" \
    -o test.pptx
  ```

- [ ] **Verify metrics file created**

  ```bash
  ls -la metrics/  # Should have new JSON file
  ```

- [ ] **Check metrics JSON structure**

  ```bash
  cat metrics/*.json | python -m json.tool  # Should be valid JSON
  ```

- [ ] **Verify all fields populated**

  ```python
  import json
  with open('metrics/run_id.json') as f:
      metrics = json.load(f)
      assert metrics['run_success'] is not None
      assert metrics['duration']['total_seconds'] > 0
      assert metrics['llm_tokens']['total']['total_tokens'] > 0
      print("✓ All fields present")
  ```

- [ ] **Check calculations**
  ```python
  # Verify cost calculation
  total_tokens = metrics['llm_tokens']['total']['total_tokens']
  prompt = metrics['llm_tokens']['total']['prompt_tokens']
  completion = metrics['llm_tokens']['total']['completion_tokens']
  expected_cost = (prompt/1000)*0.001 + (completion/1000)*0.002
  actual_cost = metrics['estimated_cost_usd']
  assert abs(expected_cost - actual_cost) < 0.0001
  print(f"✓ Cost calculation correct: ${actual_cost:.4f}")
  ```

---

## 📊 Validation Phase

### Compare to Examples

- [ ] **Load `EXAMPLE_METRICS_OUTPUT.json`**
  - Has all 14 metrics ✓
  - Duration: 392.53 seconds (realistic)
  - Tokens: 23,625 (realistic)
  - Cost: $0.0213 (correct formula)
  - Quality: 0.9375 (correct average)
  - Diagram: 1.0 (correct calculation)
  - PPTX Health: 1.0 (6/6 validations)

- [ ] **Load `EXAMPLE_METRICS_OUTPUT_FAILURE.json`**
  - Has error details ✓
  - Stage: diagram_rendering
  - Category: rendering_error
  - Early termination (no PPTX phases)
  - Quality: 0.4 (lower overall)
  - PPTX Health: 0.0 (file not created)

- [ ] **Your first run looks similar**
  - Same structure as examples
  - Reasonable value ranges
  - All calculations match formulas

---

## 🚀 Deployment Phase

### Before Going Live

- [ ] **Load testing**
  - Generate 5-10 PDFs and check metrics consistency
  - Verify no performance regression (duration unchanged)
  - Confirm metrics don't consume excessive disk space

- [ ] **Error handling**
  - Test error classification (simulate API failure, timeout, etc.)
  - Verify error_details captured correctly
  - Ensure metrics stored even on failure

- [ ] **Storage backend**
  - [ ] Metrics files persist correctly (if file-based)
  - [ ] Database schema correct (if DB-based)
  - [ ] API endpoints working (if analytics-based)
  - [ ] Backup/retention policy defined

### After Deployment

- [ ] **Monitor first 20 runs**
  - Check for unexpected error patterns
  - Verify cost estimates are accurate
  - Validate quality score distribution

- [ ] **Set up alerts**
  - Success rate < 95%
  - Duration > 480 seconds
  - Cost > $0.05 per run
  - Error rate > 5%

- [ ] **Create dashboard**
  - Real-time success/failure counts
  - Duration trend (average, p95, p99)
  - Cost per run and monthly total
  - Quality score distribution
  - Error category breakdown

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'metrics_models'"

**Solution:**

```bash
# Verify file exists
ls backend/models/metrics_models.py

# Ensure __init__.py exists
touch backend/models/__init__.py
```

### Issue: "Tracker not recording token usage"

**Solution:**

```python
# Make sure you're calling set_token_usage with correct data
response = await client.invoke(prompt, text)
usage = response.get("usage") or response.usage  # Try both patterns
tracker.set_token_usage("core", {
    "prompt_tokens": usage.prompt_tokens,
    "completion_tokens": usage.completion_tokens,
})
```

### Issue: "PPTX validation always fails"

**Solution:**

```python
# Verify PPTX is saved to disk before validation
with open("/tmp/output.pptx", "wb") as f:
    f.write(pptx_bytes)

# Then validate
tracker.validate_pptx("/tmp/output.pptx")
```

### Issue: "Metrics JSON file not created"

**Solution:**

```python
# Verify storage is called and async is awaited
tracker.finalize(success=True)
metrics_dict = tracker.get_metrics_dict()

# If using async storage:
await metrics_store.save(metrics_dict)  # Don't forget await!

# Verify directory exists
import os
os.makedirs("metrics", exist_ok=True)
```

### Issue: "Cost calculation doesn't match formula"

**Solution:**

```python
# Verify token counts are being set
print(tracker.metrics.token_usage_core)
# Should show: TokenUsageModel(prompt_tokens=X, completion_tokens=Y)

# Verify pricing constants
# Check metrics_models.py TokenUsageModel.estimated_cost_usd()
# Adjust if your pricing differs from Databricks defaults
```

---

## 📝 Documentation Checklist

- [ ] **README updated** with metrics overview
- [ ] **Developer guide** has integration instructions
- [ ] **API docs** mention metrics collection
- [ ] **Monitoring guide** explains metric meanings
- [ ] **Example JSON** stored in repo
- [ ] **Formulas documented** in code comments

---

## ✨ Final Verification

Before calling complete:

```python
# Quick test script
from models.metrics_models import GenerationMetricsModel
from services.metrics_tracker import MetricsTracker
import json

# Create and populate metrics
tracker = MetricsTracker()
tracker.update_quality_scores(0.92, 0.88, 0.95, 1.0)
tracker.finalize(success=True)

# Verify all calculations
metrics = tracker.get_metrics()
assert metrics.quality_scores.overall_score == 0.9375
assert metrics.run_success == True
assert metrics.duration_total > 0

# Verify JSON serialization
metrics_dict = tracker.get_metrics_dict()
json_str = json.dumps(metrics_dict, indent=2)
assert len(json_str) > 0

print("✅ All metrics working correctly!")
print(f"Sample output:\n{json_str[:500]}...")
```

Expected output:

```
✅ All metrics working correctly!
Sample output:
{
  "run_id": "...",
  "timestamp_start": "...",
  "run_success": true,
  "error_details": {
    "occurred": false,
    ...
```

---

## 🎯 Success Criteria

- ✅ All 14 metrics are tracked
- ✅ Formulas are correct and match documentation
- ✅ No errors in implementation
- ✅ PPTX generation still works without metrics
- ✅ Metrics are stored persistently
- ✅ Example outputs match calculated values
- ✅ Integration takes < 30 minutes
- ✅ Zero breaking changes to existing code

---

## 📞 Support

If you encounter issues:

1. **Check the example JSON files** — Do your values look reasonable?
2. **Review the formulas** — Are calculations matching `METRICS_QUICK_REFERENCE.md`?
3. **Test with example data** — Does `EXAMPLE_METRICS_OUTPUT.json` load correctly?
4. **Review integration code** — Does your code match patterns in `INTEGRATION_CODE_EXAMPLES.md`?
5. **Check the troubleshooting section** above

---

## 📅 Completion Estimate

- **Setup**: 5 minutes (copy files)
- **Integration**: 15-20 minutes (update generate.py + orchestrator)
- **Testing**: 5-10 minutes (verify with test run)
- **Documentation**: 5 minutes (update README, team wiki)

**Total**: ~30-40 minutes for complete implementation
