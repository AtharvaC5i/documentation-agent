# 🔧 Token Tracing Guide - What to Look For

## Run This Now

```bash
cd d:\documentation-agent\ai_solution_architect_v2\backend
python main.py  # or your startup command
```

Then generate a PPTX via your API.

---

## Expected Console Output (in order)

### Stage 1: DatabricksClient Token Extraction

```
[DatabricksClient] Response keys: ['choices', 'model', ...]
[DatabricksClient] Found 'usage': {...}
     OR
[DatabricksClient] No 'usage' key found in response...
     ↓
[DatabricksClient] BEFORE FALLBACK - prompt_tokens: 0, completion_tokens: 0
[DatabricksClient] APPLYING FALLBACK - prompt length: 8523, estimated tokens: 2131
[DatabricksClient] APPLYING FALLBACK - content length: 4896, estimated tokens: 1224
[DatabricksClient] AFTER FALLBACK - total_tokens: 3355 (prompt: 2131, completion: 1224)
```

### Stage 2: Orchestrator Token Collection

```
[Orchestrator] Summarization tokens: {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
[Orchestrator] Core generation tokens: {'prompt_tokens': 2131, 'completion_tokens': 1224, 'total_tokens': 3355}
[Orchestrator] Diagram generation tokens: {'prompt_tokens': 890, 'completion_tokens': 600, 'total_tokens': 1490}
[Orchestrator] TOTAL token_usage dict: {
    "summarization": {...},
    "core_generation": {...},
    "diagram_generation": {...}
}
```

### Stage 3: Generate.py Token Extraction

```
[Metrics] DEBUG - extracted token_usage: {
    "summarization": {...},
    "core_generation": {'prompt_tokens': 2131, 'completion_tokens': 1224, 'total_tokens': 3355},
    "diagram_generation": {...}
}
[Metrics] DEBUG - phase 'core_generation': 3355 total_tokens
[Metrics] DEBUG - phase 'diagram_generation': 1490 total_tokens
[Metrics] ✓ Set token usage for core_generation: {...}
[Metrics] ✓ Set token usage for diagram_generation: {...}
[Metrics] ✓ Token usage captured from LLM calls
```

### Stage 4: Metrics Saved

```
[Metrics] Saved to metrics/a6f7ee17-xxxx.json
```

---

## Possible Outcomes

### ✅ Scenario 1: Tokens Show Up in JSON

If you see all the debug output above and the metrics JSON shows non-zero tokens, **WE'RE DONE!** 🎉

### ⚠️ Scenario 2: Debug Output Shows Tokens But JSON Still Zeros

**Problem:** Tokens are being estimated but not reaching the JSON  
**Solution:** Issue is in tracker.set_token_usage() not persisting data

**Next Step:** We'll verify the tracker code

### ❌ Scenario 3: No Debug Output / All Zeros

**Problem:** Fallback code not executing  
**Solution:** Usage might not actually be 0, or there's a different issue

**Next Step:** Check if Databricks IS providing usage data in response

---

## What To Share

Please run the pipeline again and share:

1. **Complete server console output** from start to finish
2. **Specifically highlight:**
   - The `[DatabricksClient]` lines
   - The `[Orchestrator]` lines
   - The `[Metrics]` debug lines

This will show us exactly where tokens are being lost (if at all).

---

## If Tokens STILL Don't Show

If after adding this debug logging tokens still don't appear, it means:

1. **Fallback code isn't running** → Usage is not actually 0
2. **Tokens not persisting** → Tracker isn't saving them
3. **Response structure different** → API format unknown

We can then look at the actual Databricks response structure to understand what format it's using.

---

## Debug Commands

If you want to manually test the token estimation:

```python
# In Python REPL
system_prompt = "You are a helpful assistant"  # ~8 chars
user_message = "Generate architecture design"  # ~30 chars
content_response = "Here is a detailed architecture design..."  # variable

prompt_tokens = len(system_prompt + user_message) // 4  # Should be ~10
completion_tokens = len(content_response) // 4  # Variable

print(f"Estimated: {prompt_tokens} prompt, {completion_tokens} completion")
```

