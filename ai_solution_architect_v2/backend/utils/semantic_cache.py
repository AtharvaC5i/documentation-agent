import os
import hashlib
import json
import re
from typing import Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), "../storage/semantic_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _normalize(text: str) -> str:
    """
    Normalizes text for robust cache keys.
    """
    text = text.lower().strip()
    text = re.sub(r'```[a-z]*', '', text)
    text = re.sub(r'[\{\}\[\]\:\,\"\']', '', text)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_cache(system_prompt: str, user_prompt: str) -> Optional[dict]:
    """
    Check if a cached response exists for the normalized prompts.
    """
    norm_sys = _normalize(system_prompt)
    norm_user = _normalize(user_prompt)
    combined = f"{norm_sys}|||{norm_user}"
    
    prompt_hash = hashlib.md5(combined.encode('utf-8')).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{prompt_hash}.json")
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[SemanticCache] HIT: {prompt_hash}")
                return data.get("response")
        except Exception as e:
            print(f"[SemanticCache] Error reading cache file {cache_path}: {e}")
            
    return None

def set_cache(system_prompt: str, user_prompt: str, response: dict) -> None:
    """
    Saves a response to the semantic cache.
    """
    norm_sys = _normalize(system_prompt)
    norm_user = _normalize(user_prompt)
    combined = f"{norm_sys}|||{norm_user}"
    
    prompt_hash = hashlib.md5(combined.encode('utf-8')).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{prompt_hash}.json")
    
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({
                "hash": prompt_hash,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response": response
            }, f, indent=2)
        print(f"[SemanticCache] SAVED: {prompt_hash}")
    except Exception as e:
        print(f"[SemanticCache] Error writing cache file {cache_path}: {e}")
