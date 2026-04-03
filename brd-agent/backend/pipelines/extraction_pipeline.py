"""
Extraction Pipeline — optimised version.

Key changes vs original:
  1. Transcript normalization is now pure Python (no LLM call) — saves 1 API call
  2. Conflict detection + coverage analysis merged into ONE LLM call — saves 1 API call
  3. Section suggestion is now rule-based Python — saves 1 API call
  4. Source location tracked per requirement for traceability matrix
  5. User story structural parsing done in Python before LLM call

Total LLM calls: 3 (was 7) for the extraction phase.
  - Call 1: Transcript requirement extraction
  - Call 2: User story requirement extraction
  - Call 3: Glossary + conflict + coverage combined
"""

import re
import json
import traceback
from typing import List, Dict, Tuple, Any

from models.project import Project, ProjectStore, Requirement
from utils.databricks_client import call_databricks_llm, parse_llm_json
from utils.logger import info, success, warn, error, step, divider, llm_call, llm_response
from agents.section_suggester import suggest_sections_from_coverage_rules
from agents.conflict_detector import detect_conflicts_and_gaps 


# ── Python-based transcript cleaner (replaces LLM normalization call) ──────

FILLER_WORDS = re.compile(
    r'\b(um+|uh+|hmm+|you know|like I said|basically|so basically|'
    r'kind of|sort of|I mean|right\?|okay so|so yeah|yeah so|'
    r'honestly|literally|actually|anyway)\b',
    re.IGNORECASE
)
FALSE_START = re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE)  # repeated words
MULTI_SPACE = re.compile(r' {2,}')


def clean_transcript(raw: str) -> str:
    """
    Python-only transcript cleaning. No LLM needed.
    Handles filler words, false starts, extra whitespace.
    Preserves speaker labels, timestamps, and all content.
    """
    lines = raw.split('\n')
    cleaned = []
    for line in lines:
        line = FILLER_WORDS.sub('', line)
        line = FALSE_START.sub(r'\1', line)
        line = MULTI_SPACE.sub(' ', line).strip()
        if line:
            cleaned.append(line)
    result = '\n'.join(cleaned)
    info("NORMALIZE", f"Python cleaner: {len(raw)} → {len(result)} chars (no API call)")
    return result


# ── Python-based user story structural parser ──────────────────────────────

US_PATTERN = re.compile(
    r'US-(\d+).*?\n'
    r'.*?As a (.+?)\n'
    r'.*?I want to (.+?)\n'
    r'.*?So that (.+?)\n'
    r'.*?Priority:\s*(.+?)\n',
    re.DOTALL | re.IGNORECASE
)

PRIORITY_MAP = {
    'must have': 'must_have', 'must': 'must_have',
    'should have': 'should_have', 'should': 'should_have',
    'could have': 'could_have', 'could': 'could_have',
    'nice to have': 'could_have',
}


def parse_user_stories_python(stories_text: str) -> Tuple[List[Dict], str]:
    """
    Parse structured parts of user stories in Python.
    Returns (parsed_stories list, remaining_text_for_llm).
    The LLM only needs to convert parsed stories to requirement statements.
    """
    parsed = []
    for m in US_PATTERN.finditer(stories_text):
        us_id = f"US-{m.group(1).zfill(3)}"
        role = m.group(2).strip()
        action = m.group(3).strip()
        value = m.group(4).strip()
        priority_raw = m.group(5).strip().lower()
        priority = PRIORITY_MAP.get(priority_raw, 'should_have')

        parsed.append({
            'user_story_id': us_id,
            'role': role,
            'action': action,
            'value': value,
            'priority': priority,
            'raw_statement': f"As a {role}, I want to {action}, so that {value}",
        })

    info("STORIES", f"Python parser extracted {len(parsed)} structured user stories")
    return parsed, stories_text


# ── Main pipeline ──────────────────────────────────────────────────────────

