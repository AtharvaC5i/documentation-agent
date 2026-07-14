from pydantic import BaseModel, Field
from typing import Optional
from models.metrics_models import AcceptanceStatusEnum


class GenerateRequest(BaseModel):
    brd_text: str = Field(..., description="Business Requirement Document text content")
    tech_doc_text: Optional[str] = Field(
        default="", description="Optional Technical Documentation text content"
    )


class ReviewRequest(BaseModel):
    run_id: str = Field(..., description="The run identifier for the metrics payload")
    acceptance_status: AcceptanceStatusEnum = Field(..., description="The user review decision")

