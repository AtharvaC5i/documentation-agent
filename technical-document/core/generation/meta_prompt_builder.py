from core.analysis.analysis_models import AnalysisResult


SECTION_PROMPT_MAP = {
    "Executive Summary": {
        "query": "project overview architecture purpose main components",
        "instruction": (
            "Write a concise executive summary of this software project. "
            "Cover: what the system does, its primary purpose, the core tech stack, "
            "and the high-level architecture. Write for a technical manager or client "
            "who needs to understand the project quickly. 3-5 paragraphs."
        ),
    },
    "Tech Stack Overview": {
        "query": "programming languages frameworks libraries dependencies package manager",
        "instruction": (
            "Document the complete tech stack of this project. "
            "List all languages, frameworks, libraries, and tools detected. "
            "For each major technology explain why it is likely used in this project. "
            "Include versions where detectable. Use tables where appropriate."
        ),
    },
    "System Architecture": {
        "query": "architecture components modules services layers structure design patterns",
        "instruction": (
            "Describe the system architecture of this project in detail. "
            "Cover: overall architectural pattern (monolith, microservices, layered, etc.), "
            "major components and how they interact, data flow between layers, "
            "and any notable design patterns used. Include a textual architecture diagram if possible."
        ),
    },
    "API Documentation": {
        "query": "API routes endpoints HTTP methods request response parameters authentication",
        "instruction": (
            "Document all API endpoints in this project. "
            "For each endpoint provide: HTTP method, path, description, "
            "request parameters/body, response format, and authentication requirements. "
            "Group endpoints by resource or module. Use tables for parameters."
        ),
    },
    "Database Schema": {
        "query": "database models schema tables columns relationships foreign keys ORM migrations",
        "instruction": (
            "Document the database schema and data models. "
            "For each model/table: list all fields with types and constraints, "
            "describe relationships (one-to-many, many-to-many), "
            "explain the purpose of each model in the system context. "
            "Include an entity relationship description."
        ),
    },
    "Authentication & Security": {
        "query": "authentication authorization JWT OAuth security middleware permissions roles",
        "instruction": (
            "Document the authentication and security implementation. "
            "Cover: authentication mechanism used (JWT, OAuth, session, API key), "
            "authorization and role/permission system, security middleware, "
            "password handling, and any security best practices implemented."
        ),
    },
    "Deployment Guide": {
        "query": "deployment Docker Dockerfile containerization environment production build",
        "instruction": (
            "Write a complete deployment guide for this project. "
            "Cover: prerequisites, environment variables required, "
            "Docker setup and commands if applicable, build steps, "
            "production deployment process, and health checks. "
            "Be specific with exact commands."
        ),
    },
    "CI/CD Pipeline": {
        "query": "CI CD pipeline GitHub Actions GitLab Jenkins workflow build test deploy stages",
        "instruction": (
            "Document the CI/CD pipeline configuration. "
            "Cover: what CI/CD tool is used, pipeline stages (build, test, deploy), "
            "triggers and conditions, environment-specific deployments, "
            "and how to modify or extend the pipeline."
        ),
    },
    "Infrastructure & DevOps": {
        "query": "Kubernetes Terraform Ansible infrastructure IaC helm charts manifests",
        "instruction": (
            "Document the infrastructure and DevOps setup. "
            "Cover: infrastructure-as-code tools used, Kubernetes manifests and configs, "
            "Terraform resources, Ansible playbooks, scaling configuration, "
            "and how to provision or modify infrastructure."
        ),
    },
    "Environment Setup": {
        "query": "environment variables configuration setup local development .env requirements install",
        "instruction": (
            "Write a complete local environment setup guide for a new developer. "
            "Cover: prerequisites and system requirements, installation steps, "
            "environment variables and their purpose, how to run the project locally, "
            "and common setup issues. Be specific with exact commands."
        ),
    },
    "Testing Strategy": {
        "query": "tests unit integration test framework pytest jest test cases coverage",
        "instruction": (
            "Document the testing strategy and test suite. "
            "Cover: testing frameworks used, types of tests present (unit, integration, e2e), "
            "how to run tests, test coverage approach, "
            "and guidelines for writing new tests."
        ),
    },
    "Frontend Architecture": {
        "query": "frontend components pages routes state management UI React Vue Angular",
        "instruction": (
            "Document the frontend architecture. "
            "Cover: framework and key libraries used, component structure, "
            "routing setup, state management approach, "
            "API communication pattern, and styling approach."
        ),
    },
    "Mobile Architecture": {
        "query": "mobile app screens navigation state Flutter React Native components",
        "instruction": (
            "Document the mobile application architecture. "
            "Cover: framework used, screen and navigation structure, "
            "state management, API integration, "
            "platform-specific configurations, and build process."
        ),
    },
    "AI/ML Pipeline": {
        "query": "machine learning model training inference pipeline dataset embeddings LLM",
        "instruction": (
            "Document the AI/ML pipeline. "
            "Cover: models used or trained, data pipeline and preprocessing, "
            "training process if applicable, inference setup, "
            "external AI services integrated, and how to update or retrain models."
        ),
    },
    "Third-Party Integrations": {
        "query": "third party API integration external services webhooks SDK client",
        "instruction": (
            "Document all third-party integrations. "
            "For each integration: what service it is, why it is used, "
            "how it is configured, what credentials are needed, "
            "and how data flows to/from the external service."
        ),
    },
    "Performance & Scalability": {
        "query": "performance caching optimization scalability load balancing async queue",
        "instruction": (
            "Document performance and scalability considerations. "
            "Cover: caching strategies, async processing, database optimization, "
            "load balancing setup, bottlenecks identified in the code, "
            "and recommendations for scaling."
        ),
    },
    "Error Handling & Logging": {
        "query": "error handling exceptions logging middleware monitoring error responses",
        "instruction": (
            "Document the error handling and logging approach. "
            "Cover: global error handling middleware, exception types and how they are handled, "
            "logging setup and log levels, monitoring integrations if any, "
            "and how errors are surfaced to clients."
        ),
    },
    "Data Models & Schemas": {
        "query": "data models schemas validation Pydantic serializers DTOs types",
        "instruction": (
            "Document all data models, schemas, and validation logic. "
            "Cover: request/response schemas, validation rules, "
            "data transformation logic, and how models relate to database entities."
        ),
    },
}

DEFAULT_PROMPT = {
    "query": "{section_name} implementation code logic",
    "instruction": (
        "Write comprehensive documentation for the '{section_name}' section of this project. "
        "Analyse the provided code context carefully and document: "
        "what this aspect of the system does, how it is implemented, "
        "key design decisions, and anything a developer needs to know to work with it."
    ),
}


def build_meta_prompt(section_name: str, analysis: AnalysisResult) -> dict:
    """
    Returns a dict with:
      - 'query':       the ChromaDB search query for this section
      - 'instruction': the LLM instruction for generating this section
    """
    template = SECTION_PROMPT_MAP.get(section_name)

    if not template:
        # Custom section — build dynamically
        return {
            "query": DEFAULT_PROMPT["query"].format(section_name=section_name),
            "instruction": DEFAULT_PROMPT["instruction"].format(section_name=section_name),
        }

    return {
        "query":       template["query"],
        "instruction": template["instruction"],
    }
