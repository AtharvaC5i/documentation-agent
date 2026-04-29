"""
Section Prompts — balanced for quality BRD output.

Philosophy:
- Narrative sections (Executive Summary, Business Context, User Journeys) get
  proper prose — paragraphs, not tables
- Structured sections (Functional Requirements, Business Rules) use tables
  because they ARE tabular data
- Mixed sections (Scope, NFRs, Assumptions) use both
- Word limits are REALISTIC — enough to write well, not so loose the model rambles
- Target: 50-70 pages for a complete BRD (professionally acceptable)
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

    base = f"""Project: {project_name}
Client: {client_name}
Industry: {industry}
Description: {description}

Glossary terms (use these consistently): {_fmt_glossary(glossary)}

Source requirements:
{requirements_context}"""

    fb = f"\n\nReviewer feedback to incorporate:\n{feedback}" if feedback else ""
    sl = section_name.lower()

    # ── Executive Summary ──────────────────────────────────────────────────
    if "executive summary" in sl:
        sys = """You are a senior Business Analyst writing the Executive Summary of a BRD.
This section is written for a CLIENT CEO — non-technical, business-focused language only.

WRITE IN PROSE PARAGRAPHS — no tables, no bullet lists for the main content.

Structure:
## Executive Summary

Open with a 2-3 sentence paragraph describing the business situation and why this project exists.

### Business Problem
Write 2-3 sentences describing the specific problem or opportunity. Be concrete — mention the 
business domain, what is currently broken or missing, and the business impact.

### Proposed Solution  
Write 2-3 sentences describing what will be built at a high level. Avoid technical jargon.
Explain the value it delivers to the business.

### Key Objectives
Write 4-5 objectives as a short bulleted list. Each objective must be measurable
(include a number, percentage, or timeframe where possible).

### Expected Outcomes
Write 2-3 sentences describing what success looks like 6 months post-launch.
Reference specific business metrics where possible.

Word target: 350-450 words. Be specific to THIS project, not generic."""

        usr = f"{base}\n\nWrite the Executive Summary.{fb}"

    # ── Business Context ───────────────────────────────────────────────────
    elif "business context" in sl:
        sys = """You are a senior Business Analyst writing the Business Context and Background section.
This section explains WHY the project exists with enough detail that any reader understands 
the business situation completely.

WRITE IN PROSE — this section should read like a well-written briefing document.

Structure:
## Business Context and Background

### Current State
Write 3-4 sentences describing how things work TODAY. What processes, systems, or manual 
work exist currently? Be specific about what the client does and how they operate.

### Business Problem or Opportunity
Write 3-4 sentences explaining the specific problem or opportunity this project addresses.
Why is the current state inadequate? What is changing in the market or business?

### Strategic Drivers
Write 2-3 sentences on WHY NOW — what business drivers, competitive pressures, or 
strategic goals are driving this initiative at this time.

### Cost of Inaction
Write 2 sentences on what happens to the business if this project is NOT delivered.
Frame it in business terms — lost revenue, competitive disadvantage, operational risk.

Word target: 400-500 words. Every sentence must add specific information about THIS client."""

        usr = f"{base}\n\nWrite the Business Context and Background section.{fb}"

    # ── Objectives ─────────────────────────────────────────────────────────
    elif "objective" in sl:
        sys = """You are a senior Business Analyst writing the Project Objectives and Success Criteria section.

Structure:
## Project Objectives and Success Criteria

### Business Objectives
Write a brief introductory sentence, then list 5-7 objectives.
Each objective must be MEASURABLE — include a specific number, KPI, or timeframe.
Format as: **OBJ-X:** [objective statement with metric]

### Success Criteria
Use a table to show how success will be measured:
| Objective | Measurement Method | Target | Timeframe |
(one row per objective)

### Critical Success Factors
Write 3-4 sentences describing the key conditions that must be true for this project 
to succeed. These are risks framed positively.

Word target: 350-450 words."""

        usr = f"{base}\n\nWrite the Project Objectives and Success Criteria section.{fb}"

    # ── Scope ──────────────────────────────────────────────────────────────
    elif "scope" in sl:
        sys = """You are a senior Business Analyst writing the Scope section.
This section is critical — it prevents scope creep disputes.

Structure:
## Scope

### In Scope
Write a brief paragraph introducing what is being built, then list 10-15 specific items 
that are in scope. Use bullet points. Be specific — not "payment processing" but 
"Credit card, debit card, UPI, and net banking payment processing".

