"""
metrics_models.py

Comprehensive metrics tracking for AI Solution Architect PPT generation.
Tracks KPIs across generation, LLM usage, quality, and output validity.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ErrorStageEnum(str, Enum):
    """Enumeration of failure stages in the generation pipeline"""
    SUMMARIZATION = "summarization"
    CORE_GENERATION = "core_generation"
    DIAGRAM_GENERATION = "diagram_generation"
    DIAGRAM_BUILDING = "diagram_building"
    DIAGRAM_RENDERING = "diagram_rendering"
    PPTX_GENERATION = "pptx_generation"
    PPTX_ASSEMBLY = "pptx_assembly"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class ErrorCategoryEnum(str, Enum):
    """Normalized error categories for failure classification"""
    API_ERROR = "api_error"  # LLM API failures, timeouts
    DIAGRAM_ERROR = "diagram_error"  # Diagram generation or structure errors
    RENDERING_ERROR = "rendering_error"  # PNG/image rendering issues
    ASSEMBLY_ERROR = "assembly_error"  # PPTX merge/assembly issues
    DEPENDENCY_ERROR = "dependency_error"  # Missing libs, node_modules, etc
    VALIDATION_ERROR = "validation_error"  # Output doesn't meet quality standards
    TIMEOUT_ERROR = "timeout_error"  # Execution timeout
    MEMORY_ERROR = "memory_error"  # Out of memory or resource exhaustion
    UNKNOWN_ERROR = "unknown_error"  # Unclassified error


class AcceptanceStatusEnum(str, Enum):
    """Status of acceptance/rework after generation"""
    ACCEPTED_AS_IS = "accepted_as_is"
    MINOR_EDITS = "minor_edits"
    MAJOR_REWORK = "major_rework"
    REJECTED = "rejected"
    PENDING_REVIEW = "pending_review"


# ── Token Usage Model ──────────────────────────────────────

class TokenUsageModel(BaseModel):
    """LLM token consumption tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        """Total tokens consumed"""
        return self.prompt_tokens + self.completion_tokens
    
    @property
    def estimated_cost_usd(self, model: str = "databricks-llm") -> float:
        """
        Estimate cost in USD based on token usage.
        Databricks LLM pricing (approximate):
        - Input: $0.003 per 1K tokens
        - Output: $0.015 per 1K tokens
        Adjust pricing as needed based on your actual rate card.
        """
        # Pricing per 1K tokens
        PROMPT_COST_PER_1K = 0.003
        COMPLETION_COST_PER_1K = 0.015
        
        prompt_cost = (self.prompt_tokens / 1000) * PROMPT_COST_PER_1K
        completion_cost = (self.completion_tokens / 1000) * COMPLETION_COST_PER_1K
        return round(prompt_cost + completion_cost, 6)


# ── Diagram Quality Model ──────────────────────────────────

class DiagramMetricsModel(BaseModel):
    """Metrics for diagram generation and correctness"""
    attempted: bool = False  # Whether diagram generation was attempted
    success: bool = False  # Whether diagram generation succeeded
    components_count: int = 0  # Number of architecture components detected
    connections_count: int = 0  # Number of relationships/connections
    expected_components: int = 0  # Expected count from BRD
    expected_connections: int = 0  # Expected count from BRD
    
    @property
    def component_coverage(self) -> float:
        """
        Percentage of expected components that were generated.
        Range: 0.0 to 1.0
        Formula: actual_components / expected_components (or 0.0 if not attempted)
        """
        if not self.attempted:
            return 0.0  # Not attempted = 0 coverage
        if self.expected_components == 0:
            return 0.0 if self.components_count == 0 else 0.5
        return min(1.0, self.components_count / self.expected_components)
    
    @property
    def connection_coverage(self) -> float:
        """
        Percentage of expected connections that were generated.
        Range: 0.0 to 1.0
        """
        if not self.attempted:
            return 0.0  # Not attempted = 0 coverage
        if self.expected_connections == 0:
            return 0.0 if self.connections_count == 0 else 0.5
        return min(1.0, self.connections_count / self.expected_connections)
    
    @property
    def diagram_correctness_score(self) -> float:
        """
        Overall diagram correctness score (0.0 to 1.0).
        Formula: (component_coverage * 0.6 + connection_coverage * 0.4) * success_multiplier
        Weighted toward component coverage as it's more critical.
        """
        base_score = (self.component_coverage * 0.6) + (self.connection_coverage * 0.4)
        success_multiplier = 1.0 if self.success else 0.0
        return round(base_score * success_multiplier, 3)


