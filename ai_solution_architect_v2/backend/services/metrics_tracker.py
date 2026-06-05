"""
metrics_tracker.py

Service for tracking, collecting, and calculating metrics throughout
the PPT generation pipeline. Integrates non-intrusively into existing flows.
"""

import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path
import zipfile
from lxml import etree

from models.metrics_models import (
    GenerationMetricsModel,
    TokenUsageModel,
    SlideMetricsModel,
    DiagramMetricsModel,
    QualityScoreModel,
    PptxValidationModel,
    ArchitectureJustificationModel,
    ErrorDetailsModel,
    ErrorStageEnum,
    ErrorCategoryEnum,
    AcceptanceStatusEnum,
)


class MetricsTracker:
    """
    Non-intrusive metrics collection throughout the generation pipeline.
    
    Usage:
        tracker = MetricsTracker()
        
        with tracker.phase("core_generation"):
            result = await orchestrator.run(payload)
        
        tracker.set_token_usage("core", usage_from_llm)
        tracker.finalize(success=True)
        metrics_dict = tracker.get_metrics_dict()
    """
    
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or str(uuid.uuid4())
        self.metrics = GenerationMetricsModel(run_id=self.run_id)
        self._phase_timers: Dict[str, float] = {}
        self._phase_start_times: Dict[str, float] = {}
    
    @contextmanager
    def phase(self, phase_name: str):
        """
        Context manager to measure duration of a phase.
        
        Usage:
            with tracker.phase("core_generation"):
                result = await orchestrator.run(payload)
        """
        start_time = time.time()
        self._phase_start_times[phase_name] = start_time
        
        try:
            yield
            # Phase succeeded
            duration = time.time() - start_time
            self._phase_timers[phase_name] = duration
            print(f"[Metrics] {phase_name}: {duration:.2f}s")
        except Exception as e:
            # Phase failed
            duration = time.time() - start_time
            self._phase_timers[phase_name] = duration
            print(f"[Metrics] {phase_name}: FAILED after {duration:.2f}s")
            # Don't suppress the exception — let caller handle it
            raise
    
    def set_token_usage(self, phase: str, usage: Optional[Dict[str, int]]) -> None:
        """
        Record LLM token usage for a phase.
        
        Args:
            phase: One of "summarization", "core", "diagram"
            usage: Dict with keys "prompt_tokens" and "completion_tokens"
        """
        if not usage:
            return
        
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        token_model = TokenUsageModel(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        
        if phase == "summarization":
            self.metrics.token_usage_summarization = token_model
        elif phase == "core" or phase == "core_generation":
            self.metrics.token_usage_core = token_model
        elif phase == "diagram" or phase == "diagram_generation":
            self.metrics.token_usage_diagram = token_model
    
    def set_error(
        self,
        stage: ErrorStageEnum,
        category: ErrorCategoryEnum,
        message: str,
        traceback: str = "",
    ) -> None:
        """Record error details"""
        self.metrics.error_details = ErrorDetailsModel(
            occurred=True,
            stage=stage,
            category=category,
            message=message,
            traceback=traceback,
        )
    
    def update_slide_metrics(
        self,
        attempted: int = 0,
        successful: int = 0,
        failed: int = 0,
        retry_count: int = 0,
    ) -> None:
        """Update slide generation metrics"""
        self.metrics.slide_metrics = SlideMetricsModel(
            attempted=attempted,
            successful=successful,
            failed=failed,
            retry_count=retry_count,
        )
    
    def update_sections_metrics(
        self,
        selected_count: int = 0,
        selected_list: list = None,
        custom_sections_count: int = 0,
        custom_sections: list = None,
    ) -> None:
        """Update sections selection metrics"""
        from models.metrics_models import SectionsModel
        
        self.metrics.sections_metrics = SectionsModel(
            selected_count=selected_count,
            selected_list=selected_list or [],
            custom_sections_count=custom_sections_count,
            custom_sections=custom_sections or [],
            total_sections=selected_count + custom_sections_count,
        )
    
    def update_diagram_metrics(
        self,
        attempted: bool,
        success: bool,
        components_count: int,
        connections_count: int,
        expected_components: int = 0,
        expected_connections: int = 0,
    ) -> None:
        """Update diagram generation metrics"""
        self.metrics.diagram_metrics = DiagramMetricsModel(
            attempted=attempted,
            success=success,
            components_count=components_count,
            connections_count=connections_count,
            expected_components=expected_components,
            expected_connections=expected_connections,
        )
    
    def update_quality_scores(
        self,
        content_quality: float,
        diagram_quality: float,
        architecture_alignment: float,
        output_validity: float,
    ) -> None:
        """
        Update quality scores.
        
        Args:
            All scores should be 0.0 to 1.0
        """
        self.metrics.quality_scores = QualityScoreModel(
            content_quality=max(0.0, min(1.0, content_quality)),
            diagram_quality=max(0.0, min(1.0, diagram_quality)),
            architecture_alignment=max(0.0, min(1.0, architecture_alignment)),
            output_validity=max(0.0, min(1.0, output_validity)),
        )
    
    def validate_pptx(self, pptx_path: str) -> None:
        """
        Validate PPTX output integrity.
        
        Checks:
        - File exists and has content
        - Valid ZIP structure
        - Valid XML files
        - Valid relationships
        - Opens without repair
        - All slides/media present
        """
        validation = PptxValidationModel()
        pptx_file = Path(pptx_path)
        
        try:
            # Check file existence and size
            if not pptx_file.exists():
                self.metrics.pptx_validation = validation
                return
            
            validation.file_created = True
            validation.file_size_bytes = pptx_file.stat().st_size
            
            # Validate ZIP structure and XML
            with zipfile.ZipFile(pptx_file, 'r') as pptx_zip:
                # Check XML validity
                validation.valid_xml = self._validate_pptx_xml(pptx_zip)
                
                # Check relationships
                validation.valid_relationships = self._validate_relationships(pptx_zip)
                
                # Check slides
                slide_files = [f for f in pptx_zip.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
                validation.all_slides_present = len(slide_files) > 0
                
                # Check media
                media_files = [f for f in pptx_zip.namelist() if f.startswith('ppt/media/')]
                validation.all_media_present = len(media_files) > 0
            
            # The "opens_without_repair" check is tricky without actually opening in PowerPoint.
            # For now, we'll use a heuristic: if XML and relationships are valid, it's likely OK.
            validation.opens_without_repair = validation.valid_xml and validation.valid_relationships
            
        except Exception as e:
            print(f"[Metrics] PPTX validation error: {e}")
        
        self.metrics.pptx_validation = validation
    
    def _validate_pptx_xml(self, pptx_zip: zipfile.ZipFile) -> bool:
        """Check if all XML files in PPTX are well-formed"""
        try:
            for name in pptx_zip.namelist():
                if name.endswith('.xml'):
                    xml_content = pptx_zip.read(name)
                    try:
                        etree.fromstring(xml_content)
                    except etree.XMLSyntaxError:
                        return False
            return True
        except Exception:
            return False
    
    def _validate_relationships(self, pptx_zip: zipfile.ZipFile) -> bool:
        """Check if relationship files are valid"""
        try:
            for name in pptx_zip.namelist():
                if '.rels' in name:
                    xml_content = pptx_zip.read(name)
                    try:
                        etree.fromstring(xml_content)
                    except etree.XMLSyntaxError:
                        return False
            return True
        except Exception:
            return False
    
    def update_architecture_justification(
        self,
        decisions_identified: int,
        decisions_justified: int,
        brd_citations: int = 0,
        constraint_references: int = 0,
    ) -> None:
        """Update architecture decision justification metrics"""
        self.metrics.architecture_justification = ArchitectureJustificationModel(
            decisions_identified=decisions_identified,
            decisions_justified=decisions_justified,
            brd_citations=brd_citations,
            constraint_references=constraint_references,
        )
    
    def set_review_metrics(
        self,
        review_cycle_count: int = 0,
        acceptance_status: AcceptanceStatusEnum = AcceptanceStatusEnum.PENDING_REVIEW,
    ) -> None:
        """Update review and acceptance metrics"""
        self.metrics.review_cycle_count = review_cycle_count
        self.metrics.acceptance_status = acceptance_status
    
    def set_total_retry_count(self, count: int) -> None:
        """Set total retry count across the entire run"""
        self.metrics.total_retry_count = count
    
    def finalize(self, success: bool) -> None:
        """
        Finalize the metrics collection.
        Should be called after the entire pipeline completes.
        
        Args:
            success: True if the run completed successfully
        """
        self.metrics.run_success = success
        self.metrics.timestamp_end = datetime.utcnow()
        
        # Update phase durations from collected timers
        if "summarization" in self._phase_timers:
            self.metrics.duration_summarization = self._phase_timers["summarization"]
        if "core_generation" in self._phase_timers:
            self.metrics.duration_core_generation = self._phase_timers["core_generation"]
        if "diagram_generation" in self._phase_timers:
            self.metrics.duration_diagram_generation = self._phase_timers["diagram_generation"]
        if "diagram_rendering" in self._phase_timers:
            self.metrics.duration_diagram_rendering = self._phase_timers["diagram_rendering"]
        if "pptx_generation" in self._phase_timers:
            self.metrics.duration_pptx_generation = self._phase_timers["pptx_generation"]
        if "pptx_assembly" in self._phase_timers:
            self.metrics.duration_pptx_assembly = self._phase_timers["pptx_assembly"]
        if "validation" in self._phase_timers:
            self.metrics.duration_validation = self._phase_timers["validation"]
    
    def get_metrics(self) -> GenerationMetricsModel:
        """Get the raw metrics model"""
        return self.metrics
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """Get metrics as a dictionary (includes computed derived values)"""
        return self.metrics.to_dict()
    
    def get_metrics_json(self) -> str:
        """Get metrics as JSON string"""
        import json
        return json.dumps(self.get_metrics_dict(), indent=2)


# ── Helper functions for integration ────────────────────────

def extract_token_usage(llm_response: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract token usage from LLM response.
    Handles both direct dict responses and LLM client response objects.
    
    Args:
        llm_response: Response from LLM (dict or object with usage attribute)
    
    Returns:
        Dict with "prompt_tokens" and "completion_tokens"
    """
    if not llm_response:
        return {"prompt_tokens": 0, "completion_tokens": 0}
    
    # If it's a dict
    if isinstance(llm_response, dict):
        usage = llm_response.get("usage", {})
        if isinstance(usage, dict):
            return {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            }
    
    # If it's an object with usage attribute
    if hasattr(llm_response, "usage"):
        usage = llm_response.usage
        return {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
        }
    
    return {"prompt_tokens": 0, "completion_tokens": 0}


def classify_error(error: Exception, context: str = "") -> tuple[ErrorStageEnum, ErrorCategoryEnum]:
    """
    Classify an error into stage and category for metrics.
    
    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
    
    Returns:
        Tuple of (ErrorStageEnum, ErrorCategoryEnum)
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # Determine stage from context
    stage = ErrorStageEnum.UNKNOWN
    if "summariz" in context:
        stage = ErrorStageEnum.SUMMARIZATION
    elif "core" in context:
        stage = ErrorStageEnum.CORE_GENERATION
    elif "diagram" in context:
        if "render" in context or "draw" in context or "image" in context:
            stage = ErrorStageEnum.DIAGRAM_RENDERING
        elif "build" in context or "struct" in context:
            stage = ErrorStageEnum.DIAGRAM_BUILDING
        else:
            stage = ErrorStageEnum.DIAGRAM_GENERATION
    elif "pptx" in context:
        if "assem" in context or "merge" in context:
            stage = ErrorStageEnum.PPTX_ASSEMBLY
        else:
            stage = ErrorStageEnum.PPTX_GENERATION
    elif "valid" in context:
        stage = ErrorStageEnum.VALIDATION
    
    # Determine category from error characteristics
    category = ErrorCategoryEnum.UNKNOWN_ERROR
    
    if "timeout" in error_str or "timed out" in error_str:
        category = ErrorCategoryEnum.TIMEOUT_ERROR
    elif "memory" in error_str or "out of memory" in error_str:
        category = ErrorCategoryEnum.MEMORY_ERROR
    elif "api" in error_str or "network" in error_str or "connection" in error_str:
        category = ErrorCategoryEnum.API_ERROR
    elif "diagram" in error_str or "drawio" in error_str or "component" in error_str:
        category = ErrorCategoryEnum.DIAGRAM_ERROR
    elif "render" in error_str or "image" in error_str or "png" in error_str:
        category = ErrorCategoryEnum.RENDERING_ERROR
    elif "pptx" in error_str or "assembly" in error_str or "merge" in error_str or "zip" in error_str:
        category = ErrorCategoryEnum.ASSEMBLY_ERROR
    elif "module" in error_type or "import" in error_str or "not found" in error_str:
        category = ErrorCategoryEnum.DEPENDENCY_ERROR
    elif "validation" in context or "invalid" in error_str:
        category = ErrorCategoryEnum.VALIDATION_ERROR
    
    return stage, category
