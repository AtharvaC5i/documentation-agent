"""
Section Prompts — with strict length constraints.
Every prompt includes a word/format limit to keep the BRD to 45-60 pages.
"""

from typing import Tuple, Optional, Dict


def get_section_prompt(
    section_name: str,
    project_name: str,
    client_name: str,
    industry: str,
    description: str,
    requirements_context: str,
    glossary: Dict[str, str],
    feedback: Optional[str] = None
) -> Tuple[str, str]:

    base = f"""Project: {project_name} | Client: {client_name} | Industry: {industry}
Description: {description}

Glossary terms: {_fmt_glossary(glossary)}

Requirements:
{requirements_context}"""

    fb = f"\n\nReviewer feedback to incorporate:\n{feedback}" if feedback else ""
    sl = section_name.lower()

    # ── Executive Summary ──────────────────────────────────────────────────
    if "executive summary" in sl:
        sys = """Senior BA writing Executive Summary for a CEO — non-technical audience.
STRICT LIMIT: 350 words maximum. No padding.
Structure (use these exact headings):
## Executive Summary
### Business Problem (2-3 sentences)
### Proposed Solution (2-3 sentences)
### Key Objectives (3-5 bullet points, each one line)
### Scope Overview (3-4 bullet points)
### Expected Outcomes (2-3 sentences)
Be direct. No filler phrases like "it is important to note that"."""
        usr = f"{base}\n\nWrite the Executive Summary. Max 350 words.{fb}"

    # ── Business Context ───────────────────────────────────────────────────
    elif "business context" in sl:
        sys = """Senior BA writing Business Context section.
STRICT LIMIT: 300 words maximum.
Structure:
## Business Context and Background
### Current State (2-3 sentences — what exists today)
### Business Problem (2-3 sentences — why this project is needed)
### Cost of Inaction (1-2 sentences — what happens if nothing is built)"""
        usr = f"{base}\n\nWrite Business Context. Max 300 words.{fb}"

    # ── Objectives ─────────────────────────────────────────────────────────
    elif "objective" in sl:
        sys = """Senior BA writing Project Objectives section.
STRICT LIMIT: 250 words. Every objective must be measurable (include a number or KPI).
Structure:
## Project Objectives and Success Criteria
### Business Objectives
1. [Objective with measurable KPI]
(5-7 objectives maximum)
### Success Criteria
| Objective | Metric | Target |
(table format — one row per objective)"""
        usr = f"{base}\n\nWrite Objectives and Success Criteria. Max 250 words.{fb}"

    # ── Scope ──────────────────────────────────────────────────────────────
    elif "scope" in sl:
        sys = """Senior BA writing Scope section.
STRICT LIMIT: 300 words.
Structure:
## Scope
### In Scope
- [item] (10-15 bullet points max)
### Out of Scope
- [item] (5-8 items — be explicit, this prevents disputes)
### Future Scope / Phase 2
- [item] (3-5 items)"""
        usr = f"{base}\n\nWrite the Scope section. Max 300 words.{fb}"

    # ── Stakeholders ───────────────────────────────────────────────────────
    elif "stakeholder" in sl:
        sys = """Senior BA writing Stakeholder Register.
STRICT LIMIT: Use a table — no prose descriptions.
Structure:
## Stakeholder Register
| Name | Role | Organisation | Responsibilities | Involvement |
(one row per stakeholder — list every person mentioned in inputs)
Then 2-3 sentences on communication plan."""
        usr = f"{base}\n\nWrite Stakeholder Register as a table.{fb}"

    # ── Functional Requirements ────────────────────────────────────────────
    elif "functional req" in sl:
        sys = """Senior BA writing Functional Requirements section.
CRITICAL FORMAT RULE: Use ONLY tables. No prose per requirement.
Group by module. For each module:
### [Module Name]
| FR-ID | Requirement (The system SHALL...) | Priority | Acceptance Criteria |
Keep each requirement to ONE row, ONE sentence. Do not write paragraphs.
Cover ALL functional requirements from the inputs."""
        usr = f"{base}\n\nWrite Functional Requirements as tables grouped by module. Table format only.{fb}"

    # ── Non-Functional Requirements ────────────────────────────────────────
    elif "non-functional" in sl or "non functional" in sl:
        sys = """Senior BA writing Non-Functional Requirements.
STRICT LIMIT: Bullet points only — no paragraphs.
Structure:
## Non-Functional Requirements
### Performance
- [measurable requirement]
### Security
- [requirement]
### Scalability
- [requirement]
### Availability
- [requirement]
### Compliance
- [requirement]
Each bullet = one specific, measurable NFR. Max 3-4 bullets per category."""
        usr = f"{base}\n\nWrite NFRs as bullet points only. Max 4 bullets per category.{fb}"

    # ── Business Rules ─────────────────────────────────────────────────────
    elif "business rule" in sl:
        sys = """Senior BA writing Business Rules section.
STRICT FORMAT: One-line rule statements only. Use a table.
## Business Rules
| BR-ID | Rule Statement | Module | Priority |
Keep each rule to ONE sentence. No explanatory prose."""
        usr = f"{base}\n\nWrite Business Rules as a table. One sentence per rule.{fb}"

    # ── User Roles ─────────────────────────────────────────────────────────
    elif "user roles" in sl or "roles and permission" in sl:
        sys = """Senior BA writing User Roles and Permissions.
Structure:
## User Roles and Permissions
### Role Definitions (one paragraph per role — 2 sentences max each)
### Permissions Matrix
| Feature | [Role1] | [Role2] | [Role3] | [Role4] |
Use ✓ Allowed / ✗ Denied / Limited
List 15-20 key features in the matrix."""
        usr = f"{base}\n\nWrite User Roles and Permissions with a permissions matrix.{fb}"

    # ── User Journeys ──────────────────────────────────────────────────────
    elif "user journey" in sl or "use case" in sl:
        sys = """Senior BA writing User Journeys.
STRICT LIMIT: 5 journeys maximum. Each journey max 100 words.
Structure per journey:
### UC-00X: [Journey Name]
**Actor**: | **Goal**: | **Steps**: (numbered, max 6 steps) | **Outcome**:
Pick only the 5 most critical user journeys."""
        usr = f"{base}\n\nWrite 5 most critical User Journeys. Max 100 words each.{fb}"

    # ── Data Requirements ──────────────────────────────────────────────────
    elif "data req" in sl:
        sys = """Senior BA writing Data Requirements.
STRICT LIMIT: 250 words. Use tables.
Structure:
## Data Requirements
### Key Data Entities
| Entity | Key Attributes | Estimated Volume |
### Data Migration
2-3 sentences only.
### Data Retention
2-3 sentences only."""
        usr = f"{base}\n\nWrite Data Requirements. Use tables. Max 250 words.{fb}"

    # ── Integration Requirements ───────────────────────────────────────────
    elif "integration" in sl:
        sys = """Senior BA writing Integration Requirements.
STRICT FORMAT: One table per integration system found in requirements.
## Integration Requirements
For each system:
### [System Name]
| Attribute | Detail |
Rows: Type / Direction / Data Exchanged / Frequency / Owner / Fallback / Status
List only systems explicitly mentioned in the inputs."""
        usr = f"{base}\n\nWrite Integration Requirements as attribute tables. One table per system.{fb}"

    # ── Assumptions ───────────────────────────────────────────────────────
    elif "assumption" in sl:
        sys = """Senior BA writing Assumptions section.
STRICT FORMAT: Table only.
## Assumptions
| A-ID | Assumption Statement | Risk if Wrong | Owner |
Keep each assumption to ONE sentence.
List only assumptions explicitly stated or strongly implied in inputs."""
        usr = f"{base}\n\nWrite Assumptions as a table.{fb}"

    # ── Constraints ────────────────────────────────────────────────────────
    elif "constraint" in sl:
        sys = """Senior BA writing Constraints section.
STRICT FORMAT: Table only.
## Constraints
| C-ID | Constraint | Category | Impact |
Category = Technical / Timeline / Budget / Regulatory / Organisational
ONE sentence per constraint."""
        usr = f"{base}\n\nWrite Constraints as a table.{fb}"

    # ── Dependencies ───────────────────────────────────────────────────────
    elif "dependenc" in sl:
        sys = """Senior BA writing Dependencies section.
STRICT FORMAT: Table only.
## Dependencies
| # | Dependency | Owner | Required By | Impact if Delayed |"""
        usr = f"{base}\n\nWrite Dependencies as a table.{fb}"

    # ── Risks ──────────────────────────────────────────────────────────────
    elif "risk" in sl:
        sys = """Senior BA writing Risks section.
STRICT FORMAT: Table only. Max 10 risks.
## Risks
| Risk ID | Risk | Probability | Impact | Level | Mitigation |
Probability / Impact = Low / Medium / High
Level = Low × Low = Low, Medium × High = High, etc."""
        usr = f"{base}\n\nWrite top 10 risks as a table.{fb}"

    # ── Glossary ───────────────────────────────────────────────────────────
    elif "glossary" in sl:
        sys = """Senior BA writing Glossary section.
STRICT FORMAT: Table only. Alphabetical order.
## Glossary
| Term | Definition |
ONE sentence per definition. Include all terms from the project glossary provided."""
        usr = f"{base}\n\nWrite Glossary as an alphabetical table.{fb}"

    # ── Appendices ─────────────────────────────────────────────────────────
    elif "appendix" in sl or "appendices" in sl:
        sys = """Senior BA writing Appendices section.
STRICT LIMIT: 150 words.
## Appendices
### Appendix A: Reference Documents (list only)
### Appendix B: Open Questions and Action Items (bullet list)"""
        usr = f"{base}\n\nWrite Appendices. Max 150 words.{fb}"

    # ── Custom / Generic ───────────────────────────────────────────────────
    else:
        sys = f"""Senior BA writing the '{section_name}' section of a BRD.
STRICT LIMIT: 300 words. Use tables and bullet points where possible.
Start with: ## {section_name}"""
        usr = f"{base}\n\nWrite '{section_name}'. Max 300 words.{fb}"

    return sys, usr


def _fmt_glossary(glossary: Dict[str, str]) -> str:
    if not glossary:
        return "None"
    items = list(glossary.items())[:15]
    return " | ".join(f"{k}: {v[:60]}" for k, v in items)
