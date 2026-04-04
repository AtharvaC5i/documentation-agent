from typing import List
from core.analysis.analysis_models import AnalysisResult
from core.section_selector.section_registry import ALL_SECTIONS
from api.schemas.section_schema import SectionSuggestion


def suggest_sections(analysis: AnalysisResult) -> List[SectionSuggestion]:

    has_code      = analysis.total_loc > 0
    has_api       = analysis.api_endpoints_count > 0
    has_db        = len(analysis.databases) > 0
    has_tests     = len(analysis.test_frameworks) > 0
    fws           = set(analysis.frameworks)
    langs         = set(analysis.languages)
    stack_str     = " ".join(analysis.frameworks + analysis.languages).lower()

    has_web_fw    = bool(fws & {
        "fastapi", "flask", "django", "express", "nextjs", "nuxtjs",
        "nestjs", "spring", "rails", "laravel", "gin", "echo_go",
        "fiber", "actix", "axum", "rocket", "dotnet_mvc", "koa",
        "hapi", "fastify", "aiohttp", "tornado", "starlette",
        "litestar", "sanic",
    })
    has_frontend  = bool(fws & {
        "react", "vue", "angular", "svelte", "nextjs", "nuxtjs",
        "gatsby", "remix", "astro",
    })
    has_mobile    = bool(fws & {
        "flutter", "react_native", "expo", "ionic", "android",
    })
    has_ml        = bool(fws & {
        "tensorflow", "pytorch", "sklearn", "huggingface",
        "langchain", "langgraph", "openai",
    })
    has_deploy    = (
        analysis.has_dockerfile or analysis.has_kubernetes
        or analysis.has_terraform or analysis.has_ansible
        or "vite" in fws
    )
    has_infra     = (
        analysis.has_kubernetes or analysis.has_terraform or analysis.has_ansible
    )
    has_auth      = has_api or bool(fws & {
        "django", "spring", "fastapi", "nestjs", "dotnet_mvc",
        "laravel", "rails",
    })
    has_3p        = bool(fws & {
        "openai", "langchain", "langgraph", "huggingface",
        "celery", "aws_cdk", "pulumi", "graphql_js", "trpc",
        "prisma_js",
    })

    def fw_list(*keys):
        return ", ".join(f for f in analysis.frameworks
                         if f in set(keys)) or None

    rules = {
        "Executive Summary": (
            has_code,
            f"{analysis.total_loc:,} LOC across {', '.join(list(langs)[:3])}."
            if has_code else "No source code detected.",
        ),
        "Tech Stack Overview": (
            has_code,
            f"{len(langs)} language(s): {', '.join(sorted(langs)[:4])}. "
            f"{len(fws)} framework(s): {', '.join(sorted(fws)[:4])}."
            if has_code else "No stack detected.",
        ),
        "System Architecture": (
            has_code and (has_web_fw or has_frontend or has_mobile or len(langs) > 1),
            f"Multi-component system detected: {', '.join(sorted(langs)[:4])} "
            f"with {', '.join(sorted(fws)[:4])}."
            if has_code else "No architecture patterns detected.",
        ),
        "API Documentation": (
            has_api or has_web_fw,
            f"{analysis.api_endpoints_count} endpoint(s) detected. "
            f"Framework: {fw_list('fastapi','flask','django','express','spring','nestjs','gin','actix','axum','rails','laravel') or 'detected'}."
            if has_api else
            f"Web framework detected: {fw_list('fastapi','flask','django','express','spring','nestjs','koa','fastify','hapi','tornado','aiohttp','starlette')}."
            if has_web_fw else "No API endpoints or web framework found.",
        ),
        "Database Schema": (
            has_db,
            f"Detected: {', '.join(analysis.databases)}."
            if has_db else "No database libraries found.",
        ),
        "Authentication & Security": (
            has_auth,
            f"{analysis.api_endpoints_count} API endpoint(s) — auth & security documentation is essential."
            if has_api else
            f"Framework detected ({fw_list('django','spring','fastapi','nestjs','laravel','rails','dotnet_mvc')}) — auth section applicable."
            if has_auth else "No API or auth-related patterns detected.",
        ),
        "Deployment Guide": (
            has_deploy,
            " | ".join(filter(None, [
                "Dockerfile detected" if analysis.has_dockerfile else None,
                "Kubernetes manifests found" if analysis.has_kubernetes else None,
                "Terraform config found" if analysis.has_terraform else None,
                "Ansible playbooks found" if analysis.has_ansible else None,
                "Vite build config detected" if "vite" in fws else None,
            ])) + "."
            if has_deploy else "No deployment configuration found.",
        ),
        "CI/CD Pipeline": (
            analysis.has_cicd,
            "CI/CD configuration detected (GitHub Actions / GitLab CI / Jenkins / CircleCI / etc.)."
            if analysis.has_cicd else "No CI/CD configuration files found.",
        ),
        "Infrastructure & DevOps": (
            has_infra,
            " | ".join(filter(None, [
                "Kubernetes manifests found" if analysis.has_kubernetes else None,
                "Terraform IaC detected"     if analysis.has_terraform else None,
                "Ansible playbooks found"    if analysis.has_ansible else None,
            ])) + "."
            if has_infra else "No Kubernetes / Terraform / Ansible config found.",
        ),
        "Environment Setup": (
            has_code,
            f"Stack requires setup: {', '.join((sorted(langs) + sorted(fws))[:5])}."
            if has_code else "No source code found.",
        ),
        "Testing Strategy": (
            has_tests or has_code,
            f"Test frameworks detected: {', '.join(analysis.test_frameworks)}."
            if has_tests else
            "No test framework found yet — testing strategy section recommended."
            if has_code else "No source code found.",
        ),
        "Frontend Architecture": (
            has_frontend,
            f"Frontend framework(s) detected: {fw_list('react','vue','angular','svelte','nextjs','nuxtjs','gatsby','remix','astro')}."
            if has_frontend else "No frontend framework detected.",
        ),
        "Mobile Architecture": (
            has_mobile,
            f"Mobile framework(s) detected: {fw_list('flutter','react_native','expo','ionic','android')}."
            if has_mobile else "No mobile framework detected.",
        ),
        "AI/ML Pipeline": (
            has_ml,
            f"AI/ML library detected: {fw_list('tensorflow','pytorch','sklearn','huggingface','langchain','langgraph','openai')}."
            if has_ml else "No ML/AI libraries detected.",
        ),
        "Third-Party Integrations": (
            has_3p,
            f"External integrations detected: {fw_list('openai','langchain','celery','aws_cdk','pulumi','graphql_js','trpc','prisma_js')}."
            if has_3p else "No notable third-party integrations detected.",
        ),
        "Performance & Scalability": (
            has_web_fw or has_db or analysis.has_kubernetes,
            "Production-grade stack detected — performance documentation is applicable."
            if (has_web_fw or has_db or analysis.has_kubernetes) else
            "No scalability-related patterns detected.",
        ),
        "Error Handling & Logging": (
            has_code,
            "Source code present — error handling & logging documentation recommended."
            if has_code else "No source code found.",
        ),
        "Data Models & Schemas": (
            has_db or bool(fws & {"prisma_js", "typeorm", "drizzle",
                                  "sequelize", "mongoose", "dotnet_ef",
                                  "sqlalchemy"}),
            f"ORM/DB detected: {', '.join(analysis.databases[:3])}."
            if has_db else "No data layer detected.",
        ),
    }

    suggestions = []
    for section in ALL_SECTIONS:
        selected, reason = rules.get(section, (False, "No rule defined for this section."))
        suggestions.append(
            SectionSuggestion(
                name=section,
                selected=bool(selected),
                reason=reason,
            )
        )

    return suggestions
