import os
import smtplib
import json
from pathlib import Path
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

STORAGE_DIR   = os.getenv("STORAGE_DIR",  os.path.join("..", "storage"))
SMTP_HOST     = os.getenv("SMTP_HOST",    "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER",    "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM     = os.getenv("SMTP_FROM",    SMTP_USER)


def _publish_log_path(project_id: str) -> Path:
    return Path(STORAGE_DIR) / "projects" / project_id / "publish_log.json"


def _load_log(project_id: str) -> dict:
    path = _publish_log_path(project_id)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"published": False, "deliveries": []}


def _save_log(project_id: str, log: dict):
    path = _publish_log_path(project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, indent=2)


def send_email(
    project_id:   str,
    project_name: str,
    docx_path:    str,
    recipients:   List[str],
    subject:      Optional[str] = None,
    message:      Optional[str] = None,
) -> dict:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD in .env.")

    docx_file = Path(docx_path)
    if not docx_file.exists():
        raise FileNotFoundError(f"Document not found at: {docx_path}")

    subject = subject or f"Technical Documentation — {project_name}"
    message = message or (
        f"Please find attached the generated technical documentation for {project_name}.\n\n"
        "This document was generated automatically by DocAgent."
    )

    msg = MIMEMultipart()
    msg["From"]    = SMTP_FROM
    msg["To"]      = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    with open(docx_file, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{docx_file.name}"',
    )
    msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, recipients, msg.as_string())

    log = _load_log(project_id)
    log["published"] = True
    log["deliveries"].append({
        "method":     "email",
        "recipients": recipients,
        "subject":    subject,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    })
    _save_log(project_id, log)

    return {
        "success":    True,
        "recipients": recipients,
        "timestamp":  log["deliveries"][-1]["timestamp"],
    }


def get_publish_status(project_id: str) -> dict:
    return _load_log(project_id)