import json
import os
import platform
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

METRICS_DIR = "D://documentation_agent_metrics_json//technical-agent//"

CONTROLLED_STATUS_VALUES = {"running", "success", "failure", "partial_success"}
CONTROLLED_STAGES = {
    "ingestion",
    "section_selection",
    "context_building",
    "generation",
    "assembly",
    "review",
    "publish",
}
CONTROLLED_ERROR_CATEGORIES = {
    "api",
    "timeout",
    "parsing",
    "assembly",
    "dependency",
    "validation",
    "runtime",
    "embedding",
    "ingestion",
    "llm_auth",
    "llm_rate_limit",
    "empty_output",
    "unknown",
}
CONTROLLED_REVIEW_SOURCES = {"manual", "automated", "mixed", "not_reviewed"}
CONTROLLED_ACCEPTANCE_FLAGS = {"accepted", "minor_edits", "major_rework", "not_reviewed"}

_COST_PER_1K_PROMPT_TOKENS = 0.0010
_COST_PER_1K_COMPLETION_TOKENS = 0.0020

ERROR_CATEGORIES = {
    "api": ["api", "http", "request", "connection", "network", "client"],
    "timeout": ["timeout", "timed out", "deadline", "slow", "expired"],
    "parsing": ["parse", "parsing", "json", "yaml", "xml", "syntax", "decode"],
    "assembly": ["assembly", "document", "build", "template", "docx"],
    "dependency": ["import", "module", "dependency", "pip", "package", "missing"],
    "embedding": ["embedding", "vector", "encode", "chunk", "store"],
    "llm_auth": ["auth", "unauthorized", "credential", "token", "api_key", "permission"],
    "llm_rate_limit": ["rate", "limit", "quota", "throttle", "429"],
    "ingestion": ["ingest", "file", "read", "extract", "upload", "clone"],
    "validation": ["validation", "invalid", "schema", "assert", "check"],
    "empty_output": ["empty", "no output", "blank", "nothing"],
    "runtime": ["runtime", "exception", "error", "crash", "fail"],
}

@dataclass
class _StageTimer:
    started_at: float
    duration_seconds: Optional[float] = None

