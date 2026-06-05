# 🔍 Metrics - Token Zero Issue Diagnosis

## Current Run Status

✅ **Working Perfectly (12/14 KPIs):**
- Duration: 72.06s ✅
- Slides: 10/10 ✅
- Diagram: 8 components, 8 connections, score 1.0 ✅
- Quality: 0.98 overall ✅
- PPTX: Perfect health (1.0) ✅
- Architecture: 6/6 decisions justified ✅

❌ **Still Zero (2/14 KPIs):**
- `llm_tokens.total.*`: all 0
- `estimated_cost_usd`: 0.0

---

## Problem Analysis

The fallback token estimation should have triggered but didn't. This suggests one of:

1. **Fallback code not executing** - The condition `if usage["prompt_tokens"] == 0:` might not be reached
2. **Tokens not flowing through pipeline** - Estimated tokens not stored in result properly
3. **Tracker not saving tokens** - Token usage calculated but not persisted to JSON

---

## Diagnostic Steps

### Step 1: Check Server Console Output

Please share the server console output from the last run. Look for:

```
[DatabricksClient] Response keys: ['choices', 'model', ...]
[DatabricksClient] No usage data; estimated prompt tokens: XXXX
[DatabricksClient] No usage data; estimated completion tokens: XXXX
[Metrics] ✓ Token usage captured from LLM calls
```

**If you see these lines:** Tokens ARE being estimated, but not reaching metrics JSON  
**If you DON'T see these lines:** Fallback code not executing

### Step 2: Add More Detailed Logging

I'll add debug output to verify tokens at each stage:
- After estimation in `databricks_client.py`
- After collection in `orchestrator.py`
- After extraction in `generate.py`
- After storage in `tracker`

### Step 3: Verify Orchestrator Token Collection

The token collection in orchestrator happens after each LLM call:
```python
token_usage["core_generation"] = self.client.get_last_usage()
```

This should populate with estimated tokens.

---

## Quick Verification Checklist

Please check:

1. **Server Console** - Share last 50 lines from server output
2. **Orchestrator File** - Verify token collection code is in place
3. **Generate.py** - Verify token extraction is in place

---

## Next Action

Share the server console output from your last run, and I'll identify where tokens are being lost in the pipeline.

Example of what to look for:
```
[DatabricksClient] Response keys: ['choices', 'model', 'usage', ...]
     ↓ (fallback triggers if no 'usage')
[DatabricksClient] No usage data; estimated prompt tokens: 2850
[DatabricksClient] No usage data; estimated completion tokens: 1200
     ↓
[Metrics] ✓ Token usage captured from LLM calls
     ↓
metrics/a6f7ee17-xxxx.json saved with populated token counts
```

