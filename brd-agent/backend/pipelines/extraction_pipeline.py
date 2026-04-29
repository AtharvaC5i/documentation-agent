"""
Extraction Pipeline — v2 optimised.

LLM calls: 3 fixed (was 7)
  1. Transcript requirement extraction
  2. User story requirement extraction
  3. Conflict detection (separate, better quality)
  + 1 call for glossary + coverage (combined but simpler tasks)

Changes from v1:
  - Transcript normalisation is Python-only (no LLM call)
  - User story structure parsed in Python before LLM
  - Conflict detection separated from coverage for better accuracy
  - Semantic deduplication: removes near-duplicate requirements
  - Each section wrapped in try/except so one failure never kills whole pipeline
  - Source location tracked on every requirement for traceability
"""

import re
import json
import traceback
import difflib
from typing import List, Dict, Tuple, Any

from models.project import Project, ProjectStore, Requirement
from utils.databricks_client import call_databricks_llm, parse_llm_json
from utils.logger import info, success, warn, error, step, divider, llm_call, llm_response
from agents.section_suggester import suggest_sections_from_coverage_rules


# ── Python-only transcript cleaner ──────────────────────────────────────────

FILLER_RE = re.compile(
    r'\b(um+|uh+|hmm+|you know|like I said|basically|so basically|'
    r'kind of|sort of|I mean|right\?|okay so|so yeah|yeah so|'
    r'honestly|literally|actually anyway|I think|I feel like)\b',
    re.IGNORECASE
)
MULTI_SPACE = re.compile(r' {2,}')
REPEAT_WORD = re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE)


def clean_transcript(raw: str) -> str:
    lines = raw.split('\n')
    cleaned = []
    for line in lines:
        line = FILLER_RE.sub('', line)
        line = REPEAT_WORD.sub(r'\1', line)
        line = MULTI_SPACE.sub(' ', line).strip()
        if line:
            cleaned.append(line)
    result = '\n'.join(cleaned)
    info("NORMALIZE", f"Python cleaner: {len(raw)} → {len(result)} chars (no API call)")
    return result


# ── Python user story parser ─────────────────────────────────────────────────

