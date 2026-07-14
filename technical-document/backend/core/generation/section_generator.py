import os
import re
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


def prune_code_context(context: str) -> str:
    """
    Prunes code context by:
    - Stripping trivial standard imports (os, sys, json, time, etc.)
    - Collapsing multiple empty lines
    - Stripping long comments or boilerplate
    """
    lines = context.split("\n")
    pruned_lines = []
    in_docstring = False
    docstring_delim = None
    
    trivial_imports = {"os", "sys", "json", "time", "typing", "datetime", "uuid", "math", "re", "collections"}
    
    for line in lines:
        stripped = line.strip()
        
        # Docstring checks
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not in_docstring:
                in_docstring = True
                docstring_delim = '"""' if stripped.startswith('"""') else "'''"
                if len(stripped) > 3 and not stripped.endswith(docstring_delim):
                    pruned_lines.append(line)
                continue
            else:
                if stripped.endswith(docstring_delim):
                    in_docstring = False
                    continue
        if in_docstring:
            continue
            
        # Skip import lines that are trivial standard library imports
        if stripped.startswith("import ") or stripped.startswith("from "):
            parts = re.split(r'\s+', stripped)
            if len(parts) >= 2:
                import_name = parts[1].split(".")[0]
                if import_name in trivial_imports:
                    continue
                    
        # Skip purely comment lines (but keep file path headers)
        if stripped.startswith("#") and not stripped.startswith("# File:"):
            continue
            
        pruned_lines.append(line)
        
    result = "\n".join(pruned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


def active_retrieve_context(project_id: str, query: str, analysis: AnalysisResult) -> str:
    """
    Retrieves initial context, scans for file imports, and recursively fetches
    chunks from dependencies (Agentic RAG).
    """
    context = retrieve_context(project_id, query)
    
    # Find import declarations
    import_paths = re.findall(r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)', context)
    
    additional_contexts = []
    seen_files = set()
    
    # Identify what files we already retrieved in initial context
    for filepath in re.findall(r'# File:\s*(.+)', context):
        seen_files.add(filepath.strip())
        
    for path in import_paths:
        path_str = path.replace(".", "/")
        if path in {"os", "sys", "json", "time", "typing", "datetime", "uuid", "math", "re", "collections", "fastapi", "pydantic"}:
            continue
            
        import_query = f"file path {path_str} implementation"
        imp_context = retrieve_context(project_id, import_query, n_results=2)
        
        # Extract files in imp_context
        for filepath in re.findall(r'# File:\s*(.+)', imp_context):
            filepath = filepath.strip()
            if filepath not in seen_files:
                additional_contexts.append(imp_context)
                seen_files.add(filepath)
                break
                
    if additional_contexts:
        print(f"🔗 [Active Retrieval] Fetched {len(additional_contexts)} dependency contexts dynamically")
        context = context + "\n\n=== DEPENDENT CODE CONTEXT ===\n" + "\n".join(additional_contexts)
        
    return context


def verify_ast_grounding(section_name: str, content: str, project_id: str) -> str:
    """
    Validates generated class names, function names, and API route endpoints
    against actual code chunks to catch hallucinations.
    """
    routes = re.findall(r'/\w+(?:/\w+)+', content)
    classes = re.findall(r'class\s+([A-Z][a-zA-Z0-9_]+)', content)
    functions = re.findall(r'def\s+([a-z_][a-z0-9_]+)', content)
    
    hallucinations = []
    collection = None
    try:
        from core.generation.context_retriever import get_chroma_collection
        collection = get_chroma_collection(project_id)
    except Exception:
        pass
        
    if collection and collection.count() > 0:
        for r in routes[:4]:
            res = collection.query(query_texts=[r], n_results=1)
            if not res["documents"][0] or r not in res["documents"][0][0]:
                hallucinations.append(f"Route '{r}'")
                
        for f in functions[:4]:
            res = collection.query(query_texts=[f], n_results=1)
            if not res["documents"][0] or f not in res["documents"][0][0]:
                hallucinations.append(f"Function/Method '{f}'")
                
    if hallucinations:
        print(f"⚠️ [AST Validator] Found potential hallucinations: {hallucinations}")
        disclaimer = "\n\n> [!WARNING]\n> **Validator Note**: The following references in this section could not be strictly verified in the codebase: " + ", ".join(hallucinations) + ". Please double-check these names in your final review."
        content += disclaimer
        
    return content


def generate_section(
    project_id: str,
    section_name: str,
    analysis: AnalysisResult,
) -> dict:
    print(f"📝 [Generator] Starting: '{section_name}'")

    meta = build_meta_prompt(section_name, analysis)
    raw_context = active_retrieve_context(project_id, meta["query"], analysis)
    context = prune_code_context(raw_context)

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
    
    if content:
        content = verify_ast_grounding(section_name, content, project_id)
        
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
        if content:
            content = verify_ast_grounding(section_name, content, project_id)
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

    # Semantic Cache lookup
    from core.utils.semantic_cache import get_cache, set_cache
    cached_val = get_cache(GENERATION_SYSTEM_PROMPT, user_message)
    if cached_val is not None:
        return cached_val, empty_usage

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

        content = ""
        if hasattr(choice, "message"):
            content = choice.message.content.strip()
        elif isinstance(choice, dict):
            content = choice["message"]["content"].strip()
        elif isinstance(choice, str):
            content = choice.strip()

        if content:
            set_cache(GENERATION_SYSTEM_PROMPT, user_message, content)
            return content, usage

        print(f"⚠️  [Generator] Unexpected choice format for '{section_name}': {type(choice)}")
        return "", usage

    except Exception as e:
        print(f"❌ [Generator] Databricks call failed for '{section_name}': {e}")
        return "", empty_usage