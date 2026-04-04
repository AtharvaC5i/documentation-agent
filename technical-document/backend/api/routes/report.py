from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any

from core.reporting.report_builder import build_report, export_report_xlsx

router = APIRouter(prefix="/report", tags=["report"])


class ReportRequest(BaseModel):
    metadata: Dict[str, Any]


@router.post("/{project_id}")
def get_report(project_id: str, body: ReportRequest):
    try:
        return build_report(project_id, body.metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/export")
def export_report(project_id: str, body: ReportRequest):
    try:
        path = export_report_xlsx(project_id, body.metadata)
        return FileResponse(
            path=str(path),
            filename="run_report.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))