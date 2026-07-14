"""
orchestrator.py

3-step pipeline:
  Step 0 — Summarise tech doc (if provided)
  Step 1 — Generate full core architecture JSON (includes components + connections)
  Step 2 — Generate structured diagram JSON from architecture subset
            (consumed by drawioGenerator.js → drawioRenderer.js → PNG in PPTX)
"""

import json
import re
from contextlib import nullcontext
from typing import Optional, Any, List, Dict
from models.request_models import GenerateRequest
from models.response_models import (
    GenerateResponse,
    ProjectModel,
    AlignmentModel,
    ProblemStatementModel,
    ProposedSolutionModel,
    ArchitectureModel,
    ComponentModel,
    TechnologyStackModel,
    NonFunctionalModel,
    RoadmapPhaseModel,
    RiskModel,
)
from services.databricks_client import DatabricksClient
from agents.prompt_builder import (
    SUMMARIZE_PROMPT,
    CORE_PROMPT,
    DIAGRAM_PROMPT,
)


def auto_fix_diagram_json(diagram_json: dict) -> dict:
    """
    Validates and auto-fixes the diagram JSON:
    - Removes duplicate components.
    - Validates that all connections link valid component IDs.
    - Removes orphan connections.
    """
    if not isinstance(diagram_json, dict):
        return {"components": [], "connections": []}
        
    components = diagram_json.get("components", [])
    connections = diagram_json.get("connections", [])
    
    fixed_components = []
    seen_ids = set()
    
    # 1. Deduplicate components
    for comp in components:
        if not isinstance(comp, dict) or "id" not in comp:
            continue
        comp_id = comp["id"]
        if comp_id not in seen_ids:
            seen_ids.add(comp_id)
            fixed_components.append(comp)
            
    # 2. Filter connections to only those linking registered component IDs
    fixed_connections = []
    for conn in connections:
        if not isinstance(conn, dict) or "from" not in conn or "to" not in conn:
            continue
        if conn["from"] in seen_ids and conn["to"] in seen_ids:
            fixed_connections.append(conn)
        else:
            print(f"⚠️ [Diagram Auto-Fix] Removing orphan connection: {conn['from']} -> {conn['to']}")
            
    return {
        "components": fixed_components,
        "connections": fixed_connections
    }


