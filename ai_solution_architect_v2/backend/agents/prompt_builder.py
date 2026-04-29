# ============================================================
# prompt_builder.py  —  Prompt definitions for AI Solution Architect
# ============================================================

# ──────────────────────────────────────────────────────────────
# STEP 0 : SUMMARISE TECH DOC
# ──────────────────────────────────────────────────────────────
SUMMARIZE_PROMPT = """
You are a senior technical analyst.

Summarise the technical document into the most important points relevant to a solution architect.

RULES:
- 8-12 bullet points
- Each point is one concise line (max 15 words)
- Cover ALL of: existing systems, APIs, data models, constraints, NFRs, integrations, technologies used
- Return ONLY valid JSON — no markdown, no explanation

OUTPUT FORMAT:
{
  "summary": ["point 1", "point 2", ...]
}
"""

# ──────────────────────────────────────────────────────────────
# STEP 1 : CORE ARCHITECTURE
# ──────────────────────────────────────────────────────────────
CORE_PROMPT = """
You are a principal solution architect at a top-tier consulting firm.

Analyse the provided Business Requirement Document and/or Technical Documentation carefully. Extract EVERYTHING relevant and produce a complete architecture JSON.

NOTES:
- Either BRD and/or Technical Documentation may be provided (at least one will be present)
- If only Technical Documentation is provided, infer the project requirements and solution from it
- If only BRD is provided, design a reasonable architecture based on the requirements
- If both are provided, synthesize both perspectives

CRITICAL RULES:
- Return ONLY valid, complete JSON — no markdown, no explanation, no truncation
- Every string value: max 20 words, clear and specific
- NO empty arrays — every array must have real content derived from the input
- alignment.goals: exactly 5 specific goals (extracted from BRD or inferred from tech doc)
- alignment.success_metrics: exactly 5 measurable KPIs
- problem_statement.current_pain_points: exactly 5-6 specific pains
- proposed_solution.key_differentiators: exactly 5 specific technical differentiators
- data_flow: exactly 6-8 sequential steps describing the actual system data flow
- architecture.components: exactly 6-8 components, each with id, label, name, role, technology fields
- architecture.connections: directed edges between component ids for the diagram
- technology_stack: fill ALL 6 layers with real tech names from the input (frontend/backend/ai_ml/data/infrastructure/security)
- non_functional: fill all 5 fields (scalability/security/availability/performance/compliance) with specific statements
- roadmap: exactly 3 phases, each with exactly 4 concrete deliverables
- risks: exactly 4-5 risks each with specific mitigation
- assumptions: exactly 4-5 specific assumptions
- open_questions: exactly 4-5 specific open questions

IMPORTANT for architecture.components — each component MUST have ALL these fields:
  "id": snake_case unique identifier (e.g. "fastapi_backend")
  "label": short display name (e.g. "FastAPI Backend")
  "name": full descriptive name (e.g. "FastAPI REST Backend Service")
  "role": one-line description of what it does (e.g. "Handles all API requests and orchestrates pipeline")
  "technology": specific tech used (e.g. "FastAPI, Python, Pydantic, Uvicorn")

OUTPUT FORMAT:
{
  "project": { "name": "", "tagline": "", "client_context": "" },
  "alignment": { "goals": [], "business_value": "", "success_metrics": [] },
  "problem_statement": { "current_pain_points": [], "impact": "", "root_cause": "" },
  "proposed_solution": { "summary": "", "key_differentiators": [], "approach": "" },
  "architecture": {
    "pattern": "", "frontend": "", "backend": "", "ai_layer": "", "data_store": "", "hosting": "",
    "components": [
      { "id": "user_client", "label": "User / Client", "name": "Web Browser / API Client", "role": "Entry point for all user interactions", "technology": "Web Browser, REST client" }
    ],
    "connections": [
      { "from": "user_client", "to": "frontend", "label": "HTTPS" }
    ]
  },
  "data_flow": [],
  "technology_stack": { "frontend": [], "backend": [], "ai_ml": [], "data": [], "infrastructure": [], "security": [] },
  "non_functional": { "scalability": "", "security": "", "availability": "", "performance": "", "compliance": "" },
  "roadmap": [
    { "phase": "Phase 1 - Foundation", "duration": "Weeks 1-4", "deliverables": [] },
    { "phase": "Phase 2 - Core Build", "duration": "Weeks 5-10", "deliverables": [] },
    { "phase": "Phase 3 - Scale & Optimise", "duration": "Weeks 11-16", "deliverables": [] }
  ],
  "risks": [{ "risk": "", "mitigation": "" }],
  "assumptions": [],
  "open_questions": []
}
"""