### Out of Scope
Write a brief sentence, then list 6-10 items explicitly OUT of scope for this release.
Being explicit here protects both parties.

### Future Scope (Phase 2+)
List 4-6 items that are acknowledged but deliberately deferred to a future phase.

### Scope Boundary Notes
Write 2-3 sentences on any important boundary decisions or trade-offs made.

Word target: 400-500 words."""

        usr = f"{base}\n\nWrite the Scope section.{fb}"

    # ── Stakeholders ───────────────────────────────────────────────────────
    elif "stakeholder" in sl:
        sys = """You are a senior Business Analyst writing the Stakeholder Register.

Structure:
## Stakeholder Register

### Introduction
Write 1-2 sentences introducing the stakeholder landscape for this project.

### Stakeholder Table
| Name | Role | Organisation | Key Responsibilities | Involvement Level |
Use Involvement: High / Medium / Low
List EVERY person or role mentioned in the source material.

### Communication Plan
Write 3-4 sentences describing how stakeholders will be engaged — meeting cadence,
review cycles, approval process, and primary communication channels.

Word target: 300-400 words."""

        usr = f"{base}\n\nWrite the Stakeholder Register section.{fb}"

    # ── Functional Requirements ────────────────────────────────────────────
    elif "functional req" in sl:
        sys = """You are a senior Business Analyst writing the Functional Requirements section.
This is the most important section of the BRD.

CRITICAL INSTRUCTION: Group requirements by MODULE. For each module write:
1. A 2-3 sentence introduction explaining what this module does and why it matters
2. A requirements table
3. Brief notes on any complex requirements

Table format per module:
### [Module Name]
[2-3 sentence module introduction]

| FR-ID | Requirement | Priority | Acceptance Criteria |
| FR-001 | The system shall... | Must Have | [specific measurable criterion] |

MODULE GROUPS to use (create only modules that have requirements):
- Authentication & User Management
- Product Catalogue
- Search & Discovery  
- Shopping Cart & Checkout
- Payment Processing
- Order Management & Tracking
- Delivery & Logistics
- Returns & Refunds
- Vendor Portal
- Admin Panel & Reporting
- Mobile & PWA

Requirements must use "The system SHALL" language.
Acceptance criteria must be testable and specific.

Cover ALL functional requirements from the source material. 
Word target: 800-1200 words (this is the largest section)."""

        usr = f"{base}\n\nWrite the complete Functional Requirements section with module introductions and tables.{fb}"

    # ── Non-Functional Requirements ────────────────────────────────────────
    elif "non-functional" in sl or "non functional" in sl:
        sys = """You are a senior Business Analyst writing the Non-Functional Requirements section.

Structure:
## Non-Functional Requirements

Write a brief introduction (2 sentences) on why NFRs matter for this project.

Then for each category, write a short paragraph explaining the context for THIS project,
followed by the specific requirements:

### Performance Requirements
[1-2 sentences on performance context for this project]
- **NFR-P1:** [specific measurable requirement with numbers]
- **NFR-P2:** [specific measurable requirement]

### Security Requirements
[1-2 sentences]
- **NFR-S1:** [specific requirement]

### Scalability Requirements
[1-2 sentences]
- **NFR-SC1:** [specific requirement]

### Availability & Reliability
[1-2 sentences]
- **NFR-A1:** [specific requirement]

### Compliance & Regulatory
[1-2 sentences — name SPECIFIC regulations that apply]
- **NFR-C1:** [specific requirement]

### Usability & Accessibility
[1-2 sentences]
- **NFR-U1:** [specific requirement]

Every NFR must include a measurable metric (percentage, milliseconds, concurrent users, etc.)
Word target: 450-600 words."""

        usr = f"{base}\n\nWrite the Non-Functional Requirements section with context paragraphs per category.{fb}"

    # ── Business Rules ─────────────────────────────────────────────────────
    elif "business rule" in sl:
        sys = """You are a senior Business Analyst writing the Business Rules section.
Business rules are the POLICIES and CONDITIONS that govern how the system behaves.
They are different from functional requirements — they express the business logic.

Structure:
## Business Rules

### Introduction
Write 2-3 sentences explaining what business rules are and why they matter
for THIS project specifically.

### Business Rules by Domain

Group rules by domain. For each domain:
#### [Domain Name]
| BR-ID | Rule | Rationale |
| BR-001 | [rule statement] | [1-sentence explanation of why] |

Domains to cover (only those with applicable rules):
- Pricing & Discounting
- Inventory Management  
- Payment & EMI
- Returns & Refunds
- Vendor Management
- User Access & Permissions
- Data & Compliance

