import os
from typing import List
import chromadb
from dotenv import load_dotenv
load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
CHROMA_DIR  = os.path.join(STORAGE_DIR, "chroma_db")


def _get_client(project_id: str):
    persist_path = os.path.join(CHROMA_DIR, project_id)
    os.makedirs(persist_path, exist_ok=True)
    return chromadb.PersistentClient(path=persist_path)


def store_chunks(embedded_chunks: List[dict], project_id: str) -> None:
    client = _get_client(project_id)
    collection = client.get_or_create_collection(
        name=f"project_{project_id}",
        metadata={"hnsw:space": "cosine"},
    )

    ids        = [chunk["chunk_id"]   for chunk in embedded_chunks]
    embeddings = [chunk["embedding"]  for chunk in embedded_chunks]
    documents  = [chunk["text"]       for chunk in embedded_chunks]
    metadatas  = [
        {
            "file_path":    chunk["file_path"],
            "start_line":   chunk["start_line"],
            "end_line":     chunk["end_line"],
            "token_count":  chunk["token_count"],
            "raptor_level": chunk.get("raptor_level", 0),
        }
        for chunk in embedded_chunks
    ]

    batch_size = 500
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )


def query_collection(
    project_id: str,
    query_embedding: List[float],
    n_results: int = 10,
    raptor_level: int = 0,
) -> List[dict]:
    client     = _get_client(project_id)
    collection = client.get_or_create_collection(name=f"project_{project_id}")

    where_filter = {"raptor_level": {"$eq": raptor_level}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({"text": doc, "metadata": meta, "distance": dist})

    return chunks
