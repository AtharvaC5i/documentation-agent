import json
import os
from typing import List, Dict, Any

CICD_FILES = {
    ".travis.yml", "jenkinsfile", "jenkinsfile.groovy",
    "circle.yml", ".gitlab-ci.yml",
    "azure-pipelines.yml", "azure-pipelines.yaml",
    "bitbucket-pipelines.yml", "appveyor.yml",
    "buildkite.yml", ".drone.yml", "codefresh.yml",
    "cloudbuild.yaml", "cloudbuild.yml",
    "skaffold.yaml", "skaffold.yml",
}

CICD_DIRS = {
    ".github", ".circleci", ".gitlab", ".teamcity",
    ".buildkite", ".drone", "tekton",
}

DOCKER_FILES = {
    "dockerfile", "dockerfile.dev", "dockerfile.prod",
    "dockerfile.staging", "docker-compose.yml",
    "docker-compose.yaml", "docker-compose.dev.yml",
    "docker-compose.prod.yml", ".dockerignore",
}

K8S_FILES = {
    "deployment.yaml", "deployment.yml", "service.yaml",
    "ingress.yaml", "configmap.yaml", "helmfile.yaml",
}
K8S_DIRS = {"k8s", "kubernetes", "helm", "charts", "manifests", "infra"}
TERRAFORM_EXT = {".tf", ".tfvars"}
ANSIBLE_FILES = {"playbook.yml", "playbook.yaml", "ansible.cfg", "inventory"}


def detect_tech_stack(filtered_files: List[str]) -> Dict[str, Any]:
    filenames_lower = {os.path.basename(f).lower() for f in filtered_files}
    all_parts = {
        part.lower()
        for f in filtered_files
        for part in f.replace("\\", "/").split("/")
    }
    extensions = {os.path.splitext(f)[1].lower() for f in filtered_files}

    return {
        "has_dockerfile": bool(filenames_lower & DOCKER_FILES),
        "has_cicd": bool((filenames_lower & CICD_FILES) or (all_parts & CICD_DIRS)),
        "has_kubernetes": bool((filenames_lower & K8S_FILES) or (all_parts & K8S_DIRS)),
        "has_terraform": bool(extensions & TERRAFORM_EXT),
        "has_ansible": bool(filenames_lower & ANSIBLE_FILES),
        "detected_language_hints": sorted({os.path.splitext(f)[1].lower() for f in filtered_files}),
        "detected_framework_hints": [],
        "detected_database_hints": [],
        "detected_test_hints": [],
    }


def build_tech_stack_comparison(detected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
    detected_items = set()
    actual_items = set()

    for key, value in (detected or {}).items():
        if isinstance(value, bool) and value:
            detected_items.add(key)
        elif isinstance(value, list) and value:
            detected_items.add(key)

    for key, value in (actual or {}).items():
        if isinstance(value, bool) and value:
            actual_items.add(key)
        elif isinstance(value, list) and value:
            actual_items.add(key)

    correct_matches = sorted(detected_items & actual_items)
    missed_items = sorted(actual_items - detected_items)
    false_positives = sorted(detected_items - actual_items)

    denom = max(len(actual_items), len(detected_items), 1)
    accuracy_score = round(len(correct_matches) / denom, 3)

    return {
        "detected": detected or {},
        "actual": actual or {},
        "correct_matches": correct_matches,
        "missed_items": missed_items,
        "false_positives": false_positives,
        "accuracy_score": accuracy_score,
    }