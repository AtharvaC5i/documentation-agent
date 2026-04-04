import os
from openai import OpenAI
from dotenv import load_dotenv
from core.analysis.analysis_models import AnalysisResult
from core.generation.meta_prompt_builder import build_meta_prompt
from core.generation.context_retriever import retrieve_context
from core.generation.quality_scorer import score_quality

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DATABRICKS_TOKEN"),
    base_url=f"{os.getenv('DATABRICKS_HOST')}/serving-endpoints",
)

ENDPOINT          = os.getenv("DATABRICKS_ENDPOINT_NAME")
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

    content = _call_llm(section_name, meta["instruction"], context)
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
        content     = _call_llm(section_name, improved_instruction, context)
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


def _call_llm(section_name: str, instruction: str, context: str) -> str:
    user_message = f"""Section to write: {section_name}

Instruction: {instruction}

Relevant code context from the codebase:
---
{context}
---

Write the '{section_name}' section now:"""

    try:
        response = client.chat.completions.create(
            model=ENDPOINT,
            messages=[
                {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.4,
            max_tokens=4096,
        )
        print(f"DEBUG response type: {type(response)}")
        print(f"DEBUG choices[0] type: {type(response.choices[0])}")
        print(f"DEBUG choices[0]: {response.choices[0]}")

        # Handle both response formats
        choice = response.choices[0]

        # Format 1: Standard OpenAI object — choice.message.content
        if hasattr(choice, "message"):
            return choice.message.content.strip()

        # Format 2: Databricks dict — choice["message"]["content"]
        if isinstance(choice, dict):
            return choice["message"]["content"].strip()

        # Format 3: Raw string
        if isinstance(choice, str):
            return choice.strip()

        return str(choice).strip()

    except Exception as e:
        print(f"❌ [Generator] Databricks call failed for '{section_name}': {e}")
        return ""