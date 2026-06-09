"""
SMART-based requirement quality scorer (KPI 9).

Evaluates each requirement description against:
  S — Specific     (has subject + action verb)
  M — Measurable   (quantifiable criteria)
  A — Achievable   (no impossible claims)
  R — Relevant     (sufficient context)
  T — Time-bound   (temporal reference)

Returns aggregated metrics for the full requirements pool.
"""

import re
from typing import List, Dict, Any


# ── Compiled patterns ──────────────────────────────────────────────────────

# Specific: requirement must contain a concrete action verb
_SPECIFIC_RE = re.compile(
    r"\b(shall|must|will|should|can|allow|enable|provide|display|generate|create|"
    r"update|delete|send|receive|process|store|retrieve|validate|authenticate|"
    r"authorize|notify|calculate|export|import|sync|integrate|support|handle|"
    r"manage|track|monitor|log|report|prevent|restrict|enforce|assign|submit|"
    r"upload|download|search|filter|sort|paginate|render|format|parse|"
    r"schedule|trigger|execute|deploy|configure|audit)\b",
    re.IGNORECASE,
)

# Measurable: numbers with units, comparison phrases
_MEASURABLE_RE = re.compile(
    r"\b\d+(\.\d+)?\s*(%|ms|s|sec|second|minute|min|hour|day|week|month|year|"
    r"k|kb|mb|gb|tb|request|user|transaction|record|call|query|item)\b"
    r"|"
    r"\b(within|less than|more than|at least|at most|up to|maximum|minimum|"
    r"no more than|no less than|not exceed|not less than|greater than|fewer than)\b",
    re.IGNORECASE,
)

# Achievable: flag requirements with impossible/absolute claims
_IMPOSSIBLE_RE = re.compile(
    r"\b(always perfect|never fail|100% uptime|zero downtime|instantaneous response|"
    r"unlimited capacity|infinite scale|no errors ever)\b",
    re.IGNORECASE,
)

# Time-bound: temporal references
_TIME_BOUND_RE = re.compile(
    r"\b(by|before|after|within|during|deadline|schedule|launch|release|go-live|"
    r"sprint|phase|q1|q2|q3|q4|quarter|annually|monthly|weekly|daily|real.?time|"
    r"immediately|end of day|eod|eoq|fiscal|year-end|on demand)\b",
    re.IGNORECASE,
)

# Minimum word count for a requirement to be considered "relevant"
_MIN_RELEVANT_WORDS = 7


def score_requirement_smart(description: str) -> Dict[str, Any]:
    """
    Score a single requirement description against SMART criteria.

    Returns:
        {
            "specific": bool,
            "measurable": bool,
            "achievable": bool,
            "relevant": bool,
            "time_bound": bool,
            "score": float  # 0.0 – 1.0
        }
    """
    desc = description.strip()
    words = desc.split()

    specific   = bool(_SPECIFIC_RE.search(desc)) and len(words) >= 5
    measurable = bool(_MEASURABLE_RE.search(desc))
    achievable = not bool(_IMPOSSIBLE_RE.search(desc))
    relevant   = len(words) >= _MIN_RELEVANT_WORDS
    time_bound = bool(_TIME_BOUND_RE.search(desc))

    # Weighted scoring — Specific and Measurable carry the most weight
    score = (
        (1 if specific   else 0) * 0.30 +
        (1 if measurable else 0) * 0.25 +
        (1 if achievable else 0) * 0.20 +
        (1 if relevant   else 0) * 0.15 +
        (1 if time_bound else 0) * 0.10
    )

    return {
        "specific":   specific,
        "measurable": measurable,
        "achievable": achievable,
        "relevant":   relevant,
        "time_bound": time_bound,
        "score":      round(score, 2),
    }


def evaluate_requirements(requirements: List[Any]) -> Dict[str, Any]:
    """
    Evaluate a full requirements pool and return aggregated SMART quality metrics.

    Accepts a list of Requirement model instances or plain dicts.
    Returns a dict compatible with MetricsCollector.record_requirement_quality().
    """
    if not requirements:
        return {
            "total_evaluated":     0,
            "smart_scores": {
                "avg_score":       0.0,
                "specific_pct":    0.0,
                "measurable_pct":  0.0,
                "achievable_pct":  0.0,
                "relevant_pct":    0.0,
                "time_bound_pct":  0.0,
            },
            "high_quality_count":   0,
            "medium_quality_count": 0,
            "low_quality_count":    0,
        }

    scores_list       = []
    specific_count    = 0
    measurable_count  = 0
    achievable_count  = 0
    relevant_count    = 0
    time_bound_count  = 0

    for req in requirements:
        # Support both Pydantic model instances and plain dicts
        if hasattr(req, "description"):
            desc = req.description
        elif isinstance(req, dict):
            desc = req.get("description", "")
        else:
            desc = str(req)

        result = score_requirement_smart(desc)
        scores_list.append(result["score"])

        if result["specific"]:   specific_count   += 1
        if result["measurable"]: measurable_count += 1
        if result["achievable"]: achievable_count += 1
        if result["relevant"]:   relevant_count   += 1
        if result["time_bound"]: time_bound_count += 1

    total = len(requirements)
    avg   = sum(scores_list) / total

    # Quality tiers: High ≥ 0.70 | Medium 0.40–0.69 | Low < 0.40
    high   = sum(1 for s in scores_list if s >= 0.70)
    medium = sum(1 for s in scores_list if 0.40 <= s < 0.70)
    low    = sum(1 for s in scores_list if s < 0.40)

    return {
        "total_evaluated": total,
        "smart_scores": {
            "avg_score":      round(avg, 3),
            "specific_pct":   round((specific_count   / total) * 100, 1),
            "measurable_pct": round((measurable_count / total) * 100, 1),
            "achievable_pct": round((achievable_count / total) * 100, 1),
            "relevant_pct":   round((relevant_count   / total) * 100, 1),
            "time_bound_pct": round((time_bound_count / total) * 100, 1),
        },
        "high_quality_count":   high,
        "medium_quality_count": medium,
        "low_quality_count":    low,
    }
