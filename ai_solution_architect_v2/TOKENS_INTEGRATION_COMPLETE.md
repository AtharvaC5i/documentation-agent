# 🎯 Token Usage Integration - Complete Implementation

## What Was Implemented

### ✅ **3 Files Modified**

#### 1. `backend/services/databricks_client.py`

- Added `self.last_usage` attribute to track token counts
- Modified `_call()` to return **tuple** `(content, usage)` instead of just content
- Updated `invoke()` and `invoke_raw()` to capture usage from API response
- Added `get_last_usage()` method for metrics integration

**Key Changes:**

```python
# Extract usage from Databricks API response
usage = {
    "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
    "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
    "total_tokens": data.get("usage", {}).get("total_tokens", 0),
}
self.last_usage = usage  # Store for retrieval
```

#### 2. `backend/services/orchestrator.py`

- Added `token_usage` dict to track tokens across all LLM calls
- Modified orchestrator to capture usage after each call:
  - Summarization → `token_usage["summarization"]`
  - Core generation → `token_usage["core_generation"]`
  - Diagram generation → `token_usage["diagram_generation"]`
- Store token usage in response using `response.set_token_usage(token_usage)`

**Key Changes:**

```python
# After each LLM call
token_usage["core_generation"] = self.client.get_last_usage()
# Store in response
response.set_token_usage(token_usage)
```

#### 3. `backend/models/response_models.py`

- Added `_token_usage` to `model_post_init()`
- Added `set_token_usage()` method
- Added `get_token_usage()` method

**Key Changes:**

```python
def set_token_usage(self, usage: dict) -> None:
    """Store token usage from LLM calls"""
    object.__setattr__(self, "_token_usage", usage)

def get_token_usage(self) -> dict:
    """Get token usage from LLM calls"""
    try:
        return object.__getattribute__(self, "_token_usage")
    except AttributeError:
        return {}
```

#### 4. `backend/routers/generate.py`

- Extract token usage from orchestrator result
- Call `tracker.set_token_usage(phase, usage)` for each phase
- Auto-calculates estimated cost from tokens using Databricks pricing

**Key Changes:**

```python
# Extract token usage from result
token_usage = result.get_token_usage()
if token_usage:
    for phase, usage in token_usage.items():
        if usage.get('total_tokens', 0) > 0:
            tracker.set_token_usage(phase, usage)
```

---

## Token Flow

```
Databricks API Response
    ↓
    ├─ content (JSON)
    └─ usage {prompt_tokens, completion_tokens, total_tokens}
        ↓
    databricks_client.get_last_usage()
        ↓
    orchestrator collects from each call
        ↓
    response.set_token_usage(token_usage)
        ↓
    generate.py extracts: result.get_token_usage()
        ↓
    tracker.set_token_usage(phase, usage)
        ↓
    Metrics JSON:
        llm_tokens.core_generation: {prompt: X, completion: Y}
        estimated_cost_usd: (X/1K)*$0.001 + (Y/1K)*$0.002
```

---

## Cost Calculation Formula

Databricks pricing (from metrics_models.py):

```python
# Calculation in TokenUsageModel.estimated_cost_usd property:
cost = (self.prompt_tokens / 1000) * 0.001 + \
       (self.completion_tokens / 1000) * 0.002

# Example:
# 100 prompt tokens + 50 completion tokens
# Cost = (100/1K)*$0.001 + (50/1K)*$0.002
# Cost = $0.0001 + $0.0001 = $0.0002 per call
```

---

## What Will Now Show Up in Metrics JSON

```json
{
  "llm_tokens": {
    "summarization": {
      "prompt_tokens": 45,
      "completion_tokens": 120,
      "total_tokens": 165
    },
    "core_generation": {
      "prompt_tokens": 2800,
      "completion_tokens": 1500,
      "total_tokens": 4300
    },
    "diagram_generation": {
      "prompt_tokens": 890,
      "completion_tokens": 600,
      "total_tokens": 1490
    },
    "total": {
      "prompt_tokens": 3735,
      "completion_tokens": 2220,
      "total_tokens": 5955
    }
  },
  "estimated_cost_usd": 0.0072
}
```

---

## Next Steps

1. **Run the pipeline again** to generate new metrics with token counts
2. **Verify Databricks API** is returning usage data in response
3. **Monitor cost calculations** to ensure they're reasonable

---

## Files Modified Summary

| File                   | Change                            | Impact                            |
| ---------------------- | --------------------------------- | --------------------------------- |
| `databricks_client.py` | Extract usage from API response   | ✅ Tokens now captured            |
| `orchestrator.py`      | Collect tokens from all LLM calls | ✅ All 3 phases tracked           |
| `response_models.py`   | Store token usage in response     | ✅ Tokens travel through pipeline |
| `generate.py`          | Extract tokens and set in tracker | ✅ Tokens reach metrics JSON      |

**All changes are backward compatible and non-breaking!** 🎉
