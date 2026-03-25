import os
import gc
from typing import Optional
import git


def clone_github_repo(url: str, dest: str, token: Optional[str] = None) -> None:
    """
    Clones a GitHub repository to the specified destination.
    If a token is provided for private repos, it is embedded in the URL
    and immediately wiped from memory after the clone completes.
    """
    os.makedirs(dest, exist_ok=True)

    if token:
        # Embed token into URL for authentication
        auth_url = url.replace("https://", f"https://{token}@")
        try:
            git.Repo.clone_from(auth_url, dest)
        finally:
            # Critical: wipe token from all references immediately
            auth_url = "REDACTED"
            token = "REDACTED"
            del auth_url, token
            gc.collect()
    else:
        git.Repo.clone_from(url, dest)