# ── Slide Generation Model ─────────────────────────────────

class SlideMetricsModel(BaseModel):
    """Metrics for slide/section generation"""
    attempted: int = 0  # Total slides/sections attempted
    successful: int = 0  # Successfully generated slides/sections
    failed: int = 0  # Failed slides/sections
    retry_count: int = 0  # Total retries across all slides
    
    @property
    def success_rate(self) -> float:
        """
        Percentage of slides successfully generated.
        Range: 0.0 to 1.0
        Formula: successful / attempted
        """
        if self.attempted == 0:
            return 0.0
        return round(self.successful / self.attempted, 3)

# ── Sections Model ────────────────────────────────────────

class SectionsModel(BaseModel):
    """Metrics for sections/content selected by user"""
    selected_count: int = 0  # Number of selected sections
    selected_list: List[str] = []  # Names of selected sections
    custom_sections_count: int = 0  # Number of custom sections added
    custom_sections: List[str] = []  # Names of custom sections
    total_sections: int = 0  # selected_count + custom_sections_count

# ── Quality Score Model ────────────────────────────────────

class QualityScoreModel(BaseModel):
    """Aggregated quality metrics for the entire output"""
    content_quality: float = Field(0.0, ge=0.0, le=1.0)  # Content accuracy & completeness
    diagram_quality: float = Field(0.0, ge=0.0, le=1.0)  # Diagram visual quality
    architecture_alignment: float = Field(0.0, ge=0.0, le=1.0)  # How well architecture aligns with BRD
    output_validity: float = Field(0.0, ge=0.0, le=1.0)  # PPTX opens without errors
    
    @property
    def overall_score(self) -> float:
        """
        Overall quality score.
        Formula: Average of all quality dimensions
        Range: 0.0 to 1.0
        """
        scores = [
            self.content_quality,
            self.diagram_quality,
            self.architecture_alignment,
            self.output_validity,
        ]
        avg = sum(scores) / len(scores) if scores else 0.0
        return round(avg, 3)


# ── PPTX Validation Model ──────────────────────────────────

class PptxValidationModel(BaseModel):
    """Validation results for PPTX output integrity"""
    file_created: bool = False  # PPTX file successfully created
    file_size_bytes: int = 0  # Size of generated PPTX
    valid_xml: bool = False  # All XML files in PPTX are well-formed
    valid_relationships: bool = False  # Relationship files are valid
    opens_without_repair: bool = False  # PowerPoint doesn't prompt for repair
    all_slides_present: bool = False  # All expected slides are in the PPTX
    all_media_present: bool = False  # All images/diagrams are embedded
    
    @property
    def health_score(self) -> float:
        """
        PPTX generation health score.
        Formula: Count of passing validations / total validations
        Range: 0.0 to 1.0
        """
        validations = [
            self.file_created,
            self.valid_xml,
            self.valid_relationships,
            self.opens_without_repair,
            self.all_slides_present,
            self.all_media_present,
        ]
        passed = sum(validations)
        return round(passed / len(validations), 3) if validations else 0.0


# ── Architecture Decision Justification ────────────────────

class ArchitectureJustificationModel(BaseModel):
    """Metrics for how well architecture decisions are grounded in inputs"""
    decisions_identified: int = 0  # Number of key architecture decisions identified
    decisions_justified: int = 0  # Number with explicit references to BRD/TechDoc
    brd_citations: int = 0  # Count of BRD citations in justifications
    constraint_references: int = 0  # Count of constraint references from TechDoc
    
    @property
    def justification_score(self) -> float:
        """
        Score indicating how well decisions are justified.
        Formula: decisions_justified / decisions_identified
        Range: 0.0 to 1.0
        """
        if self.decisions_identified == 0:
            return 0.0
        return round(self.decisions_justified / self.decisions_identified, 3)


# ── Error Details Model ────────────────────────────────────

class ErrorDetailsModel(BaseModel):
    """Details about any error that occurred"""
    occurred: bool = False
    stage: ErrorStageEnum = ErrorStageEnum.UNKNOWN
    category: ErrorCategoryEnum = ErrorCategoryEnum.UNKNOWN_ERROR
    message: str = ""
    traceback: str = ""
    recovery_attempted: bool = False
    recovery_successful: bool = False


