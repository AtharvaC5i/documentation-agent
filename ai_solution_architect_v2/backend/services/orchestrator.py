"""
orchestrator.py

3-step pipeline:
  Step 0 — Summarise tech doc (if provided)
  Step 1 — Generate full core architecture JSON (includes components + connections)
  Step 2 — Generate structured diagram JSON from architecture subset
            (consumed by drawioGenerator.js → drawioRenderer.js → PNG in PPTX)
"""

import json
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


class OrchestratorService:
    def __init__(self):
        self.client = DatabricksClient()

    async def run(self, request: GenerateRequest) -> GenerateResponse:

        # ── STEP 0: Summarise tech doc ──────────────────────────
        tech_summary = []
        if request.tech_doc_text and request.tech_doc_text.strip():
            summary_result = await self.client.invoke(
                SUMMARIZE_PROMPT,
                request.tech_doc_text[:8000],
            )
            tech_summary = summary_result.get("summary", [])

        # ── STEP 1: Core architecture ───────────────────────────
        core_input = (
            f"BRD:\n{request.brd_text[:3500]}\n\n"
            f"TECH SUMMARY:\n{json.dumps(tech_summary)}"
        )
        core = await self.client.invoke(CORE_PROMPT, core_input)
        if not isinstance(core, dict):
            raise ValueError(f"Invalid core response type: {type(core)}")

        # ── STEP 2: Structured diagram JSON ────────────────────
        # Pass only the architecture sub-section to keep the prompt focused.
        # The LLM returns { components: [...], connections: [...] } which is
        # merged into architecture and later consumed by drawioGenerator.js.
        arch_subset = {
            "project":           core.get("project", {}),
            "architecture":      core.get("architecture", {}),
            "technology_stack":  core.get("technology_stack", {}),
            "data_flow":         core.get("data_flow", []),
        }
        diagram_json = await self.client.invoke(
            DIAGRAM_PROMPT,
            json.dumps(arch_subset),
        )

        # Store diagram graph under separate keys so we DON'T overwrite the rich
        # component data (name/role/technology) from the core step.
        # generate.py will pass raw_architecture to JS which reads diagram_components/diagram_connections.
        if isinstance(diagram_json, dict):
            arch = core.setdefault("architecture", {})
            
            # If we got diagram components from the LLM, enrich them with technology from core
            if "components" in diagram_json and diagram_json["components"]:
                diagram_comps = diagram_json["components"]
                core_comps = arch.get("components", [])
                
                # Build a map of core components by label for enrichment
                core_by_label = {}
                for cc in core_comps:
                    if isinstance(cc, dict):
                        label = cc.get("label") or cc.get("name", "")
                        if label:
                            core_by_label[label.lower()] = cc
                
                # Enrich diagram components with technology
                for dc in diagram_comps:
                    if isinstance(dc, dict) and "technology" not in dc:
                        label = dc.get("label", "")
                        if label:
                            # Try exact match first, then partial match
                            match = core_by_label.get(label.lower())
                            if match:
                                dc["technology"] = match.get("technology", "")
                
                arch["diagram_components"] = diagram_comps
            
            if "connections" in diagram_json and diagram_json["connections"]:
                arch["diagram_connections"] = diagram_json["connections"]
            
            # Fallback: if core step didn't produce diagram_components, use diagram output
            if not arch.get("diagram_components"):
                arch["diagram_components"] = arch.get("components", [])
            if not arch.get("diagram_connections"):
                arch["diagram_connections"] = arch.get("connections", [])

        return self._parse_response(core)

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