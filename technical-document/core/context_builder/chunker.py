import os
from typing import List
import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")


def _tokenize(text: str) -> List[int]:
    return ENCODING.encode(text)


def _detokenize(tokens: List[int]) -> str:
    return ENCODING.decode(tokens)


def _count_lines_before(lines: List[str], char_index: int) -> int:
    return len("".join(lines)[:char_index].splitlines())


def chunk_single_file(
    filepath: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[dict]:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return []

    if not content.strip():
        return []

    tokens = _tokenize(content)
    chunks = []
    start = 0
    lines = content.splitlines(keepends=True)
    chunk_index = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _detokenize(chunk_tokens)

        # Estimate start line number
        preceding_tokens = tokens[:start]
        preceding_text = _detokenize(preceding_tokens)
        start_line = preceding_text.count("\n") + 1
        end_line = start_line + chunk_text.count("\n")

        chunks.append({
            "chunk_id": f"{filepath}::chunk_{chunk_index}",
            "file_path": filepath,
            "text": chunk_text,
            "start_line": start_line,
            "end_line": end_line,
            "token_count": len(chunk_tokens),
            "raptor_level": 0,  # Raw chunk = level 0
        })

        chunk_index += 1
        start += chunk_size - overlap

    return chunks


def chunk_files(
    filepaths: List[str],
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[dict]:
    all_chunks = []
    for filepath in filepaths:
        all_chunks.extend(chunk_single_file(filepath, chunk_size, overlap))
    return all_chunks