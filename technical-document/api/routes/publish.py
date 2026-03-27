from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from core.publish.email_publisher import send_email, get_publish_status

router = APIRouter(prefix="/publish", tags=["publish"])


class EmailRequest(BaseModel):
    project_name: str
    docx_path:    str
    recipients:   List[str]
    subject:      Optional[str] = None
    message:      Optional[str] = None


@router.post("/{project_id}/email")
def publish_email(project_id: str, body: EmailRequest):
    if not body.recipients:
        raise HTTPException(status_code=400, detail="At least one recipient is required.")
    try:
        result = send_email(
            project_id   = project_id,
            project_name = body.project_name,
            docx_path    = body.docx_path,
            recipients   = body.recipients,
            subject      = body.subject,
            message      = body.message,
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email delivery failed: {str(e)}")


@router.get("/{project_id}/status")
def publish_status(project_id: str):
    return get_publish_status(project_id)