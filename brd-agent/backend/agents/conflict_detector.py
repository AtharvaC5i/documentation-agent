"""
Conflict & Gap Detection Agent
Finds contradictions between requirements and maps coverage against BRD sections.
"""

import uuid
from typing import List, Tuple, Dict, Any

from models.project import Requirement
from utils.databricks_client import call_databricks_llm, parse_llm_json


# All 19 standard BRD sections
ALL_BRD_SECTIONS = [
    "Executive Summary",
    "Business Context and Background",
    "Project Objectives and Success Criteria",
    "Scope",
    "Stakeholder Register",
    "Functional Requirements",
    "Non-Functional Requirements",
    "Business Rules",
    "User Roles and Permissions",
    "User Journeys and Use Cases",
    "Data Requirements",
    "Integration Requirements",
    "Assumptions",
    "Constraints",
    "Dependencies",
    "Risks",
    "Glossary",
    "Appendices",
]


async def detect_conflicts_and_gaps(
    requirements: List[Requirement],
    project_name: str,
    project_description: str
) -> Tuple[List[Dict], List[Dict], Dict[str, str]]:
    """
    Main entry point for conflict and gap detection.

    Returns:
        conflicts: List of detected contradictions
        gaps: List of missing/weak BRD sections
        coverage: Dict mapping section name -> "strong" | "weak" | "none"
    """

    req_summary = _summarize_requirements(requirements)

    conflicts = await _detect_conflicts(requirements, req_summary)
    coverage = await _analyze_coverage(req_summary, project_description)
    gaps = _build_gap_list(coverage)

    return conflicts, gaps, coverage


def _summarize_requirements(requirements: List[Requirement]) -> str:
    """Create a text summary of requirements for LLM input"""
    lines = []
    for r in requirements:
        lines.append(
            f"[{r.req_id}] [{r.type.upper()}] [{r.source}] {r.description}"
        )
    return "\n".join(lines)


async def _detect_conflicts(requirements: List[Requirement], req_summary: str) -> List[Dict]:
    """Detect contradictions between requirements"""

    system_prompt = """You are a requirements analyst specializing in conflict detection.

Find ALL contradictions or inconsistencies in the requirements list.
A conflict is when two requirements say opposite or incompatible things about the same subject.

Examples of conflicts:
- One says "users can delete their own accounts", another says "only admins can delete accounts"
- One says "sync inventory in real time", another says "sync inventory daily"
- One says "vendors control their own pricing", another says "admin controls all pricing"

For each conflict found, return:
{
  "id": "CONF-001",
  "description": "Brief description of the conflict",
  "version_a": {
    "req_id": "TR-005",
    "text": "exact text of first conflicting requirement"
  },
  "version_b": {
    "req_id": "TR-012",
    "text": "exact text of second conflicting requirement"
  },
  "impact": "high|medium|low",
  "resolved": false
}

Return JSON array. Return empty array [] if no conflicts found."""

    user_prompt = f"""Find conflicts in these requirements:

{req_summary[:6000]}"""

    raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=3000, json_mode=True)
    try:
        data = parse_llm_json(raw)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "conflicts" in data:
            return data["conflicts"]
        return []
    except Exception:
        return []


async def _analyze_coverage(req_summary: str, project_description: str) -> Dict[str, str]:
    """Analyze how well requirements cover each BRD section"""

    sections_list = "\n".join([f"- {s}" for s in ALL_BRD_SECTIONS])

    system_prompt = f"""You are a BRD completeness analyst.

For each of the following BRD sections, assess coverage based on the requirements provided:
- "strong": sufficient information exists to write this section
- "weak": some information exists but gaps remain
- "none": no relevant information found

BRD Sections to assess:
{sections_list}

Return JSON object with section name as key and coverage level as value:
{{
  "Executive Summary": "strong",
  "Business Context and Background": "strong",
  ...
}}"""

    user_prompt = f"""Project description: {project_description}

Requirements extracted:
{req_summary[:5000]}

Assess coverage for each BRD section."""

    raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=2000, json_mode=True)
    try:
        coverage = parse_llm_json(raw)
        # Ensure all sections are present
        for section in ALL_BRD_SECTIONS:
            if section not in coverage:
                coverage[section] = "none"
        return coverage
    except Exception:
        # Default all to none if parsing fails
        return {s: "none" for s in ALL_BRD_SECTIONS}


def _build_gap_list(coverage: Dict[str, str]) -> List[Dict]:
    """Build structured gap list from coverage analysis"""
    gaps = []
    for section, level in coverage.items():
        if level in ("weak", "none"):
            gaps.append({
                "id": f"GAP-{str(len(gaps)+1).zfill(3)}",
                "section": section,
                "coverage_level": level,
                "message": (
                    f"'{section}' has insufficient coverage. "
                    f"{'Some data found but gaps remain.' if level == 'weak' else 'No relevant information found in inputs.'}"
                ),
                "suggested_action": (
                    "Fill via follow-up questions to client" if level == "none"
                    else "Review and supplement with client confirmation"
                )
            })
    return gaps
