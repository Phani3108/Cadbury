"""Load DelegationPolicy from YAML files."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from policy.models import DelegationPolicy

_POLICIES_DIR = Path(__file__).parent.parent / "config" / "delegate_policies"

_cache: dict[str, DelegationPolicy] = {}


def load_policy(delegate_id: str) -> DelegationPolicy:
    """Load and cache a delegation policy from YAML. Raises FileNotFoundError if not found."""
    if delegate_id in _cache:
        return _cache[delegate_id]

    policy_path = _POLICIES_DIR / f"{delegate_id}.yaml"
    if not policy_path.exists():
        raise FileNotFoundError(f"No policy file found for delegate '{delegate_id}' at {policy_path}")

    with policy_path.open() as f:
        data = yaml.safe_load(f)

    policy = DelegationPolicy.model_validate(data)
    _cache[delegate_id] = policy
    return policy


def reload_policy(delegate_id: str) -> DelegationPolicy:
    """Force-reload policy from disk (clears cache for this delegate)."""
    _cache.pop(delegate_id, None)
    return load_policy(delegate_id)
