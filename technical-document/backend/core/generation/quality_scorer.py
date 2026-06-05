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


def score_quality(section_name: str, content: str) -> float:
    if not content or not content.strip():
        return 0.0

    score = 0.0
    words = content.split()
    word_count = len(words)

    if word_count >= 300:
        score += 0.4
    elif word_count >= 150:
        score += 0.25
    elif word_count >= 50:
        score += 0.1

    has_headers = "#" in content
    has_bullets = "- " in content or "* " in content
    has_code = "```" in content
    has_tables = "|" in content

    structure_count = sum([has_headers, has_bullets, has_code, has_tables])
    score += min(structure_count * 0.1, 0.3)

    section_keywords = section_name.lower().split()
    content_lower = content.lower()
    matches = sum(1 for kw in section_keywords if kw in content_lower)
    keyword_ratio = matches / max(len(section_keywords), 1)
    score += keyword_ratio * 0.3

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