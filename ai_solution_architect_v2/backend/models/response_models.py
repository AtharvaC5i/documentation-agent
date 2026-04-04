from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# ── Sub-models ────────────────────────────────────────────────

class ProjectModel(BaseModel):
    name: str = ""
    tagline: str = ""
    client_context: str = ""


class AlignmentModel(BaseModel):
    goals: List[str] = Field(default_factory=list)
    business_value: str = ""
    success_metrics: List[str] = Field(default_factory=list)


class ProblemStatementModel(BaseModel):
    current_pain_points: List[str] = Field(default_factory=list)
    impact: str = ""
    root_cause: str = ""


class ProposedSolutionModel(BaseModel):
    summary: str = ""
    key_differentiators: List[str] = Field(default_factory=list)
    approach: str = ""


class ComponentModel(BaseModel):
    name: str = ""
    role: str = ""
    technology: str = ""


class ArchitectureModel(BaseModel):
    pattern: str = ""
    frontend: str = ""
    backend: str = ""
    ai_layer: str = ""
    data_store: str = ""
    hosting: str = ""
    components: List[ComponentModel] = Field(default_factory=list)


class TechnologyStackModel(BaseModel):
    frontend: List[str] = Field(default_factory=list)
    backend: List[str] = Field(default_factory=list)
    ai_ml: List[str] = Field(default_factory=list)
    data: List[str] = Field(default_factory=list)
    infrastructure: List[str] = Field(default_factory=list)
    security: List[str] = Field(default_factory=list)


class NonFunctionalModel(BaseModel):
    scalability: str = ""
    security: str = ""
    availability: str = ""
    performance: str = ""
    compliance: str = ""


class RoadmapPhaseModel(BaseModel):
    phase: str = ""
    duration: str = ""
    deliverables: List[str] = Field(default_factory=list)


class RiskModel(BaseModel):
    risk: str = ""
    mitigation: str = ""


# ── Top-level response ────────────────────────────────────────

class GenerateResponse(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    project: ProjectModel = Field(default_factory=ProjectModel)
    alignment: AlignmentModel = Field(default_factory=AlignmentModel)
    problem_statement: ProblemStatementModel = Field(default_factory=ProblemStatementModel)
    proposed_solution: ProposedSolutionModel = Field(default_factory=ProposedSolutionModel)
    architecture: ArchitectureModel = Field(default_factory=ArchitectureModel)
    data_flow: List[Any] = Field(default_factory=list)
    technology_stack: TechnologyStackModel = Field(default_factory=TechnologyStackModel)
    non_functional: NonFunctionalModel = Field(default_factory=NonFunctionalModel)
    mermaid_diagram: str = ""   # retained for schema compatibility; draw.io pipeline used instead
    roadmap: List[RoadmapPhaseModel] = Field(default_factory=list)
    risks: List[RiskModel] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        # Plain Python attribute — invisible to Pydantic serialisation.
        # Holds the raw architecture dict (with id/label components + connections)
        # so generate.py can forward it to the JS generator for draw.io rendering.
        object.__setattr__(self, "_raw_arch", {})

    def set_raw_architecture(self, arch: dict) -> None:
        object.__setattr__(self, "_raw_arch", arch)

    def get_raw_architecture(self) -> dict:
        return object.__getattribute__(self, "_raw_arch")


# ── Request model ─────────────────────────────────────────────

class GenerateRequest(BaseModel):
    brd_text: str = Field(..., description="Business Requirement Document text")
    tech_doc_text: Optional[str] = Field(default="", description="Optional Technical Documentation")