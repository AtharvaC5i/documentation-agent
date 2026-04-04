from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    brd_text: str = Field(..., description="Business Requirement Document text content")
    tech_doc_text: Optional[str] = Field(
        default="", description="Optional Technical Documentation text content"
    )
