"""
Section completeness checker (KPI 10).

For each standard BRD section type, defines the required structural elements
and checks whether they are present in the generated content.

Returns a percentage-based completeness score per section and an overall average.
"""

import re
from typing import List, Dict, Any, Tuple


# ── Required elements per BRD section ────────────────────────────────────
#
# Format: section_name -> List[Tuple[element_label, List[keyword_patterns]]]
# An element is considered PRESENT if any of its keyword patterns match (case-insensitive).

SECTION_REQUIREMENTS: Dict[str, List[Tuple[str, List[str]]]] = {
    "Executive Summary": [
        ("business_problem",   ["problem", "challenge", "opportunity", "objective", "goal", "purpose"]),
        ("solution_overview",  ["solution", "system", "platform", "application", "approach"]),
        ("scope_mention",      ["scope", "included", "excluded", "boundary", "covered"]),
        ("key_stakeholders",   ["stakeholder", "team", "client", "sponsor", "owner", "key"]),
        ("success_criteria",   ["success", "criteria", "outcome", "benefit", "kpi", "metric"]),
    ],
    "Business Context and Background": [
        ("current_state",      ["current", "existing", "today", "as-is", "present", "currently"]),
        ("pain_points",        ["problem", "issue", "challenge", "gap", "limitation", "pain", "bottleneck"]),
        ("business_drivers",   ["driver", "motivation", "reason", "purpose", "trigger", "initiative"]),
        ("market_context",     ["market", "industry", "competitive", "regulatory", "landscape", "environment"]),
    ],
    "Project Objectives and Success Criteria": [
        ("objectives_list",      ["objective", "goal", "aim", "target", "purpose"]),
        ("success_criteria",     ["success", "criteria", "measure", "kpi", "metric", "indicator"]),
        ("measurable_outcomes",  ["increase", "decrease", "reduce", "improve", "achieve", "%", "by ", "from ", "to "]),
    ],
    "Scope": [
        ("in_scope_items",     ["in scope", "included", "within scope", "in-scope", "covered"]),
        ("out_of_scope_items", ["out of scope", "excluded", "not included", "out-of-scope", "outside"]),
        ("deliverables",       ["deliverable", "output", "artifact", "produce", "provide"]),
    ],
    "Stakeholder Register": [
        ("stakeholder_names",  ["name", "role", "title", "position"]),
        ("responsibilities",   ["responsibility", "accountab", "owns", "manages", "responsible", "oversees"]),
        ("department_or_org",  ["department", "team", "contact", "organisation", "org", "division", "group"]),
    ],
    "Functional Requirements": [
        ("shall_statements",         ["shall", "must", "fr-", "the system", "system shall"]),
        ("user_context",             ["user", "actor", "as a", "stakeholder", "role"]),
        ("acceptance_criteria",      ["acceptance", "criteria", "given", "when", "then", "condition"]),
        ("module_or_feature_grouping", ["module", "feature", "component", "section", "subsystem"]),
        ("priority_levels",          ["must have", "should have", "could have", "priority", "high", "medium", "low"]),
    ],
    "Non-Functional Requirements": [
        ("performance",    ["performance", "response time", "latency", "throughput", "speed", "load"]),
        ("security",       ["security", "authentication", "authoriz", "encryption", "access control", "vulnerability"]),
        ("availability",   ["availability", "uptime", "sla", "recovery", "reliability", "fault"]),
        ("scalability",    ["scalab", "concurrent", "capacity", "elastic", "horizontal", "vertical"]),
    ],
    "Business Rules": [
        ("rule_statements", ["rule", "policy", "must", "cannot", "only", "always", "never", "br-"]),
        ("conditions",      ["if", "when", "unless", "except", "provided that", "in case", "subject to"]),
    ],
    "User Roles and Permissions": [
        ("roles_defined",  ["role", "user", "admin", "manager", "operator", "viewer", "editor", "owner"]),
        ("permissions",    ["permission", "access", "can", "cannot", "allowed", "restricted", "denied", "grant"]),
    ],
    "User Journeys and Use Cases": [
        ("use_case_flows", ["step", "flow", "journey", "scenario", "trigger", "sequence", "path"]),
        ("actors",         ["actor", "user", "system", "role", "persona", "participant"]),
        ("conditions",     ["precondition", "postcondition", "assumes", "result", "outcome", "before", "after"]),
    ],
    "Data Requirements": [
        ("data_entities",    ["entity", "object", "record", "data", "field", "attribute", "table"]),
        ("data_validation",  ["validat", "format", "constraint", "rule", "type", "mandatory", "required"]),
        ("storage_or_retention", ["storage", "retain", "archive", "backup", "purge", "lifecycle", "retention"]),
    ],
    "Integration Requirements": [
        ("external_systems", ["api", "integration", "external", "third-party", "system", "service", "endpoint"]),
        ("protocols",        ["rest", "soap", "http", "ftp", "mqtt", "webhook", "grpc", "graphql", "protocol"]),
        ("data_exchange",    ["payload", "request", "response", "format", "json", "xml", "schema", "message"]),
    ],
    "Assumptions": [
        ("assumption_statements", ["assume", "assumed", "assumption", "it is assumed", "we assume", "presume"]),
        ("impact_of_assumption",  ["if this", "should this", "provided that", "based on", "dependent on"]),
    ],
    "Constraints": [
        ("technology_constraints", ["technology", "platform", "framework", "language", "stack", "vendor"]),
        ("budget_or_time_constraints", ["budget", "timeline", "deadline", "cost", "resource", "headcount"]),
        ("regulatory_constraints", ["regulatory", "compliance", "legal", "standard", "gdpr", "hipaa", "sox"]),
    ],
    "Dependencies": [
        ("dependency_list", ["depend", "requires", "prerequisite", "blocked by", "contingent", "relies on"]),
        ("owner_or_team",   ["team", "vendor", "owner", "responsible", "party", "provider"]),
    ],
    "Risks": [
        ("risk_statements",     ["risk", "threat", "vulnerability", "concern", "exposure"]),
        ("probability_impact",  ["probability", "likelihood", "impact", "severity", "high", "medium", "low"]),
        ("mitigation",          ["mitigat", "contingency", "workaround", "plan", "action", "response"]),
    ],
    "Glossary": [
        ("term_definitions",   ["term", "definition", "means", "refers to", ":"]),
        ("acronyms_or_abbrev", [r"\b[A-Z]{2,5}\b"]),
    ],
    "Appendices": [
        ("supporting_content", ["appendix", "diagram", "figure", "table", "reference", "exhibit", "attachment"]),
    ],
}

