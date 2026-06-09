"""
Pydantic data models for BRD Agent health and monitoring metrics.

Covers all 13 KPIs:
  1.  Run success / failure
  2.  Error stage
  3.  Error category
  4.  End-to-end duration
  5.  LLM token usage
  6.  Estimated cost per run
  7.  Section success rate
  8.  Review cycle count
  9.  Requirement Quality Score (SMART)
  10. Section Completeness by Type
  11. Conflict Detection Accuracy
  12. Output file generation success
  13. Acceptance / rework flag
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ── LLM usage ──────────────────────────────────────────────────────────────

class LLMStageUsage(BaseModel):
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMUsageMetrics(BaseModel):
    total_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    by_stage: Dict[str, LLMStageUsage] = Field(default_factory=dict)


# ── Cost ───────────────────────────────────────────────────────────────────

class CostMetrics(BaseModel):
    model_name: str = ""
    prompt_cost_usd: float = 0.0
    completion_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    currency: str = "USD"


# ── Run outcome (KPIs 1, 2, 3) ────────────────────────────────────────────

class RunOutcome(BaseModel):
    # KPI 1 — Run success / failure
    success: bool = False
    # KPI 2 — Error stage: ingestion | extraction | generation | assembly
    error_stage: Optional[str] = None
    # KPI 3 — Error category: api_error | parsing_error | validation_error | timeout | assembly_error | unknown
    error_category: Optional[str] = None
    error_message: Optional[str] = None


# ── Timing (KPI 4) ─────────────────────────────────────────────────────────

class TimingMetrics(BaseModel):
    run_started_at: Optional[str] = None
    run_ended_at: Optional[str] = None
    total_duration_seconds: Optional[float] = None
    extraction_duration_seconds: Optional[float] = None
    generation_duration_seconds: Optional[float] = None
    document_duration_seconds: Optional[float] = None


# ── Sections (KPIs 7, 8) ───────────────────────────────────────────────────

class SectionReviewCycles(BaseModel):
    # KPI 8 — Review cycle count
    total_regenerations: int = 0
    sections_with_rework: List[str] = Field(default_factory=list)
    per_section: Dict[str, Any] = Field(default_factory=dict)


class SectionMetrics(BaseModel):
    # KPI 7 — Section success rate
    attempted: int = 0
    succeeded: int = 0
    failed: int = 0
    success_rate_pct: float = 0.0
    # KPI 8 — Review cycles
    review_cycles: SectionReviewCycles = Field(default_factory=SectionReviewCycles)


# ── Quality (KPIs 9, 10) ───────────────────────────────────────────────────

class SmartScores(BaseModel):
    avg_score: float = 0.0
    specific_pct: float = 0.0
    measurable_pct: float = 0.0
    achievable_pct: float = 0.0
    relevant_pct: float = 0.0
    time_bound_pct: float = 0.0


class RequirementQualityMetrics(BaseModel):
    # KPI 9 — Requirement Quality Score
    total_evaluated: int = 0
    smart_scores: SmartScores = Field(default_factory=SmartScores)
    high_quality_count: int = 0
    medium_quality_count: int = 0
    low_quality_count: int = 0


class SectionCompletenessItem(BaseModel):
    required_items: int = 0
    present_items: int = 0
    completeness_pct: float = 0.0


class SectionCompletenessMetrics(BaseModel):
    # KPI 10 — Section Completeness by Type
    overall_pct: float = 0.0
    by_section: Dict[str, SectionCompletenessItem] = Field(default_factory=dict)


class QualityMetrics(BaseModel):
    requirement_quality: RequirementQualityMetrics = Field(
        default_factory=RequirementQualityMetrics
    )
    section_completeness: SectionCompletenessMetrics = Field(
        default_factory=SectionCompletenessMetrics
    )


# ── Conflicts (KPI 11) ─────────────────────────────────────────────────────

class ConflictMetrics(BaseModel):
    # KPI 11 — Conflict Detection Accuracy
    detected_count: int = 0
    resolved_count: int = 0
    unresolved_count: int = 0
    high_impact_count: int = 0
    medium_impact_count: int = 0
    low_impact_count: int = 0
    resolution_rate_pct: float = 0.0
    # Ground-truth accuracy when a reviewer labels conflicts: valid | false_positive | mixed
    accuracy_feedback: Optional[str] = None


# ── Output (KPI 12) ────────────────────────────────────────────────────────

class OutputMetrics(BaseModel):
    # KPI 12 — Output file generation success
    file_generated: bool = False
    filename: Optional[str] = None
    file_size_bytes: Optional[int] = None
    output_path: Optional[str] = None
    sections_included: int = 0
    word_count_estimate: int = 0


# ── Acceptance (KPI 13) ────────────────────────────────────────────────────

class AcceptanceMetrics(BaseModel):
    # KPI 13 — Acceptance / rework flag
    # pending | accepted_as_is | minor_edits | major_rework
    status: str = "pending"
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None
    notes: Optional[str] = None


# ── Top-level metrics document ────────────────────────────────────────────

class BRDRunMetrics(BaseModel):
    run_id: str
    project_id: str
    project_name: str
    recorded_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )

    # KPIs 1-3
    run_outcome: RunOutcome = Field(default_factory=RunOutcome)
    # KPI 4
    timing: TimingMetrics = Field(default_factory=TimingMetrics)
    # KPIs 5-6
    llm_usage: LLMUsageMetrics = Field(default_factory=LLMUsageMetrics)
    cost: CostMetrics = Field(default_factory=CostMetrics)
    # KPIs 7-8
    sections: SectionMetrics = Field(default_factory=SectionMetrics)
    # KPIs 9-10
    quality: QualityMetrics = Field(default_factory=QualityMetrics)
    # KPI 11
    conflicts: ConflictMetrics = Field(default_factory=ConflictMetrics)
    # KPI 12
    output: OutputMetrics = Field(default_factory=OutputMetrics)
    # KPI 13
    acceptance: AcceptanceMetrics = Field(default_factory=AcceptanceMetrics)
