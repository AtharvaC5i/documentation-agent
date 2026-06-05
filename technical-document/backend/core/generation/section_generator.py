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

ENDPOINT = os.getenv("DATABRICKS_ENDPOINT_NAME")
QUALITY_THRESHOLD = 0.7
MAX_RETRIES = 1

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
    project_id: str,
    section_name: str,
    analysis: AnalysisResult,
) -> dict:
    print(f"📝 [Generator] Starting: '{section_name}'")

    meta = build_meta_prompt(section_name, analysis)
    context = retrieve_context(project_id, meta["query"])

    if not context:
        print(f"⚠️  [Generator] No context found for '{section_name}'")
        return {
            "section_name": section_name,
            "content": "",
            "quality_score": 0.0,
            "regenerated": False,
            "status": "failed",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
            },
        }

    content, usage = _call_llm(section_name, meta["instruction"], context)
    score = score_quality(section_name, content)

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
        regen_content, regen_usage = _call_llm(section_name, improved_instruction, context)

        usage = {
            "prompt_tokens": usage["prompt_tokens"] + regen_usage["prompt_tokens"],
            "completion_tokens": usage["completion_tokens"] + regen_usage["completion_tokens"],
        }

        content = regen_content
        score = score_quality(section_name, content)
        regenerated = True
        print(f"📊 [Generator] '{section_name}' after regen — quality score: {score}")

    status = "success" if score >= QUALITY_THRESHOLD else "low_quality"

    return {
        "section_name": section_name,
        "content": content,
        "quality_score": score,
        "regenerated": regenerated,
        "status": status,
        "usage": usage,
    }


def _call_llm(section_name: str, instruction: str, context: str) -> tuple[str, dict]:
    """
    Returns (content, usage_dict).
    usage_dict always has prompt_tokens and completion_tokens — zeros on failure.
    """
    user_message = f"""Section to write: {section_name}

Instruction: {instruction}

Relevant code context from the codebase:
---
{context}
---

Write the '{section_name}' section now:"""

    empty_usage = {"prompt_tokens": 0, "completion_tokens": 0}

    try:
        response = client.chat.completions.create(
            model=ENDPOINT,
            messages=[
                {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            max_tokens=4096,
        )
        usage = empty_usage
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(response.usage, "completion_tokens", 0) or 0,
            }
        elif isinstance(response, dict) and response.get("usage"):
            usage = {
                "prompt_tokens": response["usage"].get("prompt_tokens", 0),
                "completion_tokens": response["usage"].get("completion_tokens", 0),
            }

        # response.choices is a list — access the first choice
        if isinstance(response.choices, list) and len(response.choices) > 0:
            choice = response.choices[0]
        else:
            choice = response.choices

        if hasattr(choice, "message"):
            return choice.message.content.strip(), usage

        if isinstance(choice, dict):
            return choice["message"]["content"].strip(), usage

        if isinstance(choice, str):
            return choice.strip(), usage

        # Fallback should never happen if LLM response is valid
        print(f"⚠️  [Generator] Unexpected choice format for '{section_name}': {type(choice)}")
        return "", usage

    except Exception as e:
        print(f"❌ [Generator] Databricks call failed for '{section_name}': {e}")
        return "", empty_usage