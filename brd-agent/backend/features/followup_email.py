"""
Automated Follow-Up Email Generator.

After conflict and gap analysis, generates a professional
client email with targeted questions for each coverage gap.

One LLM call. Output is a ready-to-send email draft.
"""

from typing import List, Dict, Any
from models.project import Project
from utils.databricks_client import call_databricks_llm
from utils.logger import info, success, llm_call, llm_response


async def generate_followup_email(project: Project) -> str:
    """
    Generate a follow-up email draft based on coverage gaps.
    Returns the email as a plain text string.
    """
    if not project.gaps:
        return "No coverage gaps detected — no follow-up questions needed."

    # Build targeted questions per gap
    # Group gaps by severity
    critical_gaps = [g for g in project.gaps if g.get("coverage_level") == "none"]
    weak_gaps = [g for g in project.gaps if g.get("coverage_level") == "weak"]

    # Pull out any unresolved conflicts to mention
    unresolved_conflicts = [c for c in project.conflicts if not c.get("resolved")]

    # Build stakeholder name from extracted stakeholders or fallback
    client_contact = "Team"
    if project.stakeholders:
        client_contact = project.stakeholders[0].get("name", "Team")

    # Identify client decision-maker from requirements pool
    for r in project.requirements_pool:
        if r.type == "stakeholder" and r.speaker:
            client_contact = r.speaker
            break

    critical_list = "\n".join(
        f"  - {g['section']}: {g['message']}" for g in critical_gaps[:8]
    )
    weak_list = "\n".join(
        f"  - {g['section']}: {g['message']}" for g in weak_gaps[:6]
    )
    conflict_list = "\n".join(
        f"  - {c['description']}" for c in unresolved_conflicts[:3]
    )

    system_prompt = """You are a senior Business Analyst writing a professional follow-up email to a client.

The email must:
1. Open with a brief, warm thank-you for the discovery call
2. Section 1 — CRITICAL CLARIFICATIONS NEEDED: questions for sections with zero coverage
3. Section 2 — CONFIRMATIONS NEEDED: questions for sections with weak/partial coverage
4. Section 3 — OPEN ITEMS (if any): unresolved contradictions that need client decision
5. Close professionally with a clear deadline request (suggest 5 business days)

Rules:
- Each question must be SPECIFIC to this project, not generic
- Reference actual topics from the meeting where possible
- Max 400 words total
- Professional but friendly tone
- Format as a proper email with Subject line, greeting, body, sign-off"""

    user_prompt = f"""Project: {project.project_name}
Client: {project.client_name}
Client contact: {client_contact}
Our team: {', '.join(project.team_members) or 'Project Team'}

CRITICAL gaps — these sections have NO coverage and block BRD completion:
{critical_list if critical_list else 'None'}

WEAK coverage — these sections have partial information needing confirmation:
{weak_list if weak_list else 'None'}

UNRESOLVED CONFLICTS — client must decide:
{conflict_list if conflict_list else 'None'}

Write the follow-up email."""

    llm_call("EMAIL", "Follow-up email generation", len(user_prompt))
    raw = await call_databricks_llm(system_prompt, user_prompt, max_tokens=1500, temperature=0.3)
    llm_response("EMAIL", len(raw))

    success("EMAIL", "Follow-up email draft generated")
    return raw
