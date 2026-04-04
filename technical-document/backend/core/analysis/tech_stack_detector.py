import os
from typing import List


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
K8S_DIRS     = {"k8s", "kubernetes", "helm", "charts", "manifests", "infra"}
TERRAFORM_EXT = {".tf", ".tfvars"}
ANSIBLE_FILES = {"playbook.yml", "playbook.yaml", "ansible.cfg", "inventory"}


def detect_tech_stack(filtered_files: List[str]) -> dict:
    filenames_lower = {os.path.basename(f).lower() for f in filtered_files}
    all_parts = {
        part.lower()
        for f in filtered_files
        for part in f.replace("\\", "/").split("/")
    }
    extensions = {os.path.splitext(f)[1].lower() for f in filtered_files}

    return {
        "has_dockerfile":  bool(filenames_lower & DOCKER_FILES),
        "has_cicd":        bool((filenames_lower & CICD_FILES) or (all_parts & CICD_DIRS)),
        "has_kubernetes":  bool((filenames_lower & K8S_FILES) or (all_parts & K8S_DIRS)),
        "has_terraform":   bool(extensions & TERRAFORM_EXT),
        "has_ansible":     bool(filenames_lower & ANSIBLE_FILES),
    }
