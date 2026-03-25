import chromadb
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
CHROMA_DIR  = os.path.join(STORAGE_DIR, "chroma_db")
MAX_TOKENS_APPROX = 5000   # ~4 chars per token
MAX_CHUNKS        = 10


def get_chroma_collection(project_id: str):
    db_path = os.path.join(CHROMA_DIR, project_id)
    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"No vector store found for project '{project_id}'. "
            "Run context building first."
        )
    client     = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name=f"project_{project_id}")
    return collection


def retrieve_context(project_id: str, query: str, n_results: int = MAX_CHUNKS) -> str:
    """
    Queries ChromaDB for the most relevant chunks for a given query.
    Returns a single string of concatenated chunks, capped at MAX_TOKENS_APPROX.
    """
    collection = get_chroma_collection(project_id)

    total_docs = collection.count()
    if total_docs == 0:
        return ""

    safe_n = min(n_results, total_docs)

    results = collection.query(
        query_texts=[query],
        n_results=safe_n,
        include=["documents", "metadatas"],
    )

    chunks    = results["documents"][0]
    metadatas = results["metadatas"][0]

    context_parts = []
    total_chars   = 0
    char_limit    = MAX_TOKENS_APPROX * 4

    for chunk, meta in zip(chunks, metadatas):
        file_path = meta.get("file_path", "unknown")
        header    = f"# File: {file_path}\n"
        block     = header + chunk + "\n\n"

        if total_chars + len(block) > char_limit:
            break

        context_parts.append(block)
        total_chars += len(block)

    return "".join(context_parts)
