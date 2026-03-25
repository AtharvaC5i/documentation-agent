from pydantic import BaseModel
from enum import Enum


class ContextStrategy(str, Enum):
    FLAT = "flat"
    RAPTOR = "raptor"


class ContextBuildRequest(BaseModel):
    project_id: str


class ContextBuildResponse(BaseModel):
    project_id: str
    strategy: ContextStrategy
    total_chunks: int
    total_loc: int
    vector_db_size_mb: float
    message: str