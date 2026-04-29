"""
Generation Pipeline — with per-section error handling and word count enforcement.

Changes:
- Each section wrapped in try/except — one failure never kills the whole pipeline
- Word count enforcer applied after generation (Python truncation)
- Better quality scorer that checks for meaningful content not just length
- Section generation logs word count alongside quality
"""

import uuid
import re
from typing import List, Dict, Any, Optional

from models.project import Project, ProjectStore, Requirement
from utils.databricks_client import call_databricks_llm, score_quality
from utils.logger import info, success, warn, error, step, divider, llm_call, llm_response
from agents.section_prompts import get_section_prompt
from pipelines.extraction_pipeline import _truncate_section_content, get_word_limit

QUALITY_THRESHOLD = 0.60


class GenerationPipeline:

    def __init__(self, project: Project, store: ProjectStore):
        self.project = project
        self.store = store

    def _update_progress(self, pct: int, message: str):
        self.project.progress = pct
        self.project.progress_message = message
        self.store.save(self.project)

    async def run(self):
        sections = self.project.selected_sections
        total = len(sections)
        divider(f"GENERATION PIPELINE — {self.project.project_name}")
        info("GENERATE", f"{total} sections selected for generation")

        self.project.generated_sections = []
        self.store.save(self.project)

        for i, section_name in enumerate(sections):
            pct = int((i / total) * 90) + 5
            self._update_progress(pct, f"Generating: {section_name} ({i+1}/{total})")
            step("GENERATE", i + 1, total, section_name)

            try:
                section_result = await self._generate_section(section_name)
                q   = section_result.get("quality_pct", "?")
                wc  = section_result.get("word_count", 0)
                reqs = section_result.get("req_count", 0)

                if section_result.get("quality_score", 0) >= QUALITY_THRESHOLD:
                    success("GENERATE", f"{section_name} | quality: {q} | words: {wc} | reqs: {reqs}")
                else:
                    warn("GENERATE", f"{section_name} | quality: {q} | words: {wc} (below threshold — auto-regenerated)")

            except Exception as ex:
                error("GENERATE", f"Section '{section_name}' failed: {ex} — inserting placeholder")
                section_result = self._placeholder_section(section_name)

            self.project.generated_sections.append(section_result)
            self.store.save(self.project)

        self.project.status = "review"
        self._update_progress(100, "All sections generated. Ready for review.")
        divider("GENERATION COMPLETE")

        valid_sections = [s for s in self.project.generated_sections if s.get("quality_score", 0) > 0]
        if valid_sections:
            avg = sum(s["quality_score"] for s in valid_sections) / len(valid_sections)
            info("GENERATE", f"Average quality: {round(avg * 100)}%")

    def _placeholder_section(self, section_name: str) -> Dict[str, Any]:
        """Fallback section when generation fails — never crashes the pipeline."""
        return {
            "id": str(uuid.uuid4()),
            "name": section_name,
            "content": f"## {section_name}\n\n*This section could not be generated automatically. Please use the Edit button to add content manually.*",
            "quality_score": 0.0,
            "quality_pct": "0%",
            "approved": False,
            "status": "failed",
            "sources": [],
            "source_req_ids": [],
            "req_count": 0,
            "word_count": 0,
        }

    async def regenerate_section(self, section_id: str, feedback: str):
        target = None
        for section in self.project.generated_sections:
            if section["id"] == section_id:
                target = section
                break
        if not target:
            return

        target["status"] = "regenerating"
        self.store.save(self.project)

        try:
            result = await self._generate_section(target["name"], feedback=feedback)
        except Exception as ex:
            warn("GENERATE", f"Regeneration failed: {ex}")
            result = self._placeholder_section(target["name"])

        for i, section in enumerate(self.project.generated_sections):
            if section["id"] == section_id:
                self.project.generated_sections[i] = {
                    **result,
                    "id": section_id,
                    "approved": False,
                    "status": "regenerated",
                }
                break

        self.store.save(self.project)

    async def _generate_section(
        self,
        section_name: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:

        relevant_reqs = self._get_relevant_requirements(section_name)
        req_context   = self._format_requirements(relevant_reqs)

        system_prompt, user_prompt = get_section_prompt(
            section_name=section_name,
            project_name=self.project.project_name,
            client_name=self.project.client_name,
            industry=self.project.industry,
            description=self.project.description,
            requirements_context=req_context,
            glossary=self.project.glossary,
            feedback=feedback,
        )

        llm_call("GENERATE", f"Section: {section_name}", len(req_context))
        content = await call_databricks_llm(system_prompt, user_prompt, max_tokens=5000, temperature=0.2)
        llm_response("GENERATE", len(content))

        # Enforce word limit — Python truncation regardless of model compliance
        word_limit = get_word_limit(section_name)
        content    = _truncate_section_content(content, word_limit)

        quality = _meaningful_quality_score(content, section_name, len(relevant_reqs))

        # Auto-regenerate once if quality too low
        if quality < QUALITY_THRESHOLD and not feedback:
            warn("GENERATE", f"Quality {round(quality*100)}% — auto-regenerating {section_name}")
            improved = user_prompt + f"\n\nIMPORTANT: Previous attempt was low quality. Be specific, use tables where appropriate, reference actual requirements."
            llm_call("GENERATE", f"Re-generate: {section_name}")
            content  = await call_databricks_llm(system_prompt, improved, max_tokens=5000, temperature=0.3)
            llm_response("GENERATE", len(content))
            content  = _truncate_section_content(content, word_limit)
            quality  = _meaningful_quality_score(content, section_name, len(relevant_reqs))

        word_count  = len(content.split())
        sources     = list(set(r.source for r in relevant_reqs))
        source_ids  = [r.req_id for r in relevant_reqs[:12]]

        return {
            "id":            str(uuid.uuid4()),
            "name":          section_name,
            "content":       content,
            "quality_score": round(quality, 2),
            "quality_pct":   f"{round(quality * 100)}%",
            "word_count":    word_count,
            "approved":      False,
            "status":        "pending_review",
            "sources":       sources,
            "source_req_ids": source_ids,
            "req_count":     len(relevant_reqs),
        }

    def _get_relevant_requirements(self, section_name: str) -> List[Requirement]:
        section_lower = section_name.lower()
        type_filters = {
            "executive summary":       None,
            "business context":        ["assumption", "constraint", "stakeholder"],
            "objective":               ["non_functional", "assumption", "functional"],
            "scope":                   ["constraint", "assumption", "functional"],
            "stakeholder":             ["stakeholder"],
            "functional req":          ["functional"],
            "non-functional":          ["non_functional"],
            "non functional":          ["non_functional"],
            "business rule":           ["business_rule"],
            "user roles":              ["functional", "stakeholder"],
            "user journey":            ["functional"],
            "use case":                ["functional"],
            "data req":                ["functional", "non_functional"],
            "integration":             ["functional", "constraint"],
            "assumption":              ["assumption"],
            "constraint":              ["constraint"],
            "dependenc":               ["constraint", "assumption"],
            "risk":                    ["constraint", "assumption"],
            "glossary":                None,
            "appendix":                None,
            "appendices":              None,
        }

        matched_types = None
        for key, types in type_filters.items():
            if key in section_lower:
                matched_types = types
                break

        pool = self.project.requirements_pool
        if matched_types is None:
            return pool

        return [r for r in pool if r.type in matched_types]

    def _format_requirements(self, requirements: List[Requirement]) -> str:
        if not requirements:
            return "No specific requirements found. Use project description."

        lines = []
        for r in requirements:
            line = f"[{r.req_id}][{r.type.upper()}]"
            if r.priority:
                line += f"[{r.priority.upper()}]"
            line += f" {r.description}"
            if r.acceptance_criteria:
                line += f" | AC: {r.acceptance_criteria[0]}"
            lines.append(line)

        return "\n".join(lines)


def _meaningful_quality_score(content: str, section_name: str, req_count: int) -> float:
    """
    Improved quality scorer that checks for meaningful content.
    Penalises sections that are too short relative to their requirements count.
    """
    score = 0.0
    words = len(content.split())
    sentences = len(re.findall(r'[.!?]+', content))
    unique_sentences = len(set(re.split(r'[.!?]+', content.lower())))

    if words < 50:
        return 0.05

    # Length score
    if words > 80:   score += 0.20
    if words > 150:  score += 0.10
    if words > 250:  score += 0.05

    # Structure score
    has_heading = bool(re.search(r'^#{1,3}\s', content, re.MULTILINE))
    has_table   = '|' in content and content.count('|') > 4
    has_bullets = bool(re.search(r'^[-*]\s', content, re.MULTILINE))
    has_numbered = bool(re.search(r'^\d+\.\s', content, re.MULTILINE))

    if has_heading:  score += 0.10
    if has_table:    score += 0.15
    if has_bullets or has_numbered: score += 0.10

    # Content uniqueness — penalise if most sentences are identical (copy-paste)
    if sentences > 0:
        uniqueness_ratio = unique_sentences / max(sentences, 1)
        if uniqueness_ratio > 0.7: score += 0.10

    # Section-specific keyword checks
    keywords_map = {
        "executive summary":    ["business", "solution", "objective"],
        "functional req":       ["shall", "system", "FR-", "user"],
        "non-functional":       ["performance", "security", "availability"],
        "business rule":        ["BR-", "must", "cannot", "only"],
        "stakeholder":          ["name", "role", "responsibility"],
        "scope":                ["in scope", "out of scope"],
        "assumption":           ["assume", "A-"],
        "constraint":           ["constraint", "C-"],
        "integration":          ["api", "integration", "sync"],
        "glossary":             ["term", "|"],
    }
    sl = section_name.lower()
    for key, words_list in keywords_map.items():
        if key in sl:
            matches = sum(1 for w in words_list if w.lower() in content.lower())
            score += min(0.20, matches * 0.07)
            break

    # Penalty if section has requirements but content doesn't reference them
    if req_count > 3 and not any(f"FR-" in content or f"TR-" in content or f"US-" in content
                                  for _ in [1]):
        score -= 0.05

    return min(1.0, max(0.0, score))
