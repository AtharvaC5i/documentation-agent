"""
Section Suggester — now pure rules-based Python.
No LLM call. Coverage analysis already done in extraction pipeline.
"""

from typing import List, Dict, Any


ALL_BRD_SECTIONS = [
    {"id": "executive_summary",    "name": "Executive Summary",                  "description": "High-level project overview for non-technical stakeholders"},
    {"id": "business_context",     "name": "Business Context and Background",    "description": "Current state, problem statement, and business drivers"},
    {"id": "objectives",           "name": "Project Objectives and Success Criteria", "description": "Measurable goals and how success is defined"},
    {"id": "scope",                "name": "Scope",                              "description": "In-scope, out-of-scope, and future scope items"},
    {"id": "stakeholders",         "name": "Stakeholder Register",               "description": "All parties with a stake in the project"},
    {"id": "functional_req",       "name": "Functional Requirements",            "description": "What the system must do — full requirements list"},
    {"id": "non_functional_req",   "name": "Non-Functional Requirements",        "description": "Performance, security, scalability, compliance"},
    {"id": "business_rules",       "name": "Business Rules",                     "description": "Policies and logic governing system behavior"},
    {"id": "user_roles",           "name": "User Roles and Permissions",         "description": "All user types and their access levels"},
    {"id": "user_journeys",        "name": "User Journeys and Use Cases",        "description": "Narrative walkthroughs of key workflows"},
    {"id": "data_requirements",    "name": "Data Requirements",                  "description": "Data entities, volumes, migration needs"},
    {"id": "integrations",         "name": "Integration Requirements",           "description": "External systems and APIs to connect with"},
    {"id": "assumptions",          "name": "Assumptions",                        "description": "Unconfirmed beliefs the project is based on"},
    {"id": "constraints",          "name": "Constraints",                        "description": "Hard limits on technology, budget, timeline"},
    {"id": "dependencies",         "name": "Dependencies",                       "description": "External deliverables the project depends on"},
    {"id": "risks",                "name": "Risks",                              "description": "Known risks and mitigation strategies"},
    {"id": "glossary",             "name": "Glossary",                           "description": "Project-specific terminology definitions"},
    {"id": "appendices",           "name": "Appendices",                         "description": "Supporting materials and references"},
]

# Sections that are ALWAYS included regardless of coverage
ALWAYS_INCLUDE = {
    "executive_summary", "scope", "functional_req",
    "stakeholders", "glossary"
}

# Rules: include if coverage is not "none" OR if contextual signal present
CONTEXT_SIGNALS = {
    "integrations":      ["api", "integration", "sap", "salesforce", "crm", "erp", "payment", "gateway"],
    "non_functional_req": ["performance", "security", "scalability", "compliance", "gdpr", "uptime", "load"],
    "data_requirements": ["migration", "data", "database", "sku", "product catalog"],
    "business_rules":    ["rule", "cannot", "only", "must not", "policy", "discount", "approval"],
    "risks":             ["risk", "concern", "problem", "challenge", "dependency"],
    "dependencies":      ["depends", "waiting", "before", "prerequisite", "vendor"],
}


def suggest_sections_from_coverage_rules(
    coverage: Dict[str, str],
    project_description: str,
    industry: str
) -> List[Dict[str, Any]]:
    """
    Pure Python rule-based section suggestion. Zero LLM calls.
    Rules:
    1. Always include the 5 core sections
    2. Include if coverage is "strong" or "weak"
    3. Include if project description contains context signals
    4. Exclude if coverage is "none" AND no context signals
    """
    desc_lower = (project_description + " " + industry).lower()
    result = []

    for section in ALL_BRD_SECTIONS:
        sid = section["id"]
        sname = section["name"]
        cov = coverage.get(sname, "none")

        # Rule 1: always include core sections
        if sid in ALWAYS_INCLUDE:
            result.append({
                **section,
                "suggested": True,
                "reason": "Always required for client-facing BRDs",
                "coverage": cov,
            })
            continue

        # Rule 2: include if has coverage
        if cov in ("strong", "weak"):
            result.append({
                **section,
                "suggested": True,
                "reason": f"Coverage found in inputs ({cov})",
                "coverage": cov,
            })
            continue

        # Rule 3: include if context signals present in description
        signals = CONTEXT_SIGNALS.get(sid, [])
        if signals and any(s in desc_lower for s in signals):
            result.append({
                **section,
                "suggested": True,
                "reason": "Inferred from project context — no input coverage yet",
                "coverage": cov,
            })
            continue

        # Rule 4: exclude
        result.append({
            **section,
            "suggested": False,
            "reason": "No coverage found and not inferred from context",
            "coverage": cov,
        })

    return result


# Keep old async function signature for any remaining callers
async def suggest_sections_from_coverage(
    coverage: Dict[str, str],
    project_description: str,
    industry: str
) -> List[Dict[str, Any]]:
    return suggest_sections_from_coverage_rules(coverage, project_description, industry)