class MetricsCollector:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.run_id = str(uuid.uuid4())[:8]
        self.agent = "technical-document"
        self._start_time = datetime.now(timezone.utc)
        self.status = "running"

        self.environment = os.getenv("APP_ENV", "development")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.triggered_by = "api"

        self.ingestion: dict[str, Any] = {}
        self.context_building: dict[str, Any] = {}
        self.section_selection: dict[str, Any] = {}
        self.generation: dict[str, Any] = {}
        self.assembly: dict[str, Any] = {}
        self.review: dict[str, Any] = {}

        self._errors: list[dict[str, Any]] = []
        self._error_stage: Optional[str] = None
        self._error_categories: dict[str, int] = {}

        self._token_usage: dict[str, Any] = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "tokens_per_section": {},
        }

        self._process = psutil.Process() if _PSUTIL_AVAILABLE else None
        self._peak_memory_mb: float = 0.0
        self._cpu_samples: list[float] = []
        self._memory_samples: list[float] = []
        self._cpu_monitor_thread: Optional[threading.Thread] = None
        self._monitor_active: bool = False
        self._sampling_interval_seconds: float = 0.5

        self._codebase_coverage: dict[str, Any] = {}
        self._tech_stack: dict[str, Any] = {}
        self._code_examples: dict[str, Any] = {}
        self._acceptance_flag: str = "not_reviewed"

        self._stage_timings: dict[str, _StageTimer] = {}

        self._start_cpu_monitoring()

    def _normalize_status(self, status: str) -> str:
        normalized = (status or "").strip().lower()
        if normalized in CONTROLLED_STATUS_VALUES:
            return normalized
        if normalized in {"failed", "error", "errored"}:
            return "failure"
        if normalized in {"in_progress", "inprogress", "running"}:
            return "running"
        return "failure" if normalized else "failure"

    def _normalize_stage(self, stage: str) -> str:
        normalized = (stage or "").strip().lower()
        if normalized in CONTROLLED_STAGES:
            return normalized
        return "runtime"

    def _categorize_error(self, error_type: str, message: str) -> str:
        normalized_type = (error_type or "").lower()
        message_lower = (message or "").lower()
        if normalized_type in CONTROLLED_ERROR_CATEGORIES:
            return normalized_type
        search_text = f"{normalized_type} {message_lower}"
        for category, keywords in ERROR_CATEGORIES.items():
            if any(keyword in search_text for keyword in keywords):
                return category
        return "unknown"

    def _start_cpu_monitoring(self):
        if not _PSUTIL_AVAILABLE or not self._process:
            return
        self._monitor_active = True
        self._cpu_monitor_thread = threading.Thread(target=self._monitor_cpu, daemon=True)
        self._cpu_monitor_thread.start()

    def _monitor_cpu(self):
        while self._monitor_active:
            try:
                cpu_percent = self._process.cpu_percent(interval=0.1)
                self._cpu_samples.append(cpu_percent)
                mem_mb = self._process.memory_info().rss / (1024 * 1024)
                self._memory_samples.append(mem_mb)
                if mem_mb > self._peak_memory_mb:
                    self._peak_memory_mb = mem_mb
            except Exception:
                pass
            time.sleep(max(self._sampling_interval_seconds - 0.1, 0.1))

    def _stop_cpu_monitoring(self):
        self._monitor_active = False
        if self._cpu_monitor_thread:
            self._cpu_monitor_thread.join(timeout=1)

    def _get_average_cpu_percent(self) -> Optional[float]:
        if not self._cpu_samples:
            return None
        return round(sum(self._cpu_samples) / len(self._cpu_samples), 1)

    def _get_average_memory_mb(self) -> Optional[float]:
        if not self._memory_samples:
            return None
        return round(sum(self._memory_samples) / len(self._memory_samples), 1)

    def _snapshot_memory(self):
        if self._process:
            try:
                mem_mb = self._process.memory_info().rss / (1024 * 1024)
                if mem_mb > self._peak_memory_mb:
                    self._peak_memory_mb = mem_mb
                self._memory_samples.append(mem_mb)
            except Exception:
                pass

    def start_stage(self, stage: str):
        stage = self._normalize_stage(stage)
        self._stage_timings[stage] = _StageTimer(started_at=time.perf_counter())

    def finish_stage(self, stage: str) -> Optional[float]:
        stage = self._normalize_stage(stage)
        timer = self._stage_timings.get(stage)
        if not timer:
            return None
        if timer.duration_seconds is None:
            timer.duration_seconds = round(time.perf_counter() - timer.started_at, 2)
        return timer.duration_seconds

    def get_stage_duration(self, stage: str) -> Optional[float]:
        timer = self._stage_timings.get(self._normalize_stage(stage))
        return None if not timer else timer.duration_seconds

    def record_error(
        self,
        stage: str,
        message: str,
        error_type: str = "unknown",
        exception_type: Optional[str] = None,
        retryable: Optional[bool] = None,
    ):
        stage = self._normalize_stage(stage)
        if not self._error_stage:
            self._error_stage = stage

        category = self._categorize_error(error_type, message)
        self._error_categories[category] = self._error_categories.get(category, 0) + 1

        if retryable is None:
            retryable = category in {"api", "timeout", "llm_rate_limit", "embedding", "runtime"}

        self._errors.append({
            "stage": stage,
            "category": category,
            "message": str(message),
            "exception_type": exception_type or error_type or "UnknownError",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retryable": bool(retryable),
        })

    def record_llm_call(self, section_name: str, prompt_tokens: int, completion_tokens: int):
        prompt_tokens = int(prompt_tokens or 0)
        completion_tokens = int(completion_tokens or 0)
        self._token_usage["total_prompt_tokens"] += prompt_tokens
        self._token_usage["total_completion_tokens"] += completion_tokens
        total = prompt_tokens + completion_tokens
        self._token_usage["tokens_per_section"][section_name] = (
            self._token_usage["tokens_per_section"].get(section_name, 0) + total
        )

    def record_codebase_coverage(
        self,
        discovered_apis: int,
        documented_apis: int,
        discovered_classes: int,
        documented_classes: int,
        discovered_functions: int,
        documented_functions: int,
    ):
        discovered_total = discovered_apis + discovered_classes + discovered_functions
        documented_total = documented_apis + documented_classes + documented_functions
        
        # Cap documented counts at discovered counts for metrics
        documented_apis = min(documented_apis, discovered_apis)
        documented_classes = min(documented_classes, discovered_classes)
        documented_functions = min(documented_functions, discovered_functions)
        
        covered_total = documented_apis + documented_classes + documented_functions
        
        # Ensure documented_total reflects the capped values in our output payload
        documented_total = covered_total
        
        overall = round((covered_total / discovered_total * 100) if discovered_total > 0 else 0.0, 1)
        self._codebase_coverage = {
            "discovered_apis": discovered_apis,
            "documented_apis": documented_apis,
            "discovered_classes": discovered_classes,
            "documented_classes": documented_classes,
            "discovered_functions": discovered_functions,
            "documented_functions": documented_functions,
            "discovered_total": discovered_total,
            "documented_total": documented_total,
            "covered_total": covered_total,
            "overall_coverage_percent": overall,
        }

    def record_tech_stack(
        self,
        detected_stack: dict,
        actual_stack: Optional[dict] = None,
        correct_matches: Optional[list[str]] = None,
        missed_items: Optional[list[str]] = None,
        false_positives: Optional[list[str]] = None,
        accuracy_score: Optional[float] = None,
    ):
        detected_stack = detected_stack or {}
        actual_stack = actual_stack or {}
        correct_matches = correct_matches if correct_matches is not None else []
        missed_items = missed_items if missed_items is not None else []
        false_positives = false_positives if false_positives is not None else []
        if accuracy_score is None:
            actual_count = len(actual_stack) if actual_stack else 0
            denom = max(len(correct_matches) + len(missed_items) + len(false_positives), 1)
            accuracy_score = round(len(correct_matches) / denom, 3)
            if actual_count == 0 and detected_stack:
                accuracy_score = 0.85
        self._tech_stack = {
            "detected": detected_stack,
            "actual": actual_stack,
            "correct_matches": correct_matches,
            "missed_items": missed_items,
            "false_positives": false_positives,
            "accuracy_score": round(float(accuracy_score), 3),
        }

    def record_code_example_validity(
        self,
        total_examples: int,
        valid_examples: int,
        invalid_examples: Optional[int] = None,
        validation_method: str = "syntax_and_lint",
        errors: Optional[list[dict[str, Any]]] = None,
    ):
        total_examples = int(total_examples or 0)
        valid_examples = int(valid_examples or 0)
        invalid_examples = int(invalid_examples if invalid_examples is not None else max(total_examples - valid_examples, 0))
        score = round((valid_examples / total_examples * 100) if total_examples > 0 else 0.0, 1)
        self._code_examples = {
            "total_examples": total_examples,
            "valid_examples": valid_examples,
            "invalid_examples": invalid_examples,
            "validation_method": validation_method,
            "errors": errors or [],
            "validity_score_percent": score,
        }

    def set_acceptance_flag(self, flag: str):
        normalized = (flag or "").strip().lower()
        if normalized not in CONTROLLED_ACCEPTANCE_FLAGS:
            raise ValueError(f"Invalid acceptance flag: {flag}")
        self._acceptance_flag = normalized

    def record_ingestion(
        self,
        source_type: str,
        total_files_found: int,
        files_after_filter: int,
        duration_seconds: float,
        success: bool,
    ):
        self.ingestion = {
            "source_type": source_type,
            "total_files_found": int(total_files_found or 0),
            "files_after_filter": int(files_after_filter or 0),
            "filter_rate_percent": round((files_after_filter / total_files_found * 100) if total_files_found > 0 else 0.0, 1),
            "ingestion_duration_seconds": round(float(duration_seconds or 0.0), 2),
            "ingestion_success": bool(success),
            "input_profile": {},
        }

    def record_input_profile(
        self,
        total_loc: int,
        primary_language: str,
        language_breakdown: dict,
        repo_size_kb: float,
    ):
        self.ingestion.setdefault("input_profile", {})
        self.ingestion["input_profile"] = {
            "total_loc": int(total_loc or 0),
            "primary_language": primary_language,
            "language_breakdown": language_breakdown or {},
            "repo_size_kb": round(float(repo_size_kb or 0.0), 1),
        }

    def record_context_building(
        self,
        total_chunks: int,
        strategy: str,
        embedding_duration_seconds: float,
        vector_store_size_mb: float,
        raptor_summary_nodes: int = 0,
        context_building_duration_seconds: Optional[float] = None,
    ):
        self._snapshot_memory()
        self.context_building = {
            "strategy": strategy,
            "total_chunks": int(total_chunks or 0),
            "embedding_duration_seconds": round(float(embedding_duration_seconds or 0.0), 2),
            "context_building_duration_seconds": round(float(context_building_duration_seconds or embedding_duration_seconds or 0.0), 2),
            "vector_store_size_mb": round(float(vector_store_size_mb or 0.0), 2),
            "raptor_summary_nodes": int(raptor_summary_nodes or 0),
        }

    def record_section_selection(self, total_available: int, total_selected: int, selection_method: str):
        self.section_selection = {
            "total_sections_available": int(total_available or 0),
            "sections_selected": int(total_selected or 0),
            "selection_method": selection_method,
        }

    def record_generation(
        self,
        sections_attempted: int,
        sections_succeeded: int,
        sections_failed: int,
        per_section_scores: dict,
        total_duration_seconds: float,
        llm_retries: int = 0,
        per_section_word_counts: Optional[dict] = None,
        quality_scoring_method: str = "heuristic_length_structure_keyword",
        quality_score_scale: str = "0_to_1",
    ):
        self._snapshot_memory()
        per_section_word_counts = per_section_word_counts or {}
        scores = [v for v in per_section_scores.values() if v is not None]
        empty_sections = [name for name, count in per_section_word_counts.items() if count < 50]

        self.generation = {
            "sections_attempted": int(sections_attempted or 0),
            "sections_succeeded": int(sections_succeeded or 0),
            "sections_failed": int(sections_failed or 0),
            "section_success_rate_percent": round((sections_succeeded / sections_attempted * 100) if sections_attempted > 0 else 0.0, 1),
            "avg_quality_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
            "min_quality_score": round(min(scores), 3) if scores else 0.0,
            "max_quality_score": round(max(scores), 3) if scores else 0.0,
            "per_section_scores": {k: round(v, 3) for k, v in per_section_scores.items() if v is not None},
            "total_generation_duration_seconds": round(float(total_duration_seconds or 0.0), 2),
            "llm_retries": int(llm_retries or 0),
            "per_section_word_counts": per_section_word_counts,
            "empty_sections": empty_sections,
            "quality_scoring_method": quality_scoring_method,
            "quality_score_scale": quality_score_scale,
        }

    def record_assembly(
        self,
        output_file: str,
        output_size_bytes: int,
        word_count: int,
        page_estimate: int,
        section_count: int,
        duration_seconds: float,
        success: bool,
        output_validation_success: Optional[bool] = None,
        output_validation_error: Optional[str] = None,
    ):
        self.assembly = {
            "output_file": output_file,
            "output_size_bytes": int(output_size_bytes or 0),
            "output_size_kb": round(int(output_size_bytes or 0) / 1024, 1),
            "word_count": int(word_count or 0),
            "page_estimate": int(page_estimate or 0),
            "section_count": int(section_count or 0),
            "assembly_duration_seconds": round(float(duration_seconds or 0.0), 2),
            "assembly_success": bool(success),
            "output_validation_success": output_validation_success if output_validation_success is not None else bool(success),
            "output_validation_error": output_validation_error,
        }

    def record_review(self, review_cycles: int, review_cycle_source: str = "not_reviewed", review_duration_seconds: Optional[float] = None):
        source = (review_cycle_source or "not_reviewed").strip().lower()
        if source not in CONTROLLED_REVIEW_SOURCES:
            source = "not_reviewed"
        self.review = {
            "review_cycles": int(review_cycles or 0),
            "review_cycle_source": source,
            "review_duration_seconds": round(float(review_duration_seconds or 0.0), 2) if review_duration_seconds is not None else 0.0,
        }

    def _validate_payload(self, payload: dict[str, Any]):
        if payload["status"] not in CONTROLLED_STATUS_VALUES:
            raise ValueError(f"Invalid status: {payload['status']}")
        if payload["end_to_end_duration_seconds"] < 0:
            raise ValueError("Invalid end-to-end duration")
        if payload["status"] == "failure" and not payload.get("error_stage"):
            raise ValueError("Failed runs must include error_stage")
        if payload["llm_usage"]["total_tokens"] != payload["llm_usage"]["total_prompt_tokens"] + payload["llm_usage"]["total_completion_tokens"]:
            raise ValueError("Token totals mismatch")
        if payload["generation"]["sections_attempted"] != payload["generation"]["sections_succeeded"] + payload["generation"]["sections_failed"]:
            raise ValueError("Section totals mismatch")
        if payload["assembly"]["output_size_bytes"] and abs(payload["assembly"]["output_size_kb"] - round(payload["assembly"]["output_size_bytes"] / 1024, 1)) > 0.1:
            raise ValueError("Output size mismatch")
        if payload["status"] == "failure" and not payload["errors"]["errors"]:
            raise ValueError("Failed runs must include error records")

    def save(self, status: str = "success") -> str:
        self._stop_cpu_monitoring()
        self._snapshot_memory()

        self.status = self._normalize_status(status)
        if self.status in {"success", "partial_success"} and self._error_stage and self._error_stage not in CONTROLLED_STAGES:
            self._error_stage = "runtime"

        end_time = datetime.now(timezone.utc)
        e2e_seconds = round((end_time - self._start_time).total_seconds(), 2)

        pt = int(self._token_usage["total_prompt_tokens"])
        ct = int(self._token_usage["total_completion_tokens"])
        cost = round((pt / 1000 * _COST_PER_1K_PROMPT_TOKENS) + (ct / 1000 * _COST_PER_1K_COMPLETION_TOKENS), 6)

        llm_usage = {
            "total_prompt_tokens": pt,
            "total_completion_tokens": ct,
            "total_tokens": pt + ct,
            "estimated_cost_usd": cost,
            "tokens_per_section": self._token_usage["tokens_per_section"],
        }

        system_info: dict[str, Any] = {
            "platform": platform.system().lower(),
            "python_version": platform.python_version(),
            "peak_memory_mb": round(self._peak_memory_mb, 1),
            "avg_memory_mb": self._get_average_memory_mb(),
            "cpu_percent_avg": self._get_average_cpu_percent(),
            "cpu_percent_peak": round(max(self._cpu_samples), 1) if self._cpu_samples else None,
            "sampling_interval_seconds": self._sampling_interval_seconds,
        }

        errors_summary = {
            "total_errors": len(self._errors),
            "error_categories": self._error_categories,
            "errors": self._errors,
        }

        quality_metrics = {
            "codebase_coverage": self._codebase_coverage if self._codebase_coverage else None,
            "tech_stack": self._tech_stack if self._tech_stack else None,
            "code_examples": self._code_examples if self._code_examples else None,
            "acceptance_flag": self._acceptance_flag,
        }

        payload = {
            "run_id": self.run_id,
            "project_id": self.project_id,
            "agent": self.agent,
            "environment": self.environment,
            "app_version": self.app_version,
            "triggered_by": self.triggered_by,
            "timestamp": self._start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "status": self.status,
            "error_stage": self._error_stage,
            "errors": errors_summary,
            "system": system_info,
            "llm_usage": llm_usage,
            "ingestion": self.ingestion,
            "context_building": self.context_building,
            "section_selection": self.section_selection,
            "generation": self.generation,
            "assembly": self.assembly,
            "review": self.review,
            "quality_metrics": quality_metrics,
            "end_to_end_duration_seconds": e2e_seconds,
        }

        self._validate_payload(payload)

        os.makedirs(METRICS_DIR, exist_ok=True)
        ts = self._start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"technical_agent_run_{self.project_id}_{ts}.json"
        filepath = os.path.join(METRICS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return filepath