from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class SourceType(str, Enum):
    GITHUB = "github"
    ZIP    = "zip"


class ProjectMetadata(BaseModel):
    project_name:  str       = Field(..., min_length=1, max_length=100)
    client_name:   str       = Field(..., min_length=1, max_length=100)
    team_members:  List[str] = Field(default_factory=list)
    description:   str       = Field(default="", max_length=1000)


class GithubIngestRequest(BaseModel):
    source_type:  SourceType       = SourceType.GITHUB
    github_url:   str              = Field(..., description="Full GitHub repository URL")
    github_token: Optional[str]    = Field(None, description="PAT — deleted immediately after clone")
    metadata:     ProjectMetadata

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        if not v.startswith("https://github.com/"):
            raise ValueError("Must be a valid GitHub repository URL.")
        return v.rstrip("/")


class IngestResponse(BaseModel):
    project_id:          str
    message:             str
    filtered_file_count: int
    total_loc:           int
    analysis:            dict
