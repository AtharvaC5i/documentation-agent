"""
RAPTOR Hierarchical Tree Builder
─────────────────────────────────
Used when codebase > 50,000 LOC.
Builds a 4-level hierarchy:
  Level 0 → Raw 500-token code chunks (leaf nodes)
  Level 1 → Module-level summaries (chunks grouped by file)
  Level 2 → Feature/domain summaries (grouped by directory)
  Level 3 → Single system-level overview summary

Summaries at levels 1–3 are generated via Groq (Llama 3.1).
All levels are stored in ChromaDB with a 'raptor_level' metadata field.
"""

import os
from typing import List
from groq import Groq
from dotenv import load_dotenv
from core.context_builder.embedder import _get_model

load_dotenv()

_groq_client = None


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


def _summarize(text: str, context: str = "") -> str:
    prompt = (
        f"You are a senior software engineer. Summarize the following code"
        f"{' (' + context + ')' if context else ''} "
        f"in 3-5 concise technical sentences. Focus on purpose, inputs, outputs, and dependencies.\n\n"
        f"```\n{text[:3000]}\n```"
    )
    response = _get_groq().chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def build_raptor_tree(level0_chunks: List[dict], project_id: str) -> List[dict]:
    """
    Takes Level 0 chunks and builds Levels 1, 2, 3 summaries.
    Returns all chunks (L0 + L1 + L2 + L3) ready for embedding + storage.
    """
    model = _get_model()
    all_chunks = list(level0_chunks)

    # ── Level 1: File-level summaries ─────────────────────────────────────
    file_groups: dict[str, List[dict]] = {}
    for chunk in level0_chunks:
        fp = chunk["file_path"]
        file_groups.setdefault(fp, []).append(chunk)

    level1_chunks = []
    for filepath, chunks in file_groups.items():
        combined_text = "\n".join(c["text"] for c in chunks)
        filename = os.path.basename(filepath)
        summary = _summarize(combined_text, context=f"file: {filename}")
        embedding = model.encode([summary], normalize_embeddings=True)[0].tolist()
        level1_chunks.append({
            "chunk_id": f"{project_id}::L1::{filepath}",
            "file_path": filepath,
            "text": summary,
            "start_line": 0,
            "end_line": 0,
            "token_count": len(summary.split()),
            "raptor_level": 1,
            "embedding": embedding,
        })

    all_chunks.extend(level1_chunks)

    # ── Level 2: Directory-level summaries ────────────────────────────────
    dir_groups: dict[str, List[dict]] = {}
    for chunk in level1_chunks:
        dir_name = os.path.dirname(chunk["file_path"])
        dir_groups.setdefault(dir_name, []).append(chunk)

    level2_chunks = []
    for dir_path, chunks in dir_groups.items():
        combined_text = "\n".join(c["text"] for c in chunks)
        dir_label = os.path.basename(dir_path) or "root"
        summary = _summarize(combined_text, context=f"module: {dir_label}")
        embedding = model.encode([summary], normalize_embeddings=True)[0].tolist()
        level2_chunks.append({
            "chunk_id": f"{project_id}::L2::{dir_path}",
            "file_path": dir_path,
            "text": summary,
            "start_line": 0,
            "end_line": 0,
            "token_count": len(summary.split()),
            "raptor_level": 2,
            "embedding": embedding,
        })

    all_chunks.extend(level2_chunks)

    # ── Level 3: System-level overview ────────────────────────────────────
    combined_l2 = "\n".join(c["text"] for c in level2_chunks)
    system_summary = _summarize(combined_l2, context="entire system")
    embedding = model.encode([system_summary], normalize_embeddings=True)[0].tolist()
    level3_chunk = {
        "chunk_id": f"{project_id}::L3::system_overview",
        "file_path": "system",
        "text": system_summary,
        "start_line": 0,
        "end_line": 0,
        "token_count": len(system_summary.split()),
        "raptor_level": 3,
        "embedding": embedding,
    }
    all_chunks.append(level3_chunk)

    return all_chunks