class OrchestratorService:
    def __init__(self):
        self.client = DatabricksClient()

    async def run(self, request: GenerateRequest, tracker: Optional[Any] = None) -> GenerateResponse:
        # Track token usage across all LLM calls
        token_usage = {
            "summarization": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "fact_sheet": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "core_generation": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "architecture_review": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "diagram_generation": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

        # ── STEP 0: Summarise tech doc ──────────────────────────
        tech_summary = []
        if request.tech_doc_text and request.tech_doc_text.strip():
            summarize_ctx = tracker.phase("summarization") if tracker else nullcontext()
            with summarize_ctx:
                summary_result = await self.client.invoke(
                    SUMMARIZE_PROMPT,
                    request.tech_doc_text[:8000],
                )
            tech_summary = summary_result.get("summary", [])
            token_usage["summarization"] = self.client.get_last_usage()
            print(f"[Orchestrator] Summarization tokens: {token_usage['summarization']}")

        # ── OPTIMIZATION: Fact-Sheet Context Compression ────────
        # Unified summarization of inputs to prevent token duplication in Stage 1 & 2
        fact_sheet_prompt = """You are a senior systems architect compiling a dense Architectural Fact Sheet from project documents.
Compile:
1. Core Business Goals (exactly 5 specific items)
2. Primary User Personas & Entry Points
3. Identified Pain Points & Constraints (exactly 5 specific items)
4. Key Technology Stack preferences (Frontend, Backend, DB)
5. Critical Security & Performance NFRs

Return ONLY valid JSON with these fields. No explanations."""
        
        input_docs = f"BRD:\n{request.brd_text[:3500]}\n\nTECH SUMMARY:\n{json.dumps(tech_summary)}"
        
        fact_sheet_ctx = tracker.phase("fact_sheet") if tracker else nullcontext()
        with fact_sheet_ctx:
            fact_sheet_json = await self.client.invoke(fact_sheet_prompt, input_docs)
        token_usage["fact_sheet"] = self.client.get_last_usage()
        fact_sheet = json.dumps(fact_sheet_json)
        print(f"[Orchestrator] Fact Sheet generated. Tokens: {token_usage['fact_sheet']}")

        # ── STEP 1: Core architecture ───────────────────────────
        core_input = f"ARCHITECTURAL FACT SHEET:\n{fact_sheet}"
        
        core_ctx = tracker.phase("core_generation") if tracker else nullcontext()
        with core_ctx:
            core = await self.client.invoke(CORE_PROMPT, core_input)
            
        if not isinstance(core, dict):
            raise ValueError(f"Invalid core response type: {type(core)}")
        token_usage["core_generation"] = self.client.get_last_usage()
        print(f"[Orchestrator] Core generation tokens: {token_usage['core_generation']}")

        # ── STEP 1.5: Architect-Reviewer Reflection Loop ────────
        reviewer_system_prompt = """You are an Architecture Review Board critic.
Review the proposed core architecture design JSON.
Check for:
1. Tech conflicts (e.g. backend doesn't support the data-flow requirements).
2. Missing NFR considerations (e.g. scalability requested but single point of failure found).
3. Missing components or goals compared to the fact sheet.

Provide corrective edits in a structured JSON schema:
{
  "gaps_found": true,
  "criticism": "detailed evaluation summary",
  "corrections": {
     "architecture": { ... corrected fields ... },
     "technology_stack": { ... corrected stack layers ... }
  }
}
Return valid JSON only."""
        
        reviewer_user_prompt = f"Fact Sheet:\n{fact_sheet}\n\nDraft Core Design:\n{json.dumps(core)}"
        
        review_ctx = tracker.phase("architecture_review") if tracker else nullcontext()
        with review_ctx:
            try:
                review_res = await self.client.invoke(reviewer_system_prompt, reviewer_user_prompt)
                token_usage["architecture_review"] = self.client.get_last_usage()
                if isinstance(review_res, dict) and review_res.get("gaps_found"):
                    corrections = review_res.get("corrections", {})
                    print(f"[Orchestrator] ARB Critic found gaps: {review_res.get('criticism')}")
                    if "architecture" in corrections and corrections["architecture"]:
                        core.setdefault("architecture", {}).update(corrections["architecture"])
                    if "technology_stack" in corrections and corrections["technology_stack"]:
                        core.setdefault("technology_stack", {}).update(corrections["technology_stack"])
            except Exception as rev_err:
                print(f"[Orchestrator] Warning: ARB Critic loop failed: {rev_err} — continuing")

        # ── STEP 2: Structured diagram JSON ────────────────────
        arch_subset = {
            "project":           core.get("project", {}),
            "architecture":      core.get("architecture", {}),
            "technology_stack":  core.get("technology_stack", {}),
            "data_flow":         core.get("data_flow", []),
        }
        diagram_ctx = tracker.phase("diagram_generation") if tracker else nullcontext()
        with diagram_ctx:
            diagram_json = await self.client.invoke(
                DIAGRAM_PROMPT,
                json.dumps(arch_subset),
            )
        token_usage["diagram_generation"] = self.client.get_last_usage()
        print(f"[Orchestrator] Diagram generation tokens: {token_usage['diagram_generation']}")

        # ── STEP 2.5: Diagram Auto-Fix Loop ─────────────────────
        if isinstance(diagram_json, dict):
            diagram_json = auto_fix_diagram_json(diagram_json)
            arch = core.setdefault("architecture", {})
            
            # If we got diagram components from the LLM, enrich them with technology from core
            if "components" in diagram_json and diagram_json["components"]:
                diagram_comps = diagram_json["components"]
                core_comps = arch.get("components", [])
                
                core_by_label = {}
                for cc in core_comps:
                    if isinstance(cc, dict):
                        label = cc.get("label") or cc.get("name", "")
                        if label:
                            core_by_label[label.lower()] = cc
                
                for dc in diagram_comps:
                    if isinstance(dc, dict) and "technology" not in dc:
                        label = dc.get("label", "")
                        if label:
                            match = core_by_label.get(label.lower())
                            if match:
                                dc["technology"] = match.get("technology", "")
                
                arch["diagram_components"] = diagram_comps
            
            if "connections" in diagram_json and diagram_json["connections"]:
                arch["diagram_connections"] = diagram_json["connections"]
            
            if not arch.get("diagram_components"):
                arch["diagram_components"] = arch.get("components", [])
            if not arch.get("diagram_connections"):
                arch["diagram_connections"] = arch.get("connections", [])

        response = self._parse_response(core)
        response.set_token_usage(token_usage)
        return response

    # ── Response parser ─────────────────────────────────────────
    def _parse_response(self, raw: dict) -> GenerateResponse:

        # project
        p = raw.get("project", {})
        project = ProjectModel(
            name=p.get("name", "Solution Architecture"),
            tagline=p.get("tagline", ""),
            client_context=p.get("client_context", ""),
        )

        # alignment
        a = raw.get("alignment", {})
        alignment = AlignmentModel(
            goals=_safe_list(a.get("goals")),
            business_value=a.get("business_value", ""),
            success_metrics=_safe_list(a.get("success_metrics")),
        )

        # problem statement
        ps = raw.get("problem_statement", {})
        problem_statement = ProblemStatementModel(
            current_pain_points=_safe_list(ps.get("current_pain_points")),
            impact=ps.get("impact", ""),
            root_cause=ps.get("root_cause", ""),
        )

        # proposed solution
        sol = raw.get("proposed_solution", {})
        proposed_solution = ProposedSolutionModel(
            summary=sol.get("summary", ""),
            key_differentiators=_safe_list(sol.get("key_differentiators")),
            approach=sol.get("approach", ""),
        )

        # architecture — preserve components and connections for diagram gen
        arch = raw.get("architecture", {})
        components = [
            ComponentModel(
                name=c.get("name", c.get("label", "")),
                role=c.get("role", ""),
                technology=c.get("technology", ""),
            )
            for c in _safe_list(arch.get("components"))
            if isinstance(c, dict)
        ]
        architecture = ArchitectureModel(
            pattern=arch.get("pattern", ""),
            frontend=arch.get("frontend", ""),
            backend=arch.get("backend", ""),
            ai_layer=arch.get("ai_layer", ""),
            data_store=arch.get("data_store", ""),
            hosting=arch.get("hosting", ""),
            components=components,
        )

        # tech stack
        ts = raw.get("technology_stack", {})
        technology_stack = TechnologyStackModel(
            frontend=_safe_list(ts.get("frontend")),
            backend=_safe_list(ts.get("backend")),
            ai_ml=_safe_list(ts.get("ai_ml")),
            data=_safe_list(ts.get("data")),
            infrastructure=_safe_list(ts.get("infrastructure")),
            security=_safe_list(ts.get("security")),
        )

        # non-functional
        nf = raw.get("non_functional", {})
        non_functional = NonFunctionalModel(
            scalability=nf.get("scalability", ""),
            security=nf.get("security", ""),
            availability=nf.get("availability", ""),
            performance=nf.get("performance", ""),
            compliance=nf.get("compliance", ""),
        )

        # roadmap
        roadmap = []
        for phase in _safe_list(raw.get("roadmap")):
            if isinstance(phase, dict):
                roadmap.append(RoadmapPhaseModel(
                    phase=phase.get("phase", ""),
                    duration=phase.get("duration", ""),
                    deliverables=_safe_list(phase.get("deliverables")),
                ))

        # risks
        risks = []
        for r in _safe_list(raw.get("risks")):
            if isinstance(r, dict):
                risks.append(RiskModel(
                    risk=r.get("risk", ""),
                    mitigation=r.get("mitigation", ""),
                ))
            elif isinstance(r, str):
                risks.append(RiskModel(risk=r, mitigation=""))

        response = GenerateResponse(
            project=project,
            alignment=alignment,
            problem_statement=problem_statement,
            proposed_solution=proposed_solution,
            architecture=architecture,
            data_flow=_safe_list(raw.get("data_flow")),
            technology_stack=technology_stack,
            non_functional=non_functional,
            mermaid_diagram="",
            roadmap=roadmap,
            risks=risks,
            assumptions=_safe_list(raw.get("assumptions")),
            open_questions=_safe_list(raw.get("open_questions")),
        )

        # Store the raw architecture dict (with id/label components + connections)
        # in the private attribute so generate.py can forward it to the JS generator.
        response.set_raw_architecture(raw.get("architecture", {}))

        return response


# ── Helpers ──────────────────────────────────────────────────

def _safe_list(value) -> list:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]