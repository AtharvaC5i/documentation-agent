from pydantic import BaseModel, Field
from typing import List, Dict


class SectionSuggestion(BaseModel):
    name: str
    selected: bool
    reason: str


class SectionSuggestionsResponse(BaseModel):
    project_id: str
    suggestions: List[SectionSuggestion]


class SectionConfirmRequest(BaseModel):
    project_id: str
    confirmed_sections: List[str] = Field(
        ..., description="Ordered list of section names to generate"
    )
    custom_sections: List[str] = Field(
        default_factory=list,
        description="Any user-defined custom section titles",
    )


class SectionConfirmResponse(BaseModel):
    project_id: str
    final_sections: List[str]
    message: str