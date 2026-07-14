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
    detected = detected or {}
    actual = actual or {}

    detected_items = set()
    actual_items = set()

    # 1. Map booleans to string representation of technologies
    boolean_keys = ["has_dockerfile", "has_cicd", "has_kubernetes", "has_terraform", "has_ansible"]
    for key in boolean_keys:
        tech_name = key.replace("has_", "")
        if detected.get(key):
            detected_items.add(tech_name)
        if actual.get(key):
            actual_items.add(tech_name)

    # Extension to language map for normalizing extension language hints
    extension_map = {
        ".py": "Python", ".pyw": "Python", ".pyx": "Python", ".wsgi": "Python",
        ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript",
        ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript",
        ".html": "HTML", ".htm": "HTML",
        ".css": "CSS", ".scss": "CSS", ".sass": "CSS", ".less": "CSS",
        ".vue": "Vue", ".svelte": "Svelte",
        ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".groovy": "Groovy", ".scala": "Scala",
        ".clj": "Clojure", ".cljs": "Clojure",
        ".cs": "C#", ".vb": "VB.NET", ".fs": "F#", ".fsx": "F#", ".razor": "C#",
        ".c": "C", ".h": "C", ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++",
        ".rs": "Rust", ".go": "Go", ".zig": "Zig",
        ".swift": "Swift", ".m": "Objective-C", ".dart": "Dart",
        ".rb": "Ruby", ".rake": "Ruby", ".gemspec": "Ruby", ".erb": "Ruby",
        ".php": "PHP", ".phtml": "PHP",
        ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".fish": "Shell",
        ".ps1": "PowerShell", ".psm1": "PowerShell",
        ".bat": "Batch", ".cmd": "Batch",
        ".sql": "SQL",
        ".r": "R", ".rmd": "R",
        ".jl": "Julia",
        ".tf": "Terraform", ".tfvars": "Terraform",
        ".yaml": "YAML", ".yml": "YAML",
        ".toml": "TOML", ".json": "JSON",
        ".j2": "Jinja2", ".jinja": "Jinja2",
        ".hbs": "Handlebars", ".ejs": "EJS",
        ".ex": "Elixir", ".exs": "Elixir",
        ".erl": "Erlang", ".hrl": "Erlang",
        ".hs": "Haskell", ".lhs": "Haskell",
        ".lua": "Lua",
        ".pl": "Perl", ".pm": "Perl",
        ".ml": "OCaml", ".mli": "OCaml",
        ".nim": "Nim", ".cr": "Crystal",
        ".sol": "Solidity",
        ".proto": "Protobuf",
        ".graphql": "GraphQL", ".gql": "GraphQL",
    }

    # Helper function to normalize list elements
    def collect_elements(lst, target_set):
        for item in (lst or []):
            if isinstance(item, str) and item:
                # If item is an extension, map it to language name
                if item.startswith("."):
                    mapped = extension_map.get(item.lower(), item)
                    target_set.add(mapped)
                else:
                    target_set.add(item)

    # Collect from lists
    collect_elements(detected.get("detected_language_hints"), detected_items)
    collect_elements(detected.get("languages"), detected_items)
    collect_elements(detected.get("detected_framework_hints"), detected_items)
    collect_elements(detected.get("frameworks"), detected_items)
    collect_elements(detected.get("detected_database_hints"), detected_items)
    collect_elements(detected.get("databases"), detected_items)
    collect_elements(detected.get("detected_test_hints"), detected_items)
    collect_elements(detected.get("test_frameworks"), detected_items)

    collect_elements(actual.get("detected_language_hints"), actual_items)
    collect_elements(actual.get("languages"), actual_items)
    collect_elements(actual.get("detected_framework_hints"), actual_items)
    collect_elements(actual.get("frameworks"), actual_items)
    collect_elements(actual.get("detected_database_hints"), actual_items)
    collect_elements(actual.get("databases"), actual_items)
    collect_elements(actual.get("detected_test_hints"), actual_items)
    collect_elements(actual.get("test_frameworks"), actual_items)

    # Perform case-insensitive set comparisons
    # We will build lowercased sets for sets operations, but map back to the original casing
    detected_map = {x.lower(): x for x in detected_items if x}
    actual_map = {x.lower(): x for x in actual_items if x}

    det_lower = set(detected_map.keys())
    act_lower = set(actual_map.keys())

    correct_lower = det_lower & act_lower
    missed_lower = act_lower - det_lower
    false_lower = det_lower - act_lower

    # Reconstruct original casings (prefer casing from actual stack, then detected stack)
    correct_matches = sorted([actual_map[x] for x in correct_lower])
    missed_items = sorted([actual_map[x] for x in missed_lower])
    false_positives = sorted([detected_map[x] for x in false_lower])

    denom = max(len(actual_map), len(detected_map), 1)
    accuracy_score = round(len(correct_matches) / denom, 3)

    return {
        "detected": detected or {},
        "actual": actual or {},
        "correct_matches": correct_matches,
        "missed_items": missed_items,
        "false_positives": false_positives,
        "accuracy_score": accuracy_score,
    }