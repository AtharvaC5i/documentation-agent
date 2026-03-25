import os
import json
from typing import List


def build_metadata_index(filtered_files: List[str], output_path: str) -> dict:
    """
    Creates a JSON metadata index of the filtered codebase.
    Stores: file paths, sizes, line counts, and extensions.
    Saved to storage/repos/<project_id>/metadata_index.json
    """
    index = {}

    for filepath in filtered_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            loc = content.count("\n") + 1
        except Exception:
            loc = 0

        _, ext = os.path.splitext(filepath)
        index[filepath] = {
            "extension": ext.lower(),
            "loc": loc,
            "size_bytes": os.path.getsize(filepath),
        }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    return index


def load_metadata_index(output_path: str) -> dict:
    if not os.path.exists(output_path):
        return {}
    with open(output_path, "r", encoding="utf-8") as f:
        return json.load(f)