class ExtractionPipeline:

    def __init__(self, project: Project, store: ProjectStore):
        self.project = project
        self.store = store

    def _update_progress(self, pct: int, message: str):
        self.project.progress = pct
        self.project.progress_message = message
        self.store.save(self.project)

    async def run(self):
        divider(f"EXTRACTION PIPELINE — {self.project.project_name}")
        try:
            # ── Step 1: Clean transcript (Python only, no LLM) ────────────
            self._update_progress(5, "Cleaning transcript...")
            cleaned_transcript = ""
            if self.project.transcript_raw:
                cleaned_transcript = clean_transcript(self.project.transcript_raw)
                success("NORMALIZE", "Transcript cleaned (Python, no API call used)")
            else:
                warn("NORMALIZE", "No transcript provided — skipping")

            # ── Step 2: Extract requirements from transcript — LLM Call 1 ─
            self._update_progress(15, "Extracting requirements from transcript...")
            transcript_requirements = []
            if cleaned_transcript:
                transcript_requirements = await self._extract_from_transcript(cleaned_transcript)
                success("EXTRACT", f"{len(transcript_requirements)} requirements from transcript")
            else:
                warn("EXTRACT", "No transcript — skipping")

            # ── Step 3: Parse + extract user stories — LLM Call 2 ─────────
            self._update_progress(35, "Parsing user stories...")
            story_requirements = []
            if self.project.user_stories_raw:
                pre_parsed, remaining = parse_user_stories_python(self.project.user_stories_raw)
                story_requirements = await self._extract_from_user_stories(
                    remaining, pre_parsed
                )
                success("STORIES", f"{len(story_requirements)} requirements from user stories")
            else:
                warn("STORIES", "No user stories — skipping")

            # ── Step 4: Merge requirements pool ───────────────────────────
            self._update_progress(55, "Merging requirements pool...")
            all_requirements = transcript_requirements + story_requirements
            seen = set()
            unique_requirements = []
            for r in all_requirements:
                if r.req_id not in seen:
                    seen.add(r.req_id)
                    unique_requirements.append(r)

            dupes = len(all_requirements) - len(unique_requirements)
            info("POOL", f"Total: {len(all_requirements)} | Dupes removed: {dupes} | Final: {len(unique_requirements)}")

            type_counts: Dict[str, int] = {}
            for r in unique_requirements:
                type_counts[r.type] = type_counts.get(r.type, 0) + 1
            for t, c in sorted(type_counts.items()):
                info("POOL", f"  {t:<28} {c}")

            self.project.requirements_pool = unique_requirements

            # ── Step 5: Glossary + conflict + coverage — LLM Call 3 ───────
            self._update_progress(65, "Running combined analysis (glossary + conflicts + coverage)...")
            all_text = (self.project.transcript_raw or "") + "\n" + (self.project.user_stories_raw or "")
            glossary, conflicts, gaps, coverage = await self._combined_analysis(
                unique_requirements, all_text
            )

            self.project.glossary = glossary
            self.project.conflicts = conflicts
            self.project.gaps = gaps
            self.project.section_coverage = coverage

            success("GLOSSARY", f"{len(glossary)} terms")
            if conflicts:
                warn("CONFLICTS", f"{len(conflicts)} conflict(s) detected")
                for c in conflicts:
                    warn("CONFLICTS", f"  [{c.get('impact','?').upper()}] {c.get('description','')}")
            else:
                success("CONFLICTS", "No conflicts detected")

            strong = sum(1 for v in coverage.values() if v == "strong")
            weak   = sum(1 for v in coverage.values() if v == "weak")
            none_  = sum(1 for v in coverage.values() if v == "none")
            info("COVERAGE", f"Sections — strong: {strong} | weak: {weak} | none: {none_}")

            # ── Step 6: Section suggestion — pure Python rules ─────────────
            self._update_progress(85, "Suggesting BRD sections (rules-based)...")
            suggested = suggest_sections_from_coverage_rules(coverage, self.project.description, self.project.industry)
            self.project.suggested_sections = suggested
            suggested_count = sum(1 for s in suggested if s.get("suggested"))
            success("SECTIONS", f"{suggested_count}/{len(suggested)} sections pre-selected (no API call used)")

            self.project.status = "extracted"
            self._update_progress(100, "Extraction complete.")
            divider("EXTRACTION COMPLETE — 3 API calls used")

        except Exception as e:
            full_error = traceback.format_exc()
            error("PIPELINE", f"Fatal error: {str(e)}")
            print("\n" + "=" * 60)
            print("FULL TRACEBACK:")
            print(full_error)
            print("=" * 60 + "\n")
            self.project.status = "error"
            self.project.progress_message = f"Extraction failed: {str(e)}"
            self.store.save(self.project)
            raise Exception(full_error)

    async def _extract_from_transcript(self, transcript: str) -> List[Requirement]:
        """LLM Call 1 — extract all requirement types from transcript."""
        system_prompt = """You are a senior Business Analyst extracting structured requirements from a meeting transcript.

Extract ALL of the following and return a JSON array:
- Functional requirements (FR): what the system must DO
- Non-functional requirements (NFR): performance, security, scalability, compliance, availability
- Business rules (BR): policies and conditions governing system behavior
- Assumptions (AS): things taken for granted, not explicitly confirmed
- Constraints (CN): hard limits on technology, budget, timeline, regulatory
- Stakeholders (ST): people, roles, and their responsibilities mentioned

STRICT JSON schema per item — return ONLY the array, no other text:
{
  "req_id": "TR-001",
  "type": "functional|non_functional|business_rule|assumption|constraint|stakeholder",
  "description": "concise professional statement, max 2 sentences",
  "source": "transcript",
  "speaker": "speaker name or null",
  "confidence": 0.7-1.0,
  "priority": "must_have|should_have|could_have|null",
  "module_tag": "one word e.g. payments|auth|inventory|search|delivery|analytics|admin",
  "source_location": "approximate timestamp or context e.g. 00:22:10 or null",
  "acceptance_criteria": ["criterion"] or null
}

Rules:
- Keep descriptions SHORT (1-2 sentences max) — no padding or explanation
- Extract EVERYTHING — err on the side of including more
- Each requirement must be standalone and unambiguous"""

        user_prompt = f"Extract all requirements from this transcript:\n\n{transcript[:5000]}"

        llm_call("EXTRACT", "Transcript requirement extraction", len(user_prompt))
        raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=8000, json_mode=True)
        llm_response("EXTRACT", len(raw))

        data = parse_llm_json(raw)
        items = data if isinstance(data, list) else data.get("requirements", []) if isinstance(data, dict) else []

        requirements = []
        skipped = 0
        for i, item in enumerate(items):
            try:
                if not item.get("req_id"):
                    item["req_id"] = f"TR-{str(i+1).zfill(3)}"
                item.setdefault("added_in_version", self.project.version)
                requirements.append(Requirement(**item))
            except Exception as ex:
                warn("EXTRACT", f"Skipping item {i}: {ex}")
                skipped += 1

        if skipped:
            warn("EXTRACT", f"{skipped} items skipped")
        return requirements

    async def _extract_from_user_stories(self, stories_text: str, pre_parsed: List[Dict]) -> List[Requirement]:
        """LLM Call 2 — convert pre-parsed user stories to formal requirements."""

        # Build a compact pre-parsed summary for the LLM
        summary_lines = []
        for p in pre_parsed[:30]:  # cap at 30 to control tokens
            summary_lines.append(
                f"{p['user_story_id']} [{p['priority']}] {p['raw_statement']}"
            )
        summary = "\n".join(summary_lines) if summary_lines else stories_text[:3000]

        system_prompt = """You are a Business Analyst converting user stories into formal requirements.

For each user story, create a structured requirement. Return a JSON array:
{
  "req_id": "US-001",
  "type": "functional",
  "description": "The system shall [action] so that [value]. Max 2 sentences.",
  "source": "user_story",
  "speaker": null,
  "confidence": 1.0,
  "priority": "must_have|should_have|could_have",
  "module_tag": "one word module",
  "user_story_id": "US-001",
  "source_location": "US-001",
  "acceptance_criteria": ["criterion 1", "criterion 2"]
}

Keep descriptions SHORT. One requirement per user story.
If acceptance criteria mention performance/security/compliance, also output a separate non_functional requirement.
Return ONLY the JSON array."""

        user_prompt = f"Convert these user stories to requirements:\n\n{summary}"

        llm_call("STORIES", "User story conversion", len(user_prompt))
        raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=8000, json_mode=True)
        llm_response("STORIES", len(raw))

        data = parse_llm_json(raw)
        items = data if isinstance(data, list) else data.get("requirements", []) if isinstance(data, dict) else []

        requirements = []
        skipped = 0
        for i, item in enumerate(items):
            try:
                if not item.get("req_id"):
                    item["req_id"] = f"US-{str(i+1).zfill(3)}"
                item["source"] = "user_story"
                item.setdefault("added_in_version", self.project.version)
                requirements.append(Requirement(**item))
            except Exception as ex:
                warn("STORIES", f"Skipping story {i}: {ex}")
                skipped += 1

        if skipped:
            warn("STORIES", f"{skipped} stories skipped")
        return requirements

    async def _combined_analysis(
        self,
        requirements: List[Requirement],
        all_text: str
    ) -> Tuple[Dict, List, List, Dict]:
        """
        LLM Call 3 — combines glossary + conflict detection + coverage into ONE call.
        Returns (glossary, conflicts, gaps, coverage).
        """

        ALL_SECTIONS = [
            "Executive Summary", "Business Context and Background",
            "Project Objectives and Success Criteria", "Scope",
            "Stakeholder Register", "Functional Requirements",
            "Non-Functional Requirements", "Business Rules",
            "User Roles and Permissions", "User Journeys and Use Cases",
            "Data Requirements", "Integration Requirements",
            "Assumptions", "Constraints", "Dependencies",
            "Risks", "Glossary", "Appendices",
        ]

        # Build compact requirements summary
        req_lines = [
            f"[{r.req_id}][{r.type}] {r.description[:120]}"
            for r in requirements
        ]
        req_summary = "\n".join(req_lines[:80])  # cap at 80 lines

        sections_list = ", ".join(ALL_SECTIONS)

        system_prompt = f"""You are a BRD analyst. Given a requirements list, return a single JSON object with three keys:

"glossary": dict of project-specific terms to definitions (10-20 terms)
  Example: {{"Admin Portal": "Web interface for central admin team to manage products, pricing and operations"}}

"conflicts": array of contradictions found between requirements
  Each: {{"id": "CONF-001", "description": "brief", "version_a": {{"req_id": "TR-X", "text": "..."}}, "version_b": {{"req_id": "TR-Y", "text": "..."}}, "impact": "high|medium|low", "resolved": false}}
  Return [] if no conflicts found.

"coverage": dict mapping each section to "strong"|"weak"|"none"
  Sections to assess: {sections_list}

Return ONLY the JSON object. No other text."""

        user_prompt = f"""Project text (for glossary): {all_text[:2000]}

Requirements list:
{req_summary}

Analyse and return the combined JSON."""

        llm_call("ANALYSIS", "Combined glossary + conflict + coverage", len(user_prompt))
        raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=4000, json_mode=True)
        llm_response("ANALYSIS", len(raw))

        data = parse_llm_json(raw)

        glossary = data.get("glossary", {})
        conflicts_raw = data.get("conflicts", [])
        coverage = data.get("coverage", {})

        # Ensure all 19 sections present in coverage
        for s in ALL_SECTIONS:
            if s not in coverage:
                coverage[s] = "none"

        # Build gaps list from coverage
        gaps = []
        for section, level in coverage.items():
            if level in ("weak", "none"):
                gaps.append({
                    "id": f"GAP-{str(len(gaps)+1).zfill(3)}",
                    "section": section,
                    "coverage_level": level,
                    "message": f"'{section}' has {'limited' if level == 'weak' else 'no'} coverage.",
                    "suggested_action": (
                        "Fill via follow-up questions to client" if level == "none"
                        else "Review and supplement with client confirmation"
                    )
                })

        return glossary, conflicts_raw, gaps, coverage
