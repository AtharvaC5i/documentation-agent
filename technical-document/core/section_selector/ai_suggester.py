import json
import os
from groq import Groq
from core.analysis.analysis_models import AnalysisResult
from api.schemas.section_schema import SectionSuggestion
from core.section_selector.section_registry import ALL_SECTIONS


client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


SYSTEM_PROMPT = """You are a senior technical writer and software architect.
You will be given a detailed analysis of a software codebase.
Your job is to decide which documentation sections should be written for this specific project.

You must return a JSON array. Each object must have exactly these three fields:
- "name": the section title (string)
- "selected": true if this section is essential for this codebase, false if optional or not applicable
- "reason": one specific sentence explaining why, referencing actual numbers or technologies from the analysis

Rules:
- Be specific. Reference actual detected technologies, endpoint counts, file counts, or config files.
- Do not give generic reasons like "recommended for all projects."
- A section with no relevance to this codebase should be selected: false with a clear reason why it does not apply.
- Return ONLY a valid JSON array. No explanation, no markdown fences, no extra text whatsoever."""


def suggest_sections_ai(analysis: AnalysisResult) -> list[SectionSuggestion]:
    context = _build_context(analysis)
    sections_list = "\n".join(f"- {s}" for s in ALL_SECTIONS)

    print("🤖 [AI Suggester] Calling Groq API for section suggestions...")

    user_message = f"""Codebase analysis:
{context}

Evaluate each of the following sections and decide if it is essential (selected: true) or not applicable (selected: false) for this specific codebase. Return a JSON array with all of them.

Sections to evaluate:
{sections_list}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.3,
            max_tokens=2048,
        )

        raw = response.choices[0].message.content.strip()
        print(f"✅ [AI Suggester] Groq responded. Raw length: {len(raw)} chars")
        print(f"📝 [AI Suggester] Raw response preview: {raw[:300]}")

        # Strip markdown fences if model adds them anyway
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        parsed = json.loads(raw)
        print(f"✅ [AI Suggester] JSON parsed successfully. {len(parsed)} sections returned.")
        return _validate_and_build(parsed, analysis)

    except json.JSONDecodeError as e:
        print(f"❌ [AI Suggester] JSON parse failed: {e}. Falling back to rule engine.")
        return _fallback(analysis)
    except Exception as e:
        print(f"❌ [AI Suggester] Groq call failed: {e}. Falling back to rule engine.")
        raise RuntimeError(f"Groq section suggestion failed: {str(e)}")


def _build_context(analysis: AnalysisResult) -> str:
    lines = [
        f"Total lines of code: {analysis.total_loc:,}",
        f"API endpoints detected: {analysis.api_endpoints_count}",
        f"Languages: {', '.join(analysis.languages) or 'None'}",
        f"Frameworks: {', '.join(analysis.frameworks) or 'None'}",
        f"Databases: {', '.join(analysis.databases) or 'None'}",
        f"Test frameworks: {', '.join(analysis.test_frameworks) or 'None'}",
        f"Has Dockerfile: {analysis.has_dockerfile}",
        f"Has CI/CD config: {analysis.has_cicd}",
        f"Has Kubernetes: {analysis.has_kubernetes}",
        f"Has Terraform: {analysis.has_terraform}",
        f"Has Ansible: {analysis.has_ansible}",
    ]
    return "\n".join(lines)



def _validate_and_build(parsed: list, analysis: AnalysisResult) -> list[SectionSuggestion]:
    """
    Validates LLM output and ensures every section in ALL_SECTIONS
    is present — fills in missing ones with selected: false.
    """
    ai_map = {}
    for item in parsed:
        if isinstance(item, dict) and "name" in item and "selected" in item and "reason" in item:
            ai_map[str(item["name"]).strip()] = {
                "selected": bool(item["selected"]),
                "reason":   str(item["reason"]).strip(),
            }

    suggestions = []
    for section in ALL_SECTIONS:
        if section in ai_map:
            suggestions.append(SectionSuggestion(
                name=section,
                selected=ai_map[section]["selected"],
                reason=ai_map[section]["reason"],
            ))
        else:
            # LLM missed this section — default to not selected
            suggestions.append(SectionSuggestion(
                name=section,
                selected=False,
                reason="Not evaluated by AI — defaulting to optional.",
            ))

    return suggestions


def _fallback(analysis: AnalysisResult) -> list[SectionSuggestion]:
    print("⚠️  [AI Suggester] FALLBACK ACTIVE — using rule engine, not AI.")
    from core.section_selector.rule_engine import suggest_sections
    return suggest_sections(analysis)
