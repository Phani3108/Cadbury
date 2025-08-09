from __future__ import annotations
from typing import List, Dict, Any
import os

def allowed_domain(domain: str) -> bool:
    # You already have a connectors allow-list elsewhere; keep this as a guard.
    return True  # replace with your existing checker if you wired one

def fetch_confluence(space: str, base_url: str, user_env: str, token_env: str) -> List[Dict[str, Any]]:
    # STUB: only activate if explicitly allowed and envs present
    if not (os.getenv(user_env) and os.getenv(token_env)):
        return []
    if not allowed_domain(base_url.split("/")[2]):
        return []
    # Implement when ready (use Atlassian REST API to pull page HTML → text)
    return []

def fetch_github(repo: str, dir: str, branch: str) -> List[Dict[str, Any]]:
    # STUB: clone/ls or use GH API; keep disabled by default
    return []

def fetch_sharepoint(site: str, doclib: str) -> List[Dict[str, Any]]:
    # STUB
    return []

def fetch_azure_ai_search(endpoint_env: str, key_env: str, index: str, query: str) -> List[Dict[str, Any]]:
    # STUB: call Azure Search when allow-listed
    return []
