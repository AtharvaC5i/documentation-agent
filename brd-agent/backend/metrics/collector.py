"""
MetricsCollector — thread-safe accumulator for all BRD run metrics.

One instance is created per project run and passed through each pipeline.
Call its methods to record events; call to_dict() to get the final JSON.
"""

import os
import uuid
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

from metrics.models import (
    BRDRunMetrics,
    LLMStageUsage,
    RunOutcome,
    SectionCompletenessItem,
    SectionCompletenessMetrics,
    RequirementQualityMetrics,
    SmartScores,
)
from utils.logger import info

# ── LLaMA 3.3 70B approximate Databricks Foundation Model Serving pricing.
# Override via environment variables if your contract differs.
_PROMPT_COST_PER_TOKEN      = float(os.getenv("LLM_PROMPT_COST_PER_TOKEN",      "0.0000009"))   # $0.90 / 1M
_COMPLETION_COST_PER_TOKEN  = float(os.getenv("LLM_COMPLETION_COST_PER_TOKEN",  "0.0000027"))   # $2.70 / 1M


class MetricsCollector:
    """
    Thread-safe metrics accumulator for one BRD project run.

    Usage:
        collector = MetricsCollector(project_id, project_name)
        collector.start_run()
        ...record events...
        collector.end_run_success()
        metrics_dict = collector.to_dict()
    """

    def __init__(self, project_id: str, project_name: str):
        self._lock = threading.Lock()
        self._metrics = BRDRunMetrics(
            run_id=str(uuid.uuid4()),
            project_id=project_id,
            project_name=project_name,
        )
        self._run_start_ts: Optional[float] = None
        self._phase_starts: Dict[str, float] = {}

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def metrics(self) -> BRDRunMetrics:
        return self._metrics

    @property
    def run_id(self) -> str:
        return self._metrics.run_id

    # ── Run lifecycle (KPIs 1-4) ───────────────────────────────────────────

    def start_run(self):
        """Call at the very beginning of the BRD pipeline."""
        with self._lock:
            now = datetime.now()
            self._run_start_ts = now.timestamp()
            self._metrics.timing.run_started_at = now.isoformat()

    def end_run_success(self):
        """Call when the entire BRD run completes without a fatal error."""
        with self._lock:
            now = datetime.now()
            self._metrics.timing.run_ended_at = now.isoformat()
            if self._run_start_ts:
                self._metrics.timing.total_duration_seconds = round(
                    now.timestamp() - self._run_start_ts, 2
                )
            self._metrics.run_outcome.success = True
            self._metrics.recorded_at = now.isoformat()
            self._calculate_cost()

    def end_run_failure(self, stage: str, category: str, message: str):
        """
        Call when the BRD run fails.

        stage:    ingestion | extraction | generation | assembly
        category: api_error | parsing_error | validation_error | timeout | assembly_error | unknown
        message:  raw error text (truncated to 500 chars)
        """
        _valid_stages = {
            "ingestion", "extraction", "generation", "assembly"
        }
        _valid_categories = {
            "api_error", "parsing_error", "validation_error",
            "timeout", "assembly_error", "unknown",
        }
        with self._lock:
            now = datetime.now()
            self._metrics.timing.run_ended_at = now.isoformat()
            if self._run_start_ts:
                self._metrics.timing.total_duration_seconds = round(
                    now.timestamp() - self._run_start_ts, 2
                )
            self._metrics.run_outcome.success = False
            self._metrics.run_outcome.error_stage = (
                stage if stage in _valid_stages else "unknown"
            )
            self._metrics.run_outcome.error_category = (
                category if category in _valid_categories else "unknown"
            )
            self._metrics.run_outcome.error_message = (
                str(message)[:500] if message else None
            )
            self._metrics.recorded_at = now.isoformat()
            self._calculate_cost()

    # ── Phase timing (KPI 4 breakdown) ────────────────────────────────────

    def start_phase(self, phase: str):
        """phase: 'extraction' | 'generation' | 'document'"""
        with self._lock:
            self._phase_starts[phase] = datetime.now().timestamp()

    def end_phase(self, phase: str):
        with self._lock:
            start = self._phase_starts.get(phase)
            if start is None:
                return
            duration = round(datetime.now().timestamp() - start, 2)
            if phase == "extraction":
                self._metrics.timing.extraction_duration_seconds = duration
            elif phase == "generation":
                self._metrics.timing.generation_duration_seconds = duration
            elif phase == "document":
                self._metrics.timing.document_duration_seconds = duration

    # ── LLM token tracking (KPIs 5-6) ────────────────────────────────────

    def record_llm_call(
        self, stage: str, prompt_tokens: int, completion_tokens: int
    ):
        """
        Record token usage for a single LLM call.

        stage: free-form label, e.g. 'extraction', 'generation', 'conflicts'
        """
        with self._lock:
            total = prompt_tokens + completion_tokens
            u = self._metrics.llm_usage
            u.total_calls += 1
            u.prompt_tokens += prompt_tokens
            u.completion_tokens += completion_tokens
            u.total_tokens += total

            if stage not in u.by_stage:
                u.by_stage[stage] = LLMStageUsage()
            s = u.by_stage[stage]
            s.calls += 1
            s.prompt_tokens += prompt_tokens
            s.completion_tokens += completion_tokens
            s.total_tokens += total

    # ── Section tracking (KPIs 7-8) ───────────────────────────────────────

    def record_section_attempt(
        self, section_name: str, section_id: str, success: bool
    ):
        """Record that a section generation was attempted (and whether it succeeded)."""
        with self._lock:
            self._metrics.sections.attempted += 1
            if success:
                self._metrics.sections.succeeded += 1
            else:
                self._metrics.sections.failed += 1

            # Seed the per-section entry
            if section_id not in self._metrics.sections.review_cycles.per_section:
                self._metrics.sections.review_cycles.per_section[section_id] = {
                    "name": section_name,
                    "cycles": 0,
                }

            # Recalculate success rate
            if self._metrics.sections.attempted > 0:
                self._metrics.sections.success_rate_pct = round(
                    (self._metrics.sections.succeeded / self._metrics.sections.attempted) * 100,
                    1,
                )

    def record_section_regeneration(self, section_name: str, section_id: str):
        """Record one manual regeneration cycle for a section."""
        with self._lock:
            rc = self._metrics.sections.review_cycles
            rc.total_regenerations += 1
            if section_name not in rc.sections_with_rework:
                rc.sections_with_rework.append(section_name)

            if section_id not in rc.per_section:
                rc.per_section[section_id] = {"name": section_name, "cycles": 0}
            rc.per_section[section_id]["cycles"] += 1

    # ── Quality (KPIs 9-10) ────────────────────────────────────────────────

    def record_requirement_quality(self, quality_data: Dict[str, Any]):
        """
        Store SMART-based requirement quality results.
        quality_data must match the shape returned by smart_scorer.evaluate_requirements().
        """
        with self._lock:
            ss = quality_data.get("smart_scores", {})
            self._metrics.quality.requirement_quality = RequirementQualityMetrics(
                total_evaluated=quality_data.get("total_evaluated", 0),
                smart_scores=SmartScores(
                    avg_score=ss.get("avg_score", 0.0),
                    specific_pct=ss.get("specific_pct", 0.0),
                    measurable_pct=ss.get("measurable_pct", 0.0),
                    achievable_pct=ss.get("achievable_pct", 0.0),
                    relevant_pct=ss.get("relevant_pct", 0.0),
                    time_bound_pct=ss.get("time_bound_pct", 0.0),
                ),
                high_quality_count=quality_data.get("high_quality_count", 0),
                medium_quality_count=quality_data.get("medium_quality_count", 0),
                low_quality_count=quality_data.get("low_quality_count", 0),
            )

    def record_section_completeness(self, completeness_data: Dict[str, Any]):
        """
        Store section completeness results.
        completeness_data must match the shape returned by
        section_completeness.evaluate_all_sections().
        """
        with self._lock:
            by_section = {}
            for sec_name, item in completeness_data.get("by_section", {}).items():
                by_section[sec_name] = SectionCompletenessItem(
                    required_items=item.get("required_items", 0),
                    present_items=item.get("present_items", 0),
                    completeness_pct=item.get("completeness_pct", 0.0),
                )
            self._metrics.quality.section_completeness = SectionCompletenessMetrics(
                overall_pct=completeness_data.get("overall_pct", 0.0),
                by_section=by_section,
            )

    # ── Conflict tracking (KPI 11) ─────────────────────────────────────────

    def record_conflicts(self, conflicts: List[Dict[str, Any]]):
        """Snapshot conflict state at the end of extraction."""
        with self._lock:
            c = self._metrics.conflicts
            c.detected_count = len(conflicts)
            c.high_impact_count   = sum(1 for x in conflicts if x.get("impact", "").lower() == "high")
            c.medium_impact_count = sum(1 for x in conflicts if x.get("impact", "").lower() == "medium")
            c.low_impact_count    = sum(1 for x in conflicts if x.get("impact", "").lower() == "low")
            resolved = sum(1 for x in conflicts if x.get("resolved", False))
            c.resolved_count   = resolved
            c.unresolved_count = len(conflicts) - resolved
            if len(conflicts) > 0:
                c.resolution_rate_pct = round(
                    (resolved / len(conflicts)) * 100, 1
                )

    def update_conflict_resolution(self, conflicts: List[Dict[str, Any]]):
        """Re-snapshot conflict state after a reviewer resolves some conflicts."""
        self.record_conflicts(conflicts)

    def set_conflict_accuracy_feedback(self, feedback: str):
        """
        Optionally set reviewer accuracy label.
        feedback: 'valid' | 'false_positive' | 'mixed'
        """
        valid = {"valid", "false_positive", "mixed"}
        with self._lock:
            self._metrics.conflicts.accuracy_feedback = (
                feedback if feedback in valid else None
            )

    # ── Output file tracking (KPI 12) ─────────────────────────────────────

    def record_output_file(
        self,
        success: bool,
        filename: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        sections_included: int = 0,
        word_count_estimate: int = 0,
    ):
        with self._lock:
            o = self._metrics.output
            o.file_generated = success
            if filename:
                o.filename = filename
            if file_path:
                o.output_path = file_path
            if file_size_bytes is not None:
                o.file_size_bytes = file_size_bytes
            o.sections_included = sections_included
            o.word_count_estimate = word_count_estimate

    # ── Acceptance flag (KPI 13) ───────────────────────────────────────────

    def set_acceptance(
        self,
        status: str,
        reviewer: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        """
        status: pending | accepted_as_is | minor_edits | major_rework
        """
        _valid = {"pending", "accepted_as_is", "minor_edits", "major_rework"}
        with self._lock:
            self._metrics.acceptance.status = status if status in _valid else "pending"
            if reviewer:
                self._metrics.acceptance.reviewer = reviewer
            if notes:
                self._metrics.acceptance.notes = notes
            self._metrics.acceptance.reviewed_at = datetime.now().isoformat()

    # ── Cost calculation (KPI 6) ───────────────────────────────────────────

    def _calculate_cost(self):
        """Internal — compute estimated cost from token counts."""
        model_name = os.getenv(
            "DATABRICKS_MODEL_ENDPOINT",
            "databricks-meta-llama-3-3-70b-instruct",
        )
        prompt_cost     = self._metrics.llm_usage.prompt_tokens     * _PROMPT_COST_PER_TOKEN
        completion_cost = self._metrics.llm_usage.completion_tokens * _COMPLETION_COST_PER_TOKEN
        self._metrics.cost.model_name           = model_name
        self._metrics.cost.prompt_cost_usd      = round(prompt_cost,                    6)
        self._metrics.cost.completion_cost_usd  = round(completion_cost,                6)
        self._metrics.cost.total_cost_usd       = round(prompt_cost + completion_cost,  6)

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Return the full metrics payload as a plain dict (JSON-serialisable)."""
        return self._metrics.dict()
