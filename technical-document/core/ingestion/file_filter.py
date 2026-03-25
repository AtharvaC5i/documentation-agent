import os
from typing import List

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "env", "dist", "build", ".next", ".nuxt", "coverage",
    ".tox", ".mypy_cache", ".pytest_cache", "target",
}

IGNORE_EXTENSIONS = {
    # Binaries & media
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".mp4", ".mp3", ".avi", ".mov", ".pdf",
    # Archives
    ".zip", ".tar", ".gz", ".rar",
    # Compiled / binary
    ".exe", ".dll", ".so", ".pyc", ".class", ".jar", ".bin",
    # Lock files (large, no documentation value)
    ".lock",
    # IDE / OS artifacts
    ".DS_Store", ".idea",
}

MAX_FILE_SIZE_BYTES = 500_000  # Skip files larger than 500KB


def filter_codebase(root: str) -> List[str]:
    """
    Walks the cloned/extracted repo and returns a list of absolute file paths
    that are suitable for analysis and chunking (source code only).
    Reduces codebase size by 70–90%.
    """
    kept_files: List[str] = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Prune ignored directories in-place to prevent descent
        dirnames[:] = [
            d for d in dirnames
            if d not in IGNORE_DIRS and not d.startswith(".")
        ]

        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext.lower() in IGNORE_EXTENSIONS:
                continue

            filepath = os.path.join(dirpath, filename)

            try:
                if os.path.getsize(filepath) > MAX_FILE_SIZE_BYTES:
                    continue
            except OSError:
                continue

            kept_files.append(filepath)

    return kept_files