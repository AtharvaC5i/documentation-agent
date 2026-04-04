import os
import json
from dotenv import load_dotenv

load_dotenv()

STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
STORE_PATH  = os.path.join(STORAGE_DIR, "project_store.json")
os.makedirs(STORAGE_DIR, exist_ok=True)

_store: dict = {}

def _load_from_disk():
    global _store
    if os.path.exists(STORE_PATH):
        try:
            with open(STORE_PATH, "r", encoding="utf-8") as f:
                _store = json.load(f)
        except Exception:
            _store = {}

def _save_to_disk():
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(_store, f, indent=2)

_load_from_disk()

def set_project(project_id: str, data: dict):
    _store[project_id] = data
    _save_to_disk()

def get_project(project_id: str) -> dict | None:
    return _store.get(project_id)

def update_project(project_id: str, key: str, value):
    if project_id not in _store:
        _store[project_id] = {}
    _store[project_id][key] = value
    _save_to_disk()