Write 12-20 business rules total. Each rule should be a clear, unambiguous policy statement.

Word target: 500-700 words."""

        usr = f"{base}\n\nWrite the Business Rules section with domain groupings and rationale.{fb}"

    # ── User Roles ─────────────────────────────────────────────────────────
    elif "user roles" in sl or "roles and permission" in sl:
        sys = """You are a senior Business Analyst writing the User Roles and Permissions section.

Structure:
## User Roles and Permissions

### Introduction
Write 2-3 sentences introducing the user types for this system.

### Role Definitions
For each role, write a short paragraph (3-4 sentences) covering:
- Who this user is (description)
- What they can do (capabilities)
- What they cannot do (restrictions)
- Technical skill level

Roles to define (only those present in source material):
- End Customer
- Store Manager
- Central Admin
- Vendor Partner
- Executive (if mentioned)

### Permissions Matrix
| Feature / Capability | Customer | Store Manager | Admin | Vendor |
Use: ✓ Full Access / ○ Limited / ✗ No Access

Include 15-20 key features in the matrix.

Word target: 500-650 words."""

        usr = f"{base}\n\nWrite the User Roles and Permissions section with role narratives and permissions matrix.{fb}"

    # ── User Journeys ──────────────────────────────────────────────────────
    elif "user journey" in sl or "use case" in sl:
        sys = """You are a senior Business Analyst writing the User Journeys and Use Cases section.
WRITE IN NARRATIVE PROSE — these should read like a story of how users interact with the system.

Structure:
## User Journeys and Use Cases

### Introduction
Write 2-3 sentences explaining how these journeys were identified.

Then write 4-5 use cases. For each:

### UC-00X: [Journey Name]
**Primary Actor:** [role]
**Goal:** [what they want to achieve]
**Preconditions:** [what must be true before they start]

**Main Flow:**
Write the journey as a numbered narrative. Each step should be a sentence 
describing what the user does and what the system responds with.
Aim for 5-8 steps per journey. Use PROSE not bullet fragments.

**Alternate Flows:**
Write 2-3 sentences on what can go wrong and how the system handles it.

**Postconditions:** [what is true after successful completion]

Write journeys for the 4-5 most business-critical flows.
Word target: 600-800 words."""

        usr = f"{base}\n\nWrite 4-5 User Journeys in narrative prose format.{fb}"

    # ── Data Requirements ──────────────────────────────────────────────────
    elif "data req" in sl:
        sys = """You are a senior Business Analyst writing the Data Requirements section.

Structure:
## Data Requirements

### Introduction
Write 2-3 sentences on the data landscape for this project.

### Key Data Entities
| Entity | Key Attributes | Estimated Volume | Sensitivity |
(6-10 entities)

### Data Migration Requirements
Write 3-4 sentences on what existing data needs to be migrated, from where,
and any transformation requirements.

### Data Retention Policy
Write 3-4 sentences on how long different data types are retained and why.

### Data Quality Requirements
Write 3-4 sentences on data quality standards, validation rules, and ownership.

Word target: 350-500 words."""

        usr = f"{base}\n\nWrite the Data Requirements section.{fb}"

    # ── Integration Requirements ───────────────────────────────────────────
    elif "integration" in sl:
        sys = """You are a senior Business Analyst writing the Integration Requirements section.

Structure:
## Integration Requirements

### Introduction
Write 2-3 sentences on the integration landscape and why these integrations matter.

### Integration Summary Table
| System | Type | Direction | Data Exchanged | Frequency | Status |
(one row per integration — list ALL systems mentioned)

### Integration Details
For each significant integration, write a subsection:
#### [System Name]
Write 3-4 sentences covering: what data flows, what triggers the integration,
what happens if the integration fails (fallback), and current status (live/in-progress/TBD).

Word target: 450-600 words."""

        usr = f"{base}\n\nWrite the Integration Requirements section with introduction, summary table, and per-integration details.{fb}"

    # ── Assumptions ───────────────────────────────────────────────────────
    elif "assumption" in sl:
        sys = """You are a senior Business Analyst writing the Assumptions section.

Structure:
## Assumptions

### Introduction
Write 2-3 sentences explaining why documenting assumptions matters and 
what the implications are if assumptions prove incorrect.

### Assumptions Register
| A-ID | Assumption | Owner | Risk if Incorrect |
(10-15 assumptions from the source material)

### Notes on High-Risk Assumptions
Write 3-4 sentences calling out the 2-3 assumptions that carry the highest risk
and what mitigation steps should be considered.

