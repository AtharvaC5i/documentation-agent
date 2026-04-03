"""
Generation Pipeline
Generates each BRD section via Databricks LLM calls.
Includes quality scoring and auto-regeneration.
"""

import uuid
from typing import List, Dict, Any, Optional

from models.project import Project, ProjectStore, Requirement
from utils.databricks_client import call_databricks_llm, score_quality
from utils.logger import info, success, warn, error, step, divider, llm_call, llm_response
from agents.section_prompts import get_section_prompt


QUALITY_THRESHOLD = 0.65  # Sections below this auto-regenerate once


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

            section_result = await self._generate_section(section_name)
            q = section_result.get("quality_pct", "?")
            reqs = section_result.get("req_count", 0)

            if section_result.get("quality_score", 0) >= QUALITY_THRESHOLD:
                success("GENERATE", f"{section_name} | quality: {q} | reqs used: {reqs}")
            else:
                warn("GENERATE", f"{section_name} | quality: {q} (below threshold, was auto-regenerated)")

            self.project.generated_sections.append(section_result)
            self.store.save(self.project)

        self.project.status = "review"
        self._update_progress(100, "All sections generated. Ready for review.")
        divider("GENERATION COMPLETE")
        avg = sum(s.get("quality_score", 0) for s in self.project.generated_sections) / max(len(self.project.generated_sections), 1)
        info("GENERATE", f"Average quality score: {round(avg * 100)}%")

    async def regenerate_section(self, section_id: str, feedback: str):
        """Regenerate a single section with user feedback"""
        # Find the section
        target = None
        for section in self.project.generated_sections:
            if section["id"] == section_id:
                target = section
                break

        if not target:
            return

        target["status"] = "regenerating"
        self.store.save(self.project)

        section_name = target["name"]
        result = await self._generate_section(section_name, feedback=feedback)

        # Update in place
        for i, section in enumerate(self.project.generated_sections):
            if section["id"] == section_id:
                self.project.generated_sections[i] = {
                    **result,
                    "id": section_id,  # preserve original ID
                    "approved": False,
                    "status": "regenerated"
                }
                break

        self.store.save(self.project)

    async def _generate_section(
        self,
        section_name: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a single BRD section"""

        # Get relevant requirements for this section
        relevant_reqs = self._get_relevant_requirements(section_name)
        req_context = self._format_requirements(relevant_reqs)

        # Get section-specific prompt
        system_prompt, user_prompt = get_section_prompt(
            section_name=section_name,
            project_name=self.project.project_name,
            client_name=self.project.client_name,
            industry=self.project.industry,
            description=self.project.description,
            requirements_context=req_context,
            glossary=self.project.glossary,
            feedback=feedback
        )

        llm_call("GENERATE", f"Section: {section_name}", len(req_context))
        content = await call_databricks_llm(system_prompt, user_prompt, max_tokens=4000, temperature=0.2)
        llm_response("GENERATE", len(content))
        quality = score_quality(content, section_name)

        # Auto-regenerate once if quality is low
        if quality < QUALITY_THRESHOLD and not feedback:
            warn("GENERATE", f"Quality {round(quality*100)}% below threshold — auto-regenerating {section_name}")
            improved_prompt = user_prompt + f"\n\nNote: Previous attempt scored {quality:.0%} quality. Please be more comprehensive, specific, and structured."
            llm_call("GENERATE", f"Re-generate: {section_name}")
            content = await call_databricks_llm(system_prompt, improved_prompt, max_tokens=4000, temperature=0.3)
            llm_response("GENERATE", len(content))
            quality = score_quality(content, section_name)

        # Extract source references
        sources = list(set([r.source for r in relevant_reqs]))
        source_req_ids = [r.req_id for r in relevant_reqs[:10]]  # top 10 for display

        return {
            "id": str(uuid.uuid4()),
            "name": section_name,
            "content": content,
            "quality_score": round(quality, 2),
            "quality_pct": f"{round(quality * 100)}%",
            "approved": False,
            "status": "pending_review",
            "sources": sources,
            "source_req_ids": source_req_ids,
            "req_count": len(relevant_reqs)
        }

    def _get_relevant_requirements(self, section_name: str) -> List[Requirement]:
        """Return requirements most relevant to a given section"""
        section_lower = section_name.lower()

        # Mapping from section to requirement types and module tags
        type_filters = {
            "executive summary": None,  # all types
            "business context": ["assumption", "constraint"],
            "objectives": ["non_functional", "assumption"],
            "scope": ["constraint", "assumption"],
            "stakeholder": ["stakeholder"],
            "functional requirements": ["functional"],
            "non-functional requirements": ["non_functional"],
            "business rules": ["business_rule"],
            "user roles": ["functional", "stakeholder"],
            "user journeys": ["functional"],
            "data requirements": ["functional", "non_functional"],
            "integration requirements": ["functional", "constraint"],
            "assumptions": ["assumption"],
            "constraints": ["constraint"],
            "dependencies": ["constraint", "assumption"],
            "risks": ["constraint", "assumption"],
            "glossary": None,  # all
            "appendices": None,  # all
        }

        # Find matching key
        matched_types = None
        for key, types in type_filters.items():
            if key in section_lower:
                matched_types = types
                break

        pool = self.project.requirements_pool

        if matched_types is None:
            return pool  # return all

        return [r for r in pool if r.type in matched_types]

    def _format_requirements(self, requirements: List[Requirement]) -> str:
        """Format requirements list for LLM context"""
        if not requirements:
            return "No specific requirements found for this section. Use project description and general knowledge."

        lines = []
        for r in requirements:
            line = f"[{r.req_id}] [{r.type.upper()}]"
            if r.priority:
                line += f" [{r.priority.upper()}]"
            line += f" {r.description}"
            if r.acceptance_criteria:
                for ac in r.acceptance_criteria[:3]:  # limit to 3
                    line += f"\n  AC: {ac}"
            if r.speaker:
                line += f"\n  Source: {r.speaker} ({r.source})"
            lines.append(line)

        return "\n\n".join(lines)
