"""
Living BRD — Change Detection Feature.

When a new transcript is uploaded to an existing completed project:
1. Extract requirements from the new transcript
2. Diff against existing Requirements Pool
3. Classify changes: new | modified | removed | conflict_with_existing
4. Generate a human-readable change report
5. On approval — merge changes, increment version, snapshot old state
"""

import uuid
from typing import List, Dict, Any, Tuple
from datetime import datetime

from models.project import Project, ProjectStore, Requirement
from utils.databricks_client import call_databricks_llm, parse_llm_json
from utils.logger import info, success, warn, divider, llm_call, llm_response


async def detect_changes(
    project: Project,
    new_requirements: List[Requirement],
) -> List[Dict[str, Any]]:
    """
    Compare new_requirements against project.requirements_pool.
    Returns a list of change objects.
    """
    divider("LIVING BRD — CHANGE DETECTION")

    existing_by_id = {r.req_id: r for r in project.requirements_pool}
    new_by_id = {r.req_id: r for r in new_requirements}

    existing_descriptions = [r.description for r in project.requirements_pool]
    new_descriptions = [r.description for r in new_requirements]

    # Ask LLM to semantically compare the two sets
    existing_summary = "\n".join(
        f"[{r.req_id}] {r.description[:120]}" for r in project.requirements_pool[:60]
    )
    new_summary = "\n".join(
        f"[{r.req_id}] {r.description[:120]}" for r in new_requirements[:60]
    )

    system_prompt = """You are a requirements change analyst.
Compare two sets of requirements and identify all changes.

For each change, output a JSON object:
{
  "change_id": "CHG-001",
  "change_type": "new|modified|removed|conflict",
  "req_id": "TR-XXX or US-XXX",
  "description": "what changed in one sentence",
  "old_text": "old requirement text or null",
  "new_text": "new requirement text or null",
  "impact": "high|medium|low",
  "affected_sections": ["Section Name 1", "Section Name 2"]
}

change_type meanings:
- new: requirement exists in new set but not old
- modified: similar requirement exists in both but wording/scope changed
- removed: requirement existed before but not in new set
- conflict: new requirement directly contradicts an existing one

Return a JSON array of ALL changes. Return [] if no changes."""

    user_prompt = f"""EXISTING requirements (current BRD v{project.version}):
{existing_summary}

NEW requirements (from latest transcript):
{new_summary}

Identify all changes."""

    llm_call("LIVING BRD", "Change detection", len(user_prompt))
    raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=4000, json_mode=True)
    llm_response("LIVING BRD", len(raw))

    data = parse_llm_json(raw)
    changes = data if isinstance(data, list) else data.get("changes", [])

    # Add IDs if missing
    for i, c in enumerate(changes):
        if not c.get("change_id"):
            c["change_id"] = f"CHG-{str(i+1).zfill(3)}"
        c["status"] = "pending"  # pending | approved | rejected

    new_count = sum(1 for c in changes if c["change_type"] == "new")
    mod_count = sum(1 for c in changes if c["change_type"] == "modified")
    rem_count = sum(1 for c in changes if c["change_type"] == "removed")
    con_count = sum(1 for c in changes if c["change_type"] == "conflict")

    info("LIVING BRD", f"Changes detected — new: {new_count} | modified: {mod_count} | removed: {rem_count} | conflicts: {con_count}")
    return changes


async def generate_change_report(project: Project, changes: List[Dict]) -> str:
    """Generate a concise human-readable change summary."""
    if not changes:
        return "No changes detected between the new transcript and the existing BRD."

    changes_text = "\n".join(
        f"- [{c['change_type'].upper()}] {c['description']}"
        for c in changes
    )

    system_prompt = """You are a project manager writing a change summary for a BRD update.
Write a professional 150-200 word summary of what changed and what sections will need updating.
Be specific about business impact. Write in plain English for a non-technical audience."""

    user_prompt = f"""Project: {project.project_name}
Previous BRD version: v{project.version}

Changes detected from new meeting transcript:
{changes_text}

Write the change summary."""

    llm_call("LIVING BRD", "Change report generation")
    raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=1000, temperature=0.3)
    llm_response("LIVING BRD", len(raw))
    return raw


def apply_approved_changes(project: Project, approved_change_ids: List[str]) -> Project:
    """
    Merge approved changes into the project.
    Snapshots current state as a previous version first.
    """
    divider(f"APPLYING CHANGES — bumping to v{project.version + 1}")

    # 1. Snapshot current state
    snapshot = {
        "version": project.version,
        "created_at": datetime.now().isoformat(),
        "document_path": project.document_path,
        "requirement_ids": [r.req_id for r in project.requirements_pool],
        "section_names": [s.get("name", "") for s in project.generated_sections],
        "change_summary": project.change_report,
    }
    project.previous_versions.append(snapshot)

    # 2. Apply approved changes to requirements pool
    approved_changes = [c for c in project.pending_changes if c["change_id"] in approved_change_ids]
    pool_by_id = {r.req_id: r for r in project.requirements_pool}

    for change in approved_changes:
        ct = change["change_type"]
        rid = change.get("req_id", "")

        if ct == "removed" and rid in pool_by_id:
            del pool_by_id[rid]

        elif ct in ("new", "modified") and change.get("new_text"):
            if rid in pool_by_id:
                # Update existing
                pool_by_id[rid].description = change["new_text"]
                pool_by_id[rid].added_in_version = project.version + 1
            else:
                # Add new requirement
                pool_by_id[rid] = Requirement(
                    req_id=rid or f"TR-NEW-{uuid.uuid4().hex[:4]}",
                    type="functional",
                    description=change["new_text"],
                    source="transcript",
                    added_in_version=project.version + 1,
                )

    project.requirements_pool = list(pool_by_id.values())

    # 3. Bump version and clear pending
    project.version += 1
    project.pending_changes = []
    project.change_report = None
    project.status = "extracted"  # ready for re-generation of affected sections

    success("LIVING BRD", f"Changes applied. Project is now v{project.version}")
    return project