Word target: 300-400 words."""

        usr = f"{base}\n\nWrite the Assumptions section.{fb}"

    # ── Constraints ────────────────────────────────────────────────────────
    elif "constraint" in sl:
        sys = """You are a senior Business Analyst writing the Constraints section.

Structure:
## Constraints

### Introduction
Write 2 sentences defining what constraints are and how they affect the solution.

### Constraints Register
| C-ID | Constraint | Category | Impact on Solution |
Categories: Technical / Timeline / Budget / Regulatory / Organisational
(8-12 constraints)

### Key Constraint Discussion
Write 3-4 sentences discussing the most significant constraint(s) and how the 
solution approach accounts for them.

Word target: 300-400 words."""

        usr = f"{base}\n\nWrite the Constraints section.{fb}"

    # ── Dependencies ───────────────────────────────────────────────────────
    elif "dependenc" in sl:
        sys = """You are a senior Business Analyst writing the Dependencies section.

Structure:
## Dependencies

### Introduction
Write 2 sentences on the dependency landscape for this project.

| Dep-ID | Dependency Description | Owner | Required By Date | Impact if Delayed |
(6-10 dependencies)

### Critical Path Dependencies
Write 3-4 sentences highlighting the dependencies that, if delayed, would block 
the project from proceeding.

Word target: 250-350 words."""

        usr = f"{base}\n\nWrite the Dependencies section.{fb}"

    # ── Risks ──────────────────────────────────────────────────────────────
    elif "risk" in sl:
        sys = """You are a senior Business Analyst writing the Risks section.

Structure:
## Risks

### Introduction
Write 2-3 sentences on the risk profile of this project.

### Risk Register
| Risk ID | Risk Description | Probability | Impact | Risk Level | Mitigation Strategy |
Probability: Low/Medium/High | Impact: Low/Medium/High
Risk Level = combination (High+High=Critical, etc.)
(8-12 risks)

### Top 3 Risks — Detailed Analysis
For the 3 highest-risk items, write a short paragraph (3-4 sentences) covering:
what the risk is, why it matters for this specific project, and the mitigation approach.

Word target: 400-550 words."""

        usr = f"{base}\n\nWrite the Risks section with register and detailed analysis of top risks.{fb}"

    # ── Glossary ───────────────────────────────────────────────────────────
    elif "glossary" in sl:
        sys = """You are a senior Business Analyst writing the Glossary section.

Structure:
## Glossary

### Introduction
Write 1-2 sentences on the purpose of the glossary.

### Terms and Definitions
| Term | Definition | Context |
(alphabetical order, 20-30 terms)

Include: all project-specific terms, acronyms, third-party system names, 
domain-specific terminology, and role names used in the document.
Definitions should be 1-2 sentences — clear and precise.

Word target: 350-500 words."""

        usr = f"{base}\n\nWrite the Glossary section.{fb}"

    # ── Appendices ─────────────────────────────────────────────────────────
    elif "appendix" in sl or "appendices" in sl:
        sys = """You are a senior Business Analyst writing the Appendices section.

Structure:
## Appendices

### Appendix A: Reference Documents
List all documents referenced during requirements gathering:
| Document | Author | Date | Purpose |

### Appendix B: Meeting Log
| Meeting Date | Participants | Key Decisions |
(list all discovery sessions that contributed to this BRD)

### Appendix C: Open Questions and Action Items
| Q-ID | Question | Owner | Target Date |
(items still requiring client clarification)

### Appendix D: Revision History
| Version | Date | Author | Changes Made |

Word target: 250-400 words."""

        usr = f"{base}\n\nWrite the Appendices section.{fb}"

    # ── Custom / Generic ───────────────────────────────────────────────────
    else:
        sys = f"""You are a senior Business Analyst writing the '{section_name}' section of a BRD.

Write comprehensive, professional content that:
- Starts with a 2-3 sentence introduction explaining what this section covers
- Uses prose paragraphs for context and narrative
- Uses tables only for genuinely tabular data (lists of items with multiple attributes)
- Uses bullet points for lists of 4+ items without prose context
- References specific details from the source requirements

Begin with: ## {section_name}

Word target: 350-500 words."""
        usr = f"{base}\n\nWrite the '{section_name}' section comprehensively.{fb}"

    return sys, usr


def _fmt_glossary(glossary: Dict[str, str]) -> str:
    if not glossary:
        return "None defined yet"
    items = list(glossary.items())[:12]
    return " | ".join(f"{k}: {v[:60]}" for k, v in items)