# Aliases map section name variants (from the generator) to the canonical key above
_SECTION_ALIASES: Dict[str, str] = {
    "business context":                            "Business Context and Background",
    "project objectives":                          "Project Objectives and Success Criteria",
    "objectives and success criteria":             "Project Objectives and Success Criteria",
    "stakeholder register":                        "Stakeholder Register",
    "stakeholders":                                "Stakeholder Register",
    "functional requirements":                     "Functional Requirements",
    "non-functional requirements":                 "Non-Functional Requirements",
    "non functional requirements":                 "Non-Functional Requirements",
    "business rules":                              "Business Rules",
    "user roles and permissions":                  "User Roles and Permissions",
    "user roles":                                  "User Roles and Permissions",
    "user journeys and use cases":                 "User Journeys and Use Cases",
    "user journeys":                               "User Journeys and Use Cases",
    "use cases":                                   "User Journeys and Use Cases",
    "data requirements":                           "Data Requirements",
    "integration requirements":                    "Integration Requirements",
    "integrations":                                "Integration Requirements",
    "risks":                                       "Risks",
    "dependencies":                                "Dependencies",
    "constraints":                                 "Constraints",
    "assumptions":                                 "Assumptions",
    "glossary":                                    "Glossary",
    "appendices":                                  "Appendices",
    "appendix":                                    "Appendices",
}


def _resolve_section_key(section_name: str) -> str:
    """Map a generated section name to the canonical SECTION_REQUIREMENTS key."""
    sl = section_name.strip().lower()

    # Exact match in the canonical dict (case-insensitive)
    for key in SECTION_REQUIREMENTS:
        if key.lower() == sl:
            return key

    # Alias lookup
    for alias, canonical in _SECTION_ALIASES.items():
        if alias in sl:
            return canonical

    # Partial match — return the first canonical key that is a substring
    for key in SECTION_REQUIREMENTS:
        if key.lower() in sl or sl in key.lower():
            return key

    return ""  # Not found


def check_section_completeness(section_name: str, content: str) -> Dict[str, Any]:
    """
    Check how complete a generated section is against its required elements.

    Returns:
        {
            "required_items":   int,
            "present_items":    int,
            "completeness_pct": float
        }
    """
    canonical_key = _resolve_section_key(section_name)
    requirements  = SECTION_REQUIREMENTS.get(canonical_key)

    if not requirements:
        # Unknown section — award full credit if meaningful content exists
        has_content = len(content.strip()) > 100
        return {
            "required_items":   1,
            "present_items":    1 if has_content else 0,
            "completeness_pct": 100.0 if has_content else 0.0,
        }

    content_lower = content.lower()
    present = 0

    for _element_label, patterns in requirements:
        for pattern in patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                present += 1
                break  # Only count the element once

    total = len(requirements)
    pct   = round((present / total) * 100, 1) if total > 0 else 0.0

    return {
        "required_items":   total,
        "present_items":    present,
        "completeness_pct": pct,
    }


def evaluate_all_sections(generated_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate completeness for all generated sections.

    generated_sections: list of section dicts (as stored in project.generated_sections)

    Returns a dict compatible with MetricsCollector.record_section_completeness():
        {
            "overall_pct":  float,
            "by_section":   { section_name: { required_items, present_items, completeness_pct } }
        }
    """
    if not generated_sections:
        return {"overall_pct": 0.0, "by_section": {}}

    by_section: Dict[str, Dict[str, Any]] = {}
    total_pct   = 0.0
    assessed    = 0

    for section in generated_sections:
        name    = section.get("name", "")
        content = section.get("content", "")
        if not name or not content:
            continue

        result             = check_section_completeness(name, content)
        by_section[name]   = result
        total_pct          += result["completeness_pct"]
        assessed           += 1

    overall = round(total_pct / assessed, 1) if assessed > 0 else 0.0

    return {
        "overall_pct": overall,
        "by_section":  by_section,
    }