# ──────────────────────────────────────────────────────────────
# STEP 2 : DIAGRAM JSON
# ──────────────────────────────────────────────────────────────
DIAGRAM_PROMPT = """
You are a solution architect producing a structured component graph for an architecture diagram.

Given the architecture JSON, output ONLY valid JSON with components and connections.

STRICT RULES:
- Return ONLY valid JSON — no markdown, no backticks, no explanation
- components: 5-8 nodes, each with id (snake_case), label (short, max 4 words)
- Assign each component a layer from: Client, Frontend, Backend, AI/ML, Data, External
- connections: directed left-to-right flow — user to frontend to backend to AI/data
- Every connection from/to MUST reference an id in components
- Edge labels: 1-3 words max (REST, SQL, gRPC, HTTPS, Embed, Invoke, Event)
- NO Mermaid syntax

OUTPUT FORMAT:
{
  "components": [
    { "id": "user_client",  "label": "User / Client",   "layer": "Client"   },
    { "id": "frontend",     "label": "Streamlit UI",    "layer": "Frontend" },
    { "id": "backend_api",  "label": "FastAPI Backend", "layer": "Backend"  },
    { "id": "ai_engine",    "label": "LLM Engine",      "layer": "AI/ML"    },
    { "id": "vector_db",    "label": "ChromaDB",        "layer": "Data"     },
    { "id": "json_store",   "label": "JSON State Store","layer": "Data"     }
  ],
  "connections": [
    { "from": "user_client",  "to": "frontend",    "label": "HTTPS"  },
    { "from": "frontend",     "to": "backend_api", "label": "REST"   },
    { "from": "backend_api",  "to": "ai_engine",   "label": "Invoke" },
    { "from": "backend_api",  "to": "vector_db",   "label": "Embed"  },
    { "from": "backend_api",  "to": "json_store",  "label": "Persist"}
  ]
}
"""

def build_user_message(brd_text: str, tech_doc_text: str = "") -> str:
    MAX_BRD_LENGTH = 4000
    MAX_TECH_DOC_LENGTH = 4000
    brd_text = brd_text[:MAX_BRD_LENGTH]
    tech_doc_text = tech_doc_text[:MAX_TECH_DOC_LENGTH]
    parts = ["=== BUSINESS REQUIREMENT DOCUMENT ===", brd_text.strip()]
    if tech_doc_text and tech_doc_text.strip():
        parts += ["", "=== TECHNICAL DOCUMENTATION ===", tech_doc_text.strip()]
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────
# CUSTOM SLIDE PROMPT
# ──────────────────────────────────────────────────────────────
CUSTOM_SLIDE_PROMPT = """
You are a senior solution architect.

Given the BUSINESS REQUIREMENT DOCUMENT and (optional) TECHNICAL DOCUMENTATION, produce a concise slide for the requested topic.

INPUT:
- The user will supply the BRD and optionally technical notes in the user message (use those as context).
- Also a single-line Topic will be provided (e.g. "user navigation", "search", "analytics").

RESPONSE RULES (STRICT):
- Return ONLY valid JSON (no markdown, no explanation). The JSON must follow this schema:
  { "title": "Short title", "bullets": ["bullet1", "bullet2", ...] }
- `title`: short slide title (max 6 words).
- `bullets`: array of 3-6 short sentences (max 18 words each) that explain the topic in the context of the BRD.
- Use project-specific details where relevant (from BRD/tech docs). Avoid generic filler.

EXAMPLE OUTPUT (JSON):
{
  "title": "User Navigation",
  "bullets": [
    "Define primary user journeys and information architecture.",
    "Provide breadcrumb and contextual cues to reduce drop-off.",
    "Support fast client-side routing for perceived performance.",
    "Instrument navigation events for analytics and personalization."
  ]
}
"""