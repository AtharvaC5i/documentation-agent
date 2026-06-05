from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any

from core.reporting.report_builder import build_report, export_report_xlsx
from core.state_store import get_collector

router = APIRouter(prefix="/report", tags=["report"])


class ReportRequest(BaseModel):
    metadata: Dict[str, Any]


@router.post("/{project_id}")
def get_report(project_id: str, body: ReportRequest):
    try:
        report = build_report(project_id, body.metadata)

        try:
            collector = get_collector(project_id)
            metrics_path = collector.save(status="success")
            print(f"📊 [report.py] Metrics written to: {metrics_path}")
        except Exception as metrics_err:
            print(f"⚠️ [report.py] Metrics save failed (non-blocking): {metrics_err}")

        return report
    except Exception as e:
        try:
            collector = get_collector(project_id)
            collector.save(status="failure")
        except Exception:
            pass
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