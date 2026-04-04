"""
Section Prompts — strict length constraints.
Target: entire BRD 35-50 pages. Max 2 pages per section.
Tables must fit within page width. No sprawling prose.
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

Glossary: {_fmt_glossary(glossary)}

Requirements:
{requirements_context}"""

    fb = f"\n\nReviewer feedback:\n{feedback}" if feedback else ""
    sl = section_name.lower()

    # ── Executive Summary ──────────────────────────────────────────────────
    if "executive summary" in sl:
        sys = """Senior BA writing Executive Summary. NON-TECHNICAL audience.
HARD LIMIT: 300 words. No exceptions. No filler.
FORMAT:
## Executive Summary
### Business Problem (2 sentences max)
### Proposed Solution (2 sentences max)
### Key Objectives (3-4 bullets, one line each)
### Expected Outcomes (2 sentences)
Write tight. Every word must earn its place."""
        usr = f"{base}\n\nExecutive Summary — 300 words MAXIMUM.{fb}"

    # ── Business Context ───────────────────────────────────────────────────
    elif "business context" in sl:
        sys = """Senior BA writing Business Context.
HARD LIMIT: 200 words.
FORMAT:
## Business Context
### Current State (1-2 sentences)
### Problem (2-3 sentences)
### Impact if Unresolved (1 sentence)"""
        usr = f"{base}\n\nBusiness Context — 200 words MAXIMUM.{fb}"

    # ── Objectives ─────────────────────────────────────────────────────────
    elif "objective" in sl:
        sys = """Senior BA writing Objectives. ALL must be measurable with numbers.
HARD LIMIT: 200 words.
FORMAT:
## Project Objectives
| # | Objective | Metric | Target |
(max 6 rows)
Then 2 sentence closing on timeline."""
        usr = f"{base}\n\nObjectives table — 200 words MAXIMUM.{fb}"

    # ── Scope ──────────────────────────────────────────────────────────────
    elif "scope" in sl:
        sys = """Senior BA writing Scope. Explicit and complete.
HARD LIMIT: 250 words.
FORMAT:
## Scope
### In Scope
- bullet (8-12 items max)
### Out of Scope
- bullet (5-8 items — be explicit)
### Future Phases
- bullet (3-5 items)"""
        usr = f"{base}\n\nScope section — 250 words MAXIMUM.{fb}"

    # ── Stakeholders ───────────────────────────────────────────────────────
    elif "stakeholder" in sl:
        sys = """Senior BA writing Stakeholder Register.
TABLE ONLY — no prose. Fit in one page.
FORMAT:
## Stakeholder Register
| Name | Role | Organisation | Key Responsibility | Availability |
(max 10 rows)"""
        usr = f"{base}\n\nStakeholder Register as table only.{fb}"

    # ── Functional Requirements ────────────────────────────────────────────
    elif "functional req" in sl:
        sys = """Senior BA writing Functional Requirements.
CRITICAL: TABLE FORMAT ONLY. No prose descriptions per requirement.
GROUP by module. Each module gets one table.
TABLE FORMAT per module:
### [Module Name]
| FR-ID | Requirement (SHALL statement, max 15 words) | Priority | Key AC |
Keep AC column to ONE criterion max per row. If more needed, list as FR-XXX-a, FR-XXX-b.
Max 8 columns total width — keep columns narrow.
Cover ALL functional requirements but keep each row concise."""
        usr = f"{base}\n\nFunctional Requirements — tables by module only. Keep rows concise.{fb}"

    # ── Non-Functional Requirements ────────────────────────────────────────
    elif "non-functional" in sl or "non functional" in sl:
        sys = """Senior BA writing NFRs.
TABLE FORMAT. One table covering all categories.
FORMAT:
## Non-Functional Requirements
| Category | Requirement | Metric |
Categories: Performance, Security, Scalability, Availability, Compliance, Usability
Max 2 rows per category. Keep metric column measurable and brief."""
        usr = f"{base}\n\nNFRs as single table. Max 2 rows per category.{fb}"

    # ── Business Rules ─────────────────────────────────────────────────────
    elif "business rule" in sl:
        sys = """Senior BA writing Business Rules.
TABLE FORMAT ONLY.
FORMAT:
## Business Rules
| BR-ID | Rule (max 20 words) | Module | Priority |
Max 15 rules. One sentence each."""
        usr = f"{base}\n\nBusiness Rules as table. Max 15 rows.{fb}"

    # ── User Roles ─────────────────────────────────────────────────────────
    elif "user roles" in sl or "roles and permission" in sl:
        sys = """Senior BA writing User Roles & Permissions.
FORMAT:
## User Roles and Permissions
### Role Definitions
One line per role: **Role Name** — description (max 15 words)
### Permissions Matrix
| Feature | [Role1] | [Role2] | [Role3] |
Use ✓ / ✗ / Limited. Max 15 features, max 5 roles."""
        usr = f"{base}\n\nUser Roles with compact permissions matrix.{fb}"

    # ── User Journeys ──────────────────────────────────────────────────────
    elif "user journey" in sl or "use case" in sl:
        sys = """Senior BA writing User Journeys.
HARD LIMIT: 3 journeys only. Each max 80 words.
FORMAT per journey:
### UC-00X: [Name]
**Actor** | **Goal** | **Steps** (max 5, numbered) | **Result**
Pick only the 3 most business-critical flows."""
        usr = f"{base}\n\n3 most critical User Journeys — 80 words each max.{fb}"

    # ── Data Requirements ──────────────────────────────────────────────────
    elif "data req" in sl:
        sys = """Senior BA writing Data Requirements.
HARD LIMIT: 200 words. Tables only.
FORMAT:
## Data Requirements
| Entity | Key Attributes | Est. Volume | Sensitivity |
(max 8 entities)
Then 1 sentence on migration if applicable."""
        usr = f"{base}\n\nData Requirements table — 200 words max.{fb}"

    # ── Integration Requirements ───────────────────────────────────────────
    elif "integration" in sl:
        sys = """Senior BA writing Integration Requirements.
ONE compact table listing all integrations.
FORMAT:
## Integration Requirements
| System | Type | Direction | Data | Frequency | Status |
Then if a system needs detail, add ONE brief note line under the table.
Max 10 integration rows."""
        usr = f"{base}\n\nIntegrations as one compact table.{fb}"

    # ── Assumptions ───────────────────────────────────────────────────────
    elif "assumption" in sl:
        sys = """Senior BA writing Assumptions.
TABLE FORMAT ONLY.
FORMAT:
## Assumptions
| A-ID | Assumption (max 20 words) | Risk if Wrong |
Max 10 assumptions."""
        usr = f"{base}\n\nAssumptions as table. Max 10 rows.{fb}"

    # ── Constraints ────────────────────────────────────────────────────────
    elif "constraint" in sl:
        sys = """Senior BA writing Constraints.
TABLE FORMAT ONLY.
FORMAT:
## Constraints
| C-ID | Constraint (max 20 words) | Category | Impact |
Max 10 constraints. Categories: Technical / Timeline / Budget / Regulatory."""
        usr = f"{base}\n\nConstraints as table. Max 10 rows.{fb}"

    # ── Dependencies ───────────────────────────────────────────────────────
    elif "dependenc" in sl:
        sys = """Senior BA writing Dependencies.
TABLE FORMAT ONLY.
FORMAT:
## Dependencies
| # | Dependency | Owner | Needed By | Impact if Delayed |
Max 8 rows."""
        usr = f"{base}\n\nDependencies as table. Max 8 rows.{fb}"

    # ── Risks ──────────────────────────────────────────────────────────────
    elif "risk" in sl:
        sys = """Senior BA writing Risks.
TABLE FORMAT ONLY. Max 8 risks.
FORMAT:
## Risks
| Risk ID | Risk (max 15 words) | Probability | Impact | Level | Mitigation (max 10 words) |"""
        usr = f"{base}\n\nTop 8 risks as table only.{fb}"

    # ── Glossary ───────────────────────────────────────────────────────────
    elif "glossary" in sl:
        sys = """Senior BA writing Glossary.
TABLE FORMAT. Alphabetical. One line definitions.
FORMAT:
## Glossary
| Term | Definition (max 15 words) |"""
        usr = f"{base}\n\nGlossary as alphabetical table. One-line definitions.{fb}"

    # ── Appendices ─────────────────────────────────────────────────────────
    elif "appendix" in sl or "appendices" in sl:
        sys = """Senior BA writing Appendices.
HARD LIMIT: 100 words.
FORMAT:
## Appendices
### Reference Documents (list only — no descriptions)
### Open Questions (bullet list — max 5 items)"""
        usr = f"{base}\n\nAppendices — 100 words max.{fb}"

    # ── Custom ─────────────────────────────────────────────────────────────
    else:
        sys = f"""Senior BA writing '{section_name}' section.
HARD LIMIT: 200 words. Use tables and bullets where possible.
Start with: ## {section_name}"""
        usr = f"{base}\n\n'{section_name}' section — 200 words MAXIMUM.{fb}"

    return sys, usr


def _fmt_glossary(glossary: Dict[str, str]) -> str:
    if not glossary:
        return "None"
    items = list(glossary.items())[:10]
    return " | ".join(f"{k}: {v[:50]}" for k, v in items)