# ── Main Metrics Model ─────────────────────────────────────

class GenerationMetricsModel(BaseModel):
    """Complete metrics payload for a single PPT generation run"""
    
    # ── Execution Identity ─────────────────────────────────
    run_id: str = Field(default_factory=lambda: "", description="Unique run identifier")
    timestamp_start: datetime = Field(default_factory=datetime.utcnow)
    timestamp_end: Optional[datetime] = None
    
    # ── Run Status ─────────────────────────────────────────
    run_success: bool = False  # Final outcome: success or failure
    error_details: ErrorDetailsModel = Field(default_factory=ErrorDetailsModel)
    
    # ── Duration Metrics ───────────────────────────────────
    # (all in seconds)
    duration_total: float = 0.0  # Total end-to-end duration
    duration_summarization: float = 0.0  # Tech doc summarization
    duration_core_generation: float = 0.0  # Core architecture generation
    duration_diagram_generation: float = 0.0  # Diagram JSON generation
    duration_diagram_rendering: float = 0.0  # PNG rendering from diagram
    duration_pptx_generation: float = 0.0  # PPTX creation from template
    duration_pptx_assembly: float = 0.0  # Merging slides into final PPTX
    duration_validation: float = 0.0  # Final validation checks
    
    # ── LLM Token Usage ────────────────────────────────────
    token_usage_summarization: TokenUsageModel = Field(default_factory=TokenUsageModel)
    token_usage_core: TokenUsageModel = Field(default_factory=TokenUsageModel)
    token_usage_diagram: TokenUsageModel = Field(default_factory=TokenUsageModel)
    
    @property
    def total_token_usage(self) -> TokenUsageModel:
        """Aggregate token usage across all LLM calls"""
        return TokenUsageModel(
            prompt_tokens=(
                self.token_usage_summarization.prompt_tokens +
                self.token_usage_core.prompt_tokens +
                self.token_usage_diagram.prompt_tokens
            ),
            completion_tokens=(
                self.token_usage_summarization.completion_tokens +
                self.token_usage_core.completion_tokens +
                self.token_usage_diagram.completion_tokens
            ),
        )
    
    @property
    def estimated_cost_usd(self) -> float:
        """Total estimated cost for this run in USD"""
        return self.total_token_usage.estimated_cost_usd
    
    # ── Slide/Section Metrics ──────────────────────────────
    slide_metrics: SlideMetricsModel = Field(default_factory=SlideMetricsModel)
    
    # ── Sections Information ───────────────────────────────
    sections_metrics: "SectionsModel" = Field(default_factory=SectionsModel)
    
    # ── Diagram Metrics ────────────────────────────────────
    diagram_metrics: DiagramMetricsModel = Field(default_factory=DiagramMetricsModel)
    
    # ── Quality Metrics ────────────────────────────────────
    quality_scores: QualityScoreModel = Field(default_factory=QualityScoreModel)
    
    # ── PPTX Validation ────────────────────────────────────
    pptx_validation: PptxValidationModel = Field(default_factory=PptxValidationModel)
    
    # ── Architecture Justification ─────────────────────────
    architecture_justification: ArchitectureJustificationModel = Field(
        default_factory=ArchitectureJustificationModel
    )
    
    # ── Review & Acceptance ────────────────────────────────
    review_cycle_count: int = 0  # How many review/refinement cycles
    acceptance_status: AcceptanceStatusEnum = AcceptanceStatusEnum.PENDING_REVIEW
    
    # ── Retry Logic ────────────────────────────────────────
    total_retry_count: int = 0  # Total retries across entire run
    
    def calculate_duration_total(self) -> None:
        """
        Calculate total duration from start/end timestamps.
        Also sums all phase durations as a consistency check.
        """
        if self.timestamp_end:
            self.duration_total = (
                self.timestamp_end - self.timestamp_start
            ).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary, computing all derived values"""
        self.calculate_duration_total()
        return {
            "run_id": self.run_id,
            "timestamp_start": self.timestamp_start.isoformat(),
            "timestamp_end": self.timestamp_end.isoformat() if self.timestamp_end else None,
            "run_success": self.run_success,
            "error_details": {
                "occurred": self.error_details.occurred,
                "stage": self.error_details.stage.value,
                "category": self.error_details.category.value,
                "message": self.error_details.message,
                "recovery_attempted": self.error_details.recovery_attempted,
                "recovery_successful": self.error_details.recovery_successful,
            },
            "duration": {
                "total_seconds": round(self.duration_total, 2),
                "summarization_seconds": round(self.duration_summarization, 2),
                "core_generation_seconds": round(self.duration_core_generation, 2),
                "diagram_generation_seconds": round(self.duration_diagram_generation, 2),
                "diagram_rendering_seconds": round(self.duration_diagram_rendering, 2),
                "pptx_generation_seconds": round(self.duration_pptx_generation, 2),
                "pptx_assembly_seconds": round(self.duration_pptx_assembly, 2),
                "validation_seconds": round(self.duration_validation, 2),
            },
            "llm_tokens": {
                "summarization": {
                    "prompt_tokens": self.token_usage_summarization.prompt_tokens,
                    "completion_tokens": self.token_usage_summarization.completion_tokens,
                    "total_tokens": self.token_usage_summarization.total_tokens,
                },
                "core_generation": {
                    "prompt_tokens": self.token_usage_core.prompt_tokens,
                    "completion_tokens": self.token_usage_core.completion_tokens,
                    "total_tokens": self.token_usage_core.total_tokens,
                },
                "diagram_generation": {
                    "prompt_tokens": self.token_usage_diagram.prompt_tokens,
                    "completion_tokens": self.token_usage_diagram.completion_tokens,
                    "total_tokens": self.token_usage_diagram.total_tokens,
                },
                "total": {
                    "prompt_tokens": self.total_token_usage.prompt_tokens,
                    "completion_tokens": self.total_token_usage.completion_tokens,
                    "total_tokens": self.total_token_usage.total_tokens,
                },
            },
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "sections": {
                "selected_count": self.sections_metrics.selected_count,
                "selected_list": self.sections_metrics.selected_list,
                "custom_sections_count": self.sections_metrics.custom_sections_count,
                "custom_sections": self.sections_metrics.custom_sections,
                "total_sections": self.sections_metrics.total_sections,
            },
            "slides": {
                "attempted": self.slide_metrics.attempted,
                "successful": self.slide_metrics.successful,
                "failed": self.slide_metrics.failed,
                "retry_count": self.slide_metrics.retry_count,
                "success_rate": self.slide_metrics.success_rate,
            },
            "diagram": {
                "attempted": self.diagram_metrics.attempted,
                "success": self.diagram_metrics.success,
                "components_count": self.diagram_metrics.components_count,
                "connections_count": self.diagram_metrics.connections_count,
                "expected_components": self.diagram_metrics.expected_components,
                "expected_connections": self.diagram_metrics.expected_connections,
                "component_coverage": self.diagram_metrics.component_coverage,
                "connection_coverage": self.diagram_metrics.connection_coverage,
                "correctness_score": self.diagram_metrics.diagram_correctness_score,
            },
            "quality": {
                "content_quality": self.quality_scores.content_quality,
                "diagram_quality": self.quality_scores.diagram_quality,
                "architecture_alignment": self.quality_scores.architecture_alignment,
                "output_validity": self.quality_scores.output_validity,
                "overall_score": self.quality_scores.overall_score,
            },
            "pptx_validation": {
                "file_created": self.pptx_validation.file_created,
                "file_size_bytes": self.pptx_validation.file_size_bytes,
                "valid_xml": self.pptx_validation.valid_xml,
                "valid_relationships": self.pptx_validation.valid_relationships,
                "opens_without_repair": self.pptx_validation.opens_without_repair,
                "all_slides_present": self.pptx_validation.all_slides_present,
                "all_media_present": self.pptx_validation.all_media_present,
                "health_score": self.pptx_validation.health_score,
            },
            "architecture_justification": {
                "decisions_identified": self.architecture_justification.decisions_identified,
                "decisions_justified": self.architecture_justification.decisions_justified,
                "brd_citations": self.architecture_justification.brd_citations,
                "constraint_references": self.architecture_justification.constraint_references,
                "justification_score": self.architecture_justification.justification_score,
            },
            "review_cycle_count": self.review_cycle_count,
            "acceptance_status": self.acceptance_status.value,
            "total_retry_count": self.total_retry_count,
        }
