import os
from groq import Groq
from core.analysis.analysis_models import AnalysisResult
from core.generation.meta_prompt_builder import build_meta_prompt
from core.generation.context_retriever import retrieve_context
from core.generation.quality_scorer import score_quality

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

QUALITY_THRESHOLD = 0.7
MAX_RETRIES       = 1


GENERATION_SYSTEM_PROMPT = """You are a senior technical writer producing professional software documentation.
You will be given:
1. A specific documentation section to write
2. Relevant source code context extracted from the actual codebase

Rules:
- Write ONLY the content for the requested section. Do not add a preamble or meta-commentary.
- Base everything on the provided code context. Do not invent details not present in the code.
- Use proper markdown: headers (##, ###), code blocks (```), bullet points, and tables where appropriate.
- Be specific — reference actual function names, class names, routes, and file paths from the context.
- Write for a technical audience (developers and architects).
- Minimum 300 words. Be thorough."""


def generate_section(
    project_id:   str,
    section_name: str,
    analysis:     AnalysisResult,
) -> dict:
    """
    Generates content for a single documentation section.

    Returns:
        {
            "section_name":  str,
            "content":       str,
            "quality_score": float,
            "regenerated":   bool,
            "status":        "success" | "low_quality" | "failed",
        }
    """
    print(f"📝 [Generator] Starting: '{section_name}'")

    meta    = build_meta_prompt(section_name, analysis)
    context = retrieve_context(project_id, meta["query"])

    if not context:
        print(f"⚠️  [Generator] No context found for '{section_name}'")
        return {
            "section_name":  section_name,
            "content":       "",
            "quality_score": 0.0,
            "regenerated":   False,
            "status":        "failed",
        }

    content = _call_groq(section_name, meta["instruction"], context)
    score   = score_quality(section_name, content)

    print(f"📊 [Generator] '{section_name}' — quality score: {score}")

    regenerated = False

    if score < QUALITY_THRESHOLD:
        print(f"🔁 [Generator] Score {score} below threshold. Regenerating '{section_name}'...")
        improved_instruction = (
            f"{meta['instruction']}\n\n"
            "IMPORTANT: The previous attempt scored poorly. "
            "Ensure you: use markdown headers, include specific code references, "
            "write at least 300 words, and cover the topic thoroughly."
        )
        content     = _call_groq(section_name, improved_instruction, context)
        score       = score_quality(section_name, content)
        regenerated = True
        print(f"📊 [Generator] '{section_name}' after regen — quality score: {score}")

    status = "success" if score >= QUALITY_THRESHOLD else "low_quality"

    return {
        "section_name":  section_name,
        "content":       content,
        "quality_score": score,
        "regenerated":   regenerated,
        "status":        status,
    }


def _call_groq(section_name: str, instruction: str, context: str) -> str:
    user_message = f"""Section to write: {section_name}

Instruction: {instruction}

Relevant code context from the codebase:
---
{context}
---

Write the '{section_name}' section now:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.4,
            max_tokens=4096,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ [Generator] Groq call failed for '{section_name}': {e}")
        return ""
