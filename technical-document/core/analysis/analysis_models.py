from pydantic import BaseModel
from typing import List


class AnalysisResult(BaseModel):
    languages:           List[str] = []
    frameworks:          List[str] = []
    databases:           List[str] = []
    test_frameworks:     List[str] = []
    has_dockerfile:      bool      = False
    has_cicd:            bool      = False
    has_kubernetes:      bool      = False
    has_terraform:       bool      = False
    has_ansible:         bool      = False
    api_endpoints_count: int       = 0
    total_loc:           int       = 0
