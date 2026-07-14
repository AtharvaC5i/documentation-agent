from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class QualityScoreResult:
    score: float
    method: str
    scale: str
    word_count: int
    has_headers: bool
    has_bullets: bool
    has_code: bool
    has_tables: bool
    keyword_match_ratio: float


import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def score_quality(section_name: str, content: str) -> float:
    if not content or not content.strip():
        return 0.0

    try:
        api_key = os.getenv("DATABRICKS_TOKEN")
        base_url = os.getenv("DATABRICKS_HOST")
        endpoint = os.getenv("DATABRICKS_ENDPOINT_NAME") or os.getenv("DATABRICKS_MODEL_ENDPOINT")
        
        if api_key and base_url and endpoint:
            # Ensure serving-endpoints is appended if missing from host url
            if not base_url.endswith("serving-endpoints"):
                base_url = f"{base_url.rstrip('/')}/serving-endpoints"
                
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            
            # Truncate content to first 1200 characters to keep token consumption extremely low (~200 tokens)
            preview = content[:1200]
            
            system_prompt = "Score the technical document section from 0.0 to 1.0 based on technical depth, formatting structure (headers/code blocks/lists), and content clarity. Respond with ONLY the float number (e.g. 0.85)."
            user_msg = f"Section: {section_name}\nContent Preview:\n{preview}\n\nScore:"
            
            response = client.chat.completions.create(
                model=endpoint,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=10,
            )
            
            val = response.choices[0].message.content.strip()
            match = re.search(r'([0-1]\.\d+)', val)
            if match:
                return float(match.group(1))
            if "1.0" in val or "1" in val:
                return 1.0
            if "0" in val:
                return 0.0
    except Exception as e:
        print(f"⚠️ [QualityScorer] Dynamic LLM scoring failed: {e}. Falling back to heuristic.")

    # Fallback to a simpler heuristic to prevent runtime exceptions
    score = 0.0
    words = content.split()
    word_count = len(words)

    if word_count >= 300:
        score += 0.4
    elif word_count >= 150:
        score += 0.25
    elif word_count >= 50:
        score += 0.1

    if "#" in content:
        score += 0.2
    if "```" in content:
        score += 0.2
    if "|" in content:
        score += 0.2

    return round(min(score, 1.0), 2)


def score_quality_detailed(section_name: str, content: str) -> Dict[str, Any]:
    if not content or not content.strip():
        return {
            "score": 0.0,
            "method": "heuristic_length_structure_keyword",
            "scale": "0_to_1",
            "word_count": 0,
            "has_headers": False,
            "has_bullets": False,
            "has_code": False,
            "has_tables": False,
            "keyword_match_ratio": 0.0,
        }

    words = content.split()
    word_count = len(words)
    has_headers = "#" in content
    has_bullets = "- " in content or "* " in content
    has_code = "```" in content
    has_tables = "|" in content

    section_keywords = section_name.lower().split()
    content_lower = content.lower()
    matches = sum(1 for kw in section_keywords if kw in content_lower)
    keyword_ratio = matches / max(len(section_keywords), 1)

    return {
        "score": score_quality(section_name, content),
        "method": "heuristic_length_structure_keyword",
        "scale": "0_to_1",
        "word_count": word_count,
        "has_headers": has_headers,
        "has_bullets": has_bullets,
        "has_code": has_code,
        "has_tables": has_tables,
        "keyword_match_ratio": round(keyword_ratio, 3),
    }