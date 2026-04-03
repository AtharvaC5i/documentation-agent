"""
Databricks Model Serving client
Handles all API calls to Databricks served models
"""

import os
import httpx
import json
from typing import Optional


DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
DATABRICKS_MODEL_ENDPOINT = os.getenv("DATABRICKS_MODEL_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")


async def call_databricks_llm(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    temperature: float = 0.2,
    json_mode: bool = False
) -> str:
    """
    Call Databricks served model via OpenAI-compatible API.

    Args:
        system_prompt: System instruction for the model
        user_prompt: User message / task
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (lower = more deterministic)
        json_mode: If True, instructs model to return only valid JSON

    Returns:
        Generated text string
    """
    if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
        raise ValueError(
            "DATABRICKS_HOST and DATABRICKS_TOKEN environment variables must be set. "
            "Set them in your .env file."
        )

    url = f"{DATABRICKS_HOST}/serving-endpoints/{DATABRICKS_MODEL_ENDPOINT}/invocations"

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    if json_mode:
        system_prompt += "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, no code fences."

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(
                f"Databricks API error {response.status_code}: {response.text}"
            )

        data = response.json()

        # Handle both OpenAI-compatible and Databricks native response formats
        if "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
        elif "predictions" in data:
            return data["predictions"][0].strip()
        else:
            raise Exception(f"Unexpected response format: {data}")


def parse_llm_json(text: str) -> dict:
    """
    Safely parse JSON from LLM response.
    Handles markdown fences, language specifiers, and truncated responses.
    Truncation happens when max_tokens is hit mid-output — we recover
    all complete objects rather than failing entirely.
    """
    text = text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = text.strip()

    # Remove "json" language specifier left over from fences
    if text.lower().startswith("json"):
        text = text[4:].strip()

    # Attempt 1 — clean parse (response was complete)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 2 — array truncated mid-object, recover all complete objects
    if text.startswith("["):
        candidate = _recover_truncated_array(text)
        if candidate is not None:
            return candidate

    # Attempt 3 — object truncated mid-key or mid-value
    if text.startswith("{"):
        candidate = _recover_truncated_object(text)
        if candidate is not None:
            return candidate

    raise ValueError(
        f"Failed to parse LLM JSON response even after recovery attempts.\n"
        f"Raw text (first 400 chars): {text[:400]}"
    )


def _recover_truncated_array(text: str) -> list:
    """
    Recover a JSON array cut off before the closing bracket.
    Walks backwards finding the last complete object, closes the array after it.
    """
    i = len(text) - 1
    while i > 0:
        pos = text.rfind("}", 0, i + 1)
        if pos == -1:
            break
        candidate_text = text[:pos + 1].rstrip() + "\n]"
        try:
            result = json.loads(candidate_text)
            if isinstance(result, list) and len(result) > 0:
                return result
        except json.JSONDecodeError:
            pass
        i = pos - 1
    return None


def _recover_truncated_object(text: str) -> dict:
    """
    Recover a JSON object truncated before the closing brace.
    """
    candidate_text = text.rstrip() + "}"
    try:
        return json.loads(candidate_text)
    except json.JSONDecodeError:
        pass
    return None


def score_quality(content: str, section_name: str) -> float:
    """
    Simple heuristic quality scorer for generated sections.
    Returns score 0.0 - 1.0
    In production this would be an LLM-as-judge call.
    """
    score = 0.0

    if len(content) < 100:
        return 0.1

    # Length check
    if len(content) > 300:
        score += 0.3
    if len(content) > 800:
        score += 0.1

    # Structure checks
    if any(marker in content for marker in ["##", "**", "- ", "1.", "•"]):
        score += 0.2

    # Section-specific keyword checks
    keywords_map = {
        "executive summary": ["business", "solution", "objective", "scope"],
        "functional requirements": ["FR-", "shall", "user", "system"],
        "non-functional requirements": ["performance", "security", "availability", "scalability"],
        "business rules": ["rule", "must", "cannot", "only", "always"],
        "stakeholder": ["name", "role", "responsibility"],
        "scope": ["in scope", "out of scope", "included", "excluded"],
        "assumptions": ["assume", "assumed", "assumption"],
        "constraints": ["constraint", "limited", "must use", "required to"],
        "integrations": ["api", "integration", "sync", "connect"],
        "glossary": ["term", "definition", "means"],
    }

    section_lower = section_name.lower()
    for key, words in keywords_map.items():
        if key in section_lower:
            matches = sum(1 for w in words if w.lower() in content.lower())
            score += min(0.3, matches * 0.08)
            break

    return min(1.0, score)