US_PATTERN = re.compile(
    r'(US-\d+).*?\nTitle:\s*(.+?)\n'
    r'.*?As a (.+?)\n.*?I want to (.+?)\n.*?So that (.+?)\n'
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
    parsed = []
    for m in US_PATTERN.finditer(stories_text):
        us_id    = m.group(1)
        title    = m.group(2).strip()
        role     = m.group(3).strip()
        action   = m.group(4).strip()
        value    = m.group(5).strip()
        priority = PRIORITY_MAP.get(m.group(6).strip().lower(), 'should_have')
        parsed.append({
            'user_story_id': us_id,
            'title': title,
            'role': role,
            'action': action,
            'value': value,
            'priority': priority,
            'raw_statement': f"As a {role}, I want to {action}, so that {value}",
        })
    info("STORIES", f"Python parser extracted {len(parsed)} structured user stories")
    return parsed, stories_text


# ── Semantic deduplication ────────────────────────────────────────────────────

def _deduplicate_requirements(requirements: List[Requirement]) -> List[Requirement]:
    """
    Remove near-duplicate requirements using string similarity.
    Keeps the first occurrence. Threshold: 85% similar descriptions.
    """
    unique = []
    seen_descs = []
    removed = 0

    for req in requirements:
        desc = req.description.lower().strip()
        is_dup = False
        for seen in seen_descs:
            ratio = difflib.SequenceMatcher(None, desc, seen).ratio()
            if ratio > 0.85:
                is_dup = True
                removed += 1
                break
        if not is_dup:
            unique.append(req)
            seen_descs.append(desc)

    if removed:
        warn("POOL", f"Semantic deduplication removed {removed} near-duplicate requirements")
    return unique


# ── Post-generation word count limiter (FIXED MARKDOWN TRUNCATION) ───────────

def _truncate_section_content(content: str, max_words: int = 350) -> str:
    """
    Truncate generated section content to max_words without destroying formatting.
    Preserves original newlines, Markdown tables, and headings.
    """
    # Quick check: if already under limit, return as is
    if len(content.split()) <= max_words:
        return content

    # Find the exact character index where the word count hits max_words
    # Using regex preserves all the original \n and spaces!
    matches = list(re.finditer(r'\S+', content))
    if len(matches) <= max_words:
        return content
        
    cutoff_index = matches[max_words - 1].end()
    partial = content[:cutoff_index]

    # 1. TABLE PROTECTION: Check if we are currently inside a Markdown table
    last_newline = partial.rfind('\n')
    current_line = partial[last_newline:] if last_newline != -1 else partial

    if '|' in current_line:
        # We are inside a table row! 
        # Extend to the end of the current table row from the original content
        row_end = content.find('\n', cutoff_index)
        if row_end == -1:
            row_end = len(content)
        return content[:row_end].strip()

    # 2. PROSE PROTECTION: Clean sentence break
    # Find the last period, exclamation, or question mark in the partial string
    last_period = max(
        partial.rfind('. '), partial.rfind('.\n'),
        partial.rfind('! '), partial.rfind('!\n'),
        partial.rfind('? '), partial.rfind('?\n')
    )

    if last_period != -1:
        return partial[:last_period + 1].strip()

    # Fallback if no sentence boundaries found
    return partial.strip() + '...'


# ── Section word limits (matches section_prompts.py) ─────────────────────────

SECTION_WORD_LIMITS = {
    "executive summary":    500,
    "business context":     600,
    "objective":            500,
    "scope":                600,
    "stakeholder":          500,
    "functional req":       1400,  # largest section — tables + prose per module
    "non-functional":       700,
    "non functional":       700,
    "business rule":        800,
    "user roles":           750,
    "user journey":         900,
    "use case":             900,
    "data req":             600,
    "integration":          700,
    "assumption":           500,
    "constraint":           500,
    "dependenc":            450,
    "risk":                 650,
    "glossary":             600,
    "appendix":             500,
    "appendices":           500,
}


def get_word_limit(section_name: str) -> int:
    sl = section_name.lower()
    for key, limit in SECTION_WORD_LIMITS.items():
        if key in sl:
            return limit
    return 300  # default


# ── Main pipeline ─────────────────────────────────────────────────────────────

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
            # ── Step 1: Clean transcript (Python, no LLM) ─────────────────
            self._update_progress(5, "Cleaning transcript...")
            cleaned_transcript = ""
            if self.project.transcript_raw:
                cleaned_transcript = clean_transcript(self.project.transcript_raw)
                success("NORMALIZE", "Transcript cleaned — no API call used")
            else:
                warn("NORMALIZE", "No transcript provided")

            # ── Step 2: Extract from transcript — LLM Call 1 ──────────────
            self._update_progress(15, "Extracting requirements from transcript...")
            transcript_requirements = []
            if cleaned_transcript:
                try:
                    transcript_requirements = await self._extract_from_transcript(cleaned_transcript)
                    success("EXTRACT", f"{len(transcript_requirements)} requirements from transcript")
                except Exception as ex:
                    warn("EXTRACT", f"Transcript extraction failed: {ex} — continuing with empty pool")

            # ── Step 3: Parse + extract user stories — LLM Call 2 ─────────
            self._update_progress(35, "Parsing user stories...")
            story_requirements = []
            if self.project.user_stories_raw:
                try:
                    pre_parsed, remaining = parse_user_stories_python(self.project.user_stories_raw)
                    story_requirements = await self._extract_from_user_stories(remaining, pre_parsed)
                    success("STORIES", f"{len(story_requirements)} requirements from user stories")
                except Exception as ex:
                    warn("STORIES", f"User story extraction failed: {ex} — continuing")

            # ── Step 4: Merge and deduplicate pool ────────────────────────
            self._update_progress(50, "Building requirements pool...")
            all_requirements = transcript_requirements + story_requirements

            # First pass: exact req_id dedup
            seen_ids = set()
            id_unique = []
            for r in all_requirements:
                if r.req_id not in seen_ids:
                    seen_ids.add(r.req_id)
                    id_unique.append(r)

            # Second pass: semantic dedup
            unique_requirements = _deduplicate_requirements(id_unique)

            type_counts: Dict[str, int] = {}
            for r in unique_requirements:
                type_counts[r.type] = type_counts.get(r.type, 0) + 1

            info("POOL", f"Final pool: {len(unique_requirements)} requirements")
            for t, c in sorted(type_counts.items()):
                info("POOL", f"  {t:<28} {c}")

            self.project.requirements_pool = unique_requirements

            # ── Step 5: Glossary + coverage — LLM Call 3 ──────────────────
            self._update_progress(60, "Building glossary and coverage analysis...")
            all_text = (self.project.transcript_raw or "") + "\n" + (self.project.user_stories_raw or "")
            try:
                glossary, coverage = await self._glossary_and_coverage(unique_requirements, all_text)
                self.project.glossary  = glossary
                self.project.section_coverage = coverage
                success("GLOSSARY", f"{len(glossary)} terms")
            except Exception as ex:
                warn("GLOSSARY", f"Glossary/coverage failed: {ex} — using defaults")
                self.project.glossary = {}
                self.project.section_coverage = {}

            # ── Step 6: Conflict detection — LLM Call 4 ───────────────────
            # Separate call for better conflict detection accuracy
            self._update_progress(72, "Detecting conflicts...")
            try:
                conflicts = await self._detect_conflicts(unique_requirements)
                self.project.conflicts = conflicts
                if conflicts:
                    warn("CONFLICTS", f"{len(conflicts)} conflict(s) detected")
                    for c in conflicts:
                        warn("CONFLICTS", f"  [{c.get('impact','?').upper()}] {c.get('description','')}")
                else:
                    success("CONFLICTS", "No conflicts detected")
            except Exception as ex:
                warn("CONFLICTS", f"Conflict detection failed: {ex} — skipping")
                self.project.conflicts = []

            # Build gaps from coverage
            gaps = self._build_gaps(self.project.section_coverage)
            self.project.gaps = gaps
            strong = sum(1 for v in self.project.section_coverage.values() if v == "strong")
            weak   = sum(1 for v in self.project.section_coverage.values() if v == "weak")
            none_  = sum(1 for v in self.project.section_coverage.values() if v == "none")
            info("COVERAGE", f"Sections — strong: {strong} | weak: {weak} | none: {none_}")

            # ── Step 7: Section suggestion — pure Python rules ─────────────
            self._update_progress(88, "Suggesting sections (rules-based, no API)...")
            suggested = suggest_sections_from_coverage_rules(
                self.project.section_coverage,
                self.project.description,
                self.project.industry
            )
            self.project.suggested_sections = suggested
            suggested_count = sum(1 for s in suggested if s.get("suggested"))
            success("SECTIONS", f"{suggested_count}/{len(suggested)} sections pre-selected")

            self.project.status = "extracted"
            self._update_progress(100, "Extraction complete.")
            divider("EXTRACTION COMPLETE — 4 API calls used")

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
        system_prompt = """You are a senior Business Analyst extracting structured requirements from a meeting transcript.

Extract ALL of the following — return a JSON array ONLY:
- Functional requirements: what the system must DO
- Non-functional requirements: performance, security, scalability, compliance, availability
- Business rules: policies and conditions governing system behavior
- Assumptions: things taken for granted, not explicitly confirmed
- Constraints: hard limits on technology, budget, timeline, regulatory
- Stakeholders: people, roles, and their responsibilities

JSON schema per item:
{
  "req_id": "TR-001",
  "type": "functional|non_functional|business_rule|assumption|constraint|stakeholder",
  "description": "concise professional statement — MAX 25 WORDS",
  "source": "transcript",
  "speaker": "speaker name or null",
  "confidence": 0.7-1.0,
  "priority": "must_have|should_have|could_have|null",
  "module_tag": "payments|auth|inventory|search|delivery|analytics|admin|vendor|mobile|compliance",
  "source_location": "approximate timestamp e.g. 00:22:10 or null",
  "acceptance_criteria": ["one criterion max"] or null
}

RULES:
- descriptions MAX 25 words — be concise
- Extract EVERY requirement — miss nothing
- Return ONLY the JSON array, nothing else"""

        user_prompt = f"Extract all requirements:\n\n{transcript[:5000]}"
        llm_call("EXTRACT", "Transcript extraction", len(user_prompt))
        raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=8000, json_mode=True)
        llm_response("EXTRACT", len(raw))

        data = parse_llm_json(raw)
        items = data if isinstance(data, list) else data.get("requirements", []) if isinstance(data, dict) else []

        requirements = []
        for i, item in enumerate(items):
            try:
                if not item.get("req_id"):
                    item["req_id"] = f"TR-{str(i+1).zfill(3)}"
                item.setdefault("added_in_version", self.project.version)
                requirements.append(Requirement(**item))
            except Exception as ex:
                warn("EXTRACT", f"Skipping item {i}: {ex}")
        return requirements

    async def _extract_from_user_stories(self, stories_text: str, pre_parsed: List[Dict]) -> List[Requirement]:
        summary_lines = [
            f"{p['user_story_id']} [{p['priority']}] {p['raw_statement']}"
            for p in pre_parsed[:30]
        ]
        summary = "\n".join(summary_lines) if summary_lines else stories_text[:3000]

        system_prompt = """You are a Business Analyst converting user stories to formal requirements.

For each user story, return ONE JSON object:
{
  "req_id": "US-001",
  "type": "functional",
  "description": "The system shall [action]. MAX 20 WORDS.",
  "source": "user_story",
  "speaker": null,
  "confidence": 1.0,
  "priority": "must_have|should_have|could_have",
  "module_tag": "one word",
  "user_story_id": "US-001",
  "source_location": "US-001",
  "acceptance_criteria": ["one key criterion"]
}

Return ONLY the JSON array. Descriptions MAX 20 words each."""

        user_prompt = f"Convert to requirements:\n\n{summary}"
        llm_call("STORIES", "User story conversion", len(user_prompt))
        raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=8000, json_mode=True)
        llm_response("STORIES", len(raw))

        data = parse_llm_json(raw)
        items = data if isinstance(data, list) else data.get("requirements", []) if isinstance(data, dict) else []

        requirements = []
        for i, item in enumerate(items):
            try:
                if not item.get("req_id"):
                    item["req_id"] = f"US-{str(i+1).zfill(3)}"
                item["source"] = "user_story"
                item.setdefault("added_in_version", self.project.version)
                requirements.append(Requirement(**item))
            except Exception as ex:
                warn("STORIES", f"Skipping story {i}: {ex}")
        return requirements

    async def _glossary_and_coverage(
        self,
        requirements: List[Requirement],
        all_text: str
    ) -> Tuple[Dict, Dict]:
        """LLM Call 3 — glossary + coverage only (conflicts separated for accuracy)."""

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

        req_lines = [f"[{r.req_id}][{r.type}] {r.description[:100]}" for r in requirements[:60]]
        req_summary = "\n".join(req_lines)
        sections_list = ", ".join(ALL_SECTIONS)

        system_prompt = f"""You are a BRD analyst. Return a JSON object with exactly two keys:

"glossary": dict of 10-15 project-specific terms to one-line definitions
"coverage": dict mapping each section name to "strong"|"weak"|"none"

Sections: {sections_list}

Return ONLY valid JSON. No other text."""

        user_prompt = f"Project text: {all_text[:1500]}\n\nRequirements:\n{req_summary}"

        llm_call("ANALYSIS", "Glossary + coverage", len(user_prompt))
        raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=3000, json_mode=True)
        llm_response("ANALYSIS", len(raw))

        data = parse_llm_json(raw)
        glossary = data.get("glossary", {})
        coverage = data.get("coverage", {})

        for s in ALL_SECTIONS:
            if s not in coverage:
                coverage[s] = "none"

        return glossary, coverage

    async def _detect_conflicts(self, requirements: List[Requirement]) -> List[Dict]:
        """LLM Call 4 — conflict detection only, no other tasks mixed in."""

        req_lines = [f"[{r.req_id}][{r.type}] {r.description[:120]}" for r in requirements[:70]]
        req_summary = "\n".join(req_lines)

        system_prompt = """You are a requirements conflict analyst.

Find ALL contradictions — where two requirements say incompatible things.
Examples: pricing controlled by vendor vs admin, real-time sync vs batch, 7-day return vs 30-day.

Return JSON array. Each item:
{
  "id": "CONF-001",
  "description": "brief description of the contradiction",
  "version_a": {"req_id": "TR-X", "text": "first requirement text"},
  "version_b": {"req_id": "TR-Y", "text": "second requirement text"},
  "impact": "high|medium|low",
  "resolved": false
}

Return [] if no conflicts. Return ONLY the JSON array."""

        user_prompt = f"Find conflicts:\n\n{req_summary}"
        llm_call("CONFLICTS", "Conflict detection", len(user_prompt))
        raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=3000, json_mode=True)
        llm_response("CONFLICTS", len(raw))

        data = parse_llm_json(raw)
        return data if isinstance(data, list) else data.get("conflicts", [])

    def _build_gaps(self, coverage: Dict[str, str]) -> List[Dict]:
        gaps = []
        for section, level in coverage.items():
            if level in ("weak", "none"):
                gaps.append({
                    "id": f"GAP-{str(len(gaps)+1).zfill(3)}",
                    "section": section,
                    "coverage_level": level,
                    "message": f"'{section}' has {'limited' if level == 'weak' else 'no'} coverage.",
                    "suggested_action": (
                        "Fill via follow-up questions" if level == "none"
                        else "Review and confirm with client"
                    )
                })
        return gaps