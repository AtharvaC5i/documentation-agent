from typing import List
from sentence_transformers import SentenceTransformer

# all-MiniLM-L6-v2: ~80MB, fast on CPU, excellent for code + prose
_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_chunks(chunks: List[dict], batch_size: int = 64) -> List[dict]:
    """
    Generates embeddings for each chunk using Sentence Transformers (CPU).
    Adds an 'embedding' field to each chunk dict in-place.
    """
    model = _get_model()
    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    return chunks