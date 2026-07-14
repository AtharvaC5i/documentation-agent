"""
databricks_client.py

Wraps Databricks model-serving endpoint.
  invoke()     — expects JSON back, returns dict
  invoke_raw() — returns raw text string
"""

import os
import logging
import httpx
import json


logger = logging.getLogger(__name__)


class DatabricksClient:
    def __init__(self):
        self.host     = os.getenv("DATABRICKS_HOST", "")
        self.endpoint = os.getenv("DATABRICKS_ENDPOINT", "")
        self.token    = os.getenv("DATABRICKS_TOKEN", "")

        if not self.host or not self.endpoint or not self.token:
            raise ValueError(
                "Missing Databricks environment variables: "
                "DATABRICKS_HOST, DATABRICKS_ENDPOINT, DATABRICKS_TOKEN"
            )
        if not self.host.startswith("http"):
            raise ValueError("DATABRICKS_HOST must include https://")

        self.url = f"{self.host}/serving-endpoints/{self.endpoint}/invocations"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        # Track last usage for metrics collection
        self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.retry_count = 0

    # ── Low-level call ────────────────────────────────────────

    async def _call(self, system_prompt: str, user_message: str, max_tokens: int = 1500) -> tuple:
        """Call Databricks API and return (content, usage_dict)"""
        payload = {
            "messages": [
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": user_message},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }
        
        max_attempts = 3
        attempt = 0
        response = None
        
        while attempt < max_attempts:
            attempt += 1
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(self.url, headers=self.headers, json=payload)
                
                if response.status_code != 200:
                    raise Exception(
                        f"Databricks API error ({response.status_code}): "
                        f"{response.text[:400]}"
                    )
                break  # Success!
            except Exception as e:
                if attempt >= max_attempts:
                    raise  # Re-raise the exception if we have exhausted all attempts
                self.retry_count += 1
                import asyncio
                logger.warning(f"[DatabricksClient] Attempt {attempt} failed: {e}. Retrying in 2 seconds...")
                await asyncio.sleep(2.0)

        try:
            data = response.json()
        except Exception:
            raise Exception("Invalid JSON response from Databricks model")

        if "choices" not in data or not data["choices"]:
            raise Exception("Unexpected response format: missing 'choices'")

        content = data["choices"][0]["message"]["content"]
        
        # ← DEBUG: Log response structure to identify usage field
        logger.info(f"[DatabricksClient] Response keys: {list(data.keys())}")
        if "usage" in data:
            logger.info(f"[DatabricksClient] Found 'usage': {data['usage']}")
        else:
            logger.info(f"[DatabricksClient] No 'usage' key found in response. Available keys: {list(data.keys())}")
        
        # Extract usage info (Databricks API includes this in response)
        usage = {
            "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
            "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
            "total_tokens": data.get("usage", {}).get("total_tokens", 0),
        }
        
        # ← FALLBACK: If no usage in response, estimate from prompt/completion length
        # (1 token ≈ 4 characters is a common approximation)
        logger.info(f"[DatabricksClient] BEFORE FALLBACK - prompt_tokens: {usage['prompt_tokens']}, completion_tokens: {usage['completion_tokens']}")
        
        if usage["prompt_tokens"] == 0:
            estimated_prompt_tokens = max(1, len(system_prompt + user_message) // 4)
            logger.info(f"[DatabricksClient] APPLYING FALLBACK - prompt length: {len(system_prompt + user_message)}, estimated tokens: {estimated_prompt_tokens}")
            usage["prompt_tokens"] = estimated_prompt_tokens
        
        if usage["completion_tokens"] == 0:
            estimated_completion_tokens = max(1, len(content) // 4)
            logger.info(f"[DatabricksClient] APPLYING FALLBACK - content length: {len(content)}, estimated tokens: {estimated_completion_tokens}")
            usage["completion_tokens"] = estimated_completion_tokens
        
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        
        logger.info(f"[DatabricksClient] AFTER FALLBACK - total_tokens: {usage['total_tokens']} (prompt: {usage['prompt_tokens']}, completion: {usage['completion_tokens']})")
        
        # Store for later retrieval
        self.last_usage = usage
        
        return content, usage

    # ── Public: returns parsed dict ───────────────────────────
    # FIX: max_tokens raised from 1500 to 4000.
    # The CORE_PROMPT response is a large nested JSON (components, roadmap,
    # risks, tech stack, NFRs etc.). At 1500 tokens it was being truncated
    # mid-JSON, causing _try_parse_json to fail silently and return
    # _fallback_response() — resulting in all-empty slides.

    async def invoke(self, system_prompt: str, user_message: str) -> dict:
        """Call API and return parsed JSON (usage stored in self.last_usage)"""
        from utils.semantic_cache import get_cache, set_cache
        cached = get_cache(system_prompt, user_message)
        if cached is not None:
            self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return cached

        raw, usage = await self._call(system_prompt, user_message, max_tokens=4000)
        cleaned = _strip_markdown_fences(raw)
        parsed  = _try_parse_json(cleaned)
        if parsed is not None:
            set_cache(system_prompt, user_message, parsed)
            return parsed
        # Log clearly so truncation / bad JSON is visible in server logs
        logger.warning(
            "[DatabricksClient] JSON parse failed — returning empty fallback response.\n"
            "This usually means the model response was truncated (increase max_tokens)\n"
            "or the model returned non-JSON text.\n"
            f"Raw response preview (first 600 chars):\n{cleaned[:600]}"
        )
        return self._fallback_response()

    # ── Public: returns raw text ──────────────────────────────

    async def invoke_raw(self, system_prompt: str, user_message: str) -> str:
        """Call API and return raw text (usage stored in self.last_usage)"""
        from utils.semantic_cache import get_cache, set_cache
        cached = get_cache(system_prompt, user_message)
        if cached is not None:
            self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return cached

        raw, usage = await self._call(system_prompt, user_message, max_tokens=800)
        content = _strip_markdown_fences(raw).strip()
        set_cache(system_prompt, user_message, content)
        return content
    
    def get_last_usage(self) -> dict:
        """Get token usage from last API call"""
        return self.last_usage.copy()

    # ── Fallback ──────────────────────────────────────────────

    def _fallback_response(self) -> dict:
        return {
            "project":           {"name": "Solution Architecture", "tagline": "", "client_context": ""},
            "alignment":         {"goals": [], "business_value": "", "success_metrics": []},
            "problem_statement": {"current_pain_points": [], "impact": "", "root_cause": ""},
            "proposed_solution": {"summary": "", "key_differentiators": [], "approach": ""},
            "architecture":      {"pattern": "", "frontend": "", "backend": "", "ai_layer": "",
                                  "data_store": "", "hosting": "", "components": []},
            "data_flow":         [],
            "technology_stack":  {"frontend": [], "backend": [], "ai_ml": [],
                                  "data": [], "infrastructure": [], "security": []},
            "non_functional":    {"scalability": "", "security": "", "availability": "",
                                  "performance": "", "compliance": ""},
            "roadmap":           [],
            "risks":             [],
            "assumptions":       [],
            "open_questions":    [],
        }


# ── Helpers ───────────────────────────────────────────────────

def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _try_parse_json(text: str) -> dict | None:
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try extracting first {...} block
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass
    return None