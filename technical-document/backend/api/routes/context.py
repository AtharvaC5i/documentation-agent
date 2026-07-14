import os
import time

from fastapi import APIRouter, HTTPException

from api.schemas.context_schema import ContextBuildRequest, ContextBuildResponse, ContextStrategy
from core.context_builder.chunker import chunk_files
from core.context_builder.embedder import embed_chunks
from core.context_builder.vector_store import store_chunks
from core.context_builder.raptor_builder import build_raptor_tree
from core.state_store import get_project, update_project, get_collector

from dotenv import load_dotenv
load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
CHROMA_DIR = os.path.join(STORAGE_DIR, "chroma_db")

router = APIRouter()
LOC_THRESHOLD = 50_000


@router.post("/build", response_model=ContextBuildResponse)
def build_context(request: ContextBuildRequest):
    project = get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{request.project_id}' not found.")

    collector = get_collector(request.project_id)
    filtered_files = project["filtered_files"]
    total_loc = project["analysis"]["total_loc"]
    strategy = ContextStrategy.RAPTOR if total_loc > LOC_THRESHOLD else ContextStrategy.FLAT

    t_start = time.perf_counter()
    try:
        chunks = chunk_files(filtered_files, chunk_size=500, overlap=50)
        raptor_nodes = 0
        if strategy == ContextStrategy.RAPTOR:
            chunks = build_raptor_tree(chunks, project_id=request.project_id)
            raptor_nodes = max(0, len(chunks) - len(filtered_files))

        embedded_chunks = embed_chunks(chunks)
        store_chunks(embedded_chunks, project_id=request.project_id)

        embedding_duration = time.perf_counter() - t_start

        chroma_path = os.path.join(CHROMA_DIR, request.project_id)
        db_size_mb = round(
            sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, filenames in os.walk(chroma_path)
                for f in filenames
            ) / (1024 * 1024), 2,
        )

        collector.record_context_building(
            total_chunks=len(chunks),
            strategy=strategy.value,
            embedding_duration_seconds=embedding_duration,
            vector_store_size_mb=db_size_mb,
            raptor_summary_nodes=raptor_nodes,
            context_building_duration_seconds=embedding_duration,
        )
    except Exception as e:
        collector.record_error(
            stage="context_building",
            message=str(e),
            error_type="embedding" if "embed" in str(e).lower() or "vector" in str(e).lower() else "runtime",
            exception_type=type(e).__name__,
        )
        raise HTTPException(status_code=500, detail=f"Context build failed: {str(e)}")

    update_project(request.project_id, "strategy", strategy.value)   # ← also fixed here for consistency
    update_project(request.project_id, "total_chunks", len(chunks))
    update_project(request.project_id, "context_built", True)

    return ContextBuildResponse(
        project_id=request.project_id,
        strategy=strategy,
        total_chunks=len(chunks),
        total_loc=total_loc,
        vector_db_size_mb=db_size_mb,
        message=f"Context built using '{strategy.value}' strategy. {len(chunks)} chunks stored in ChromaDB.",
    )