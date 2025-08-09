from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import yaml, os

from ..adapters.base import AgentAdapter
from ..adapters.agent_mock import MockAgent
from ..adapters.azure_openai import AzureOpenAIAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]

def load_agent_cfg(agent: str, environment: str) -> Dict[str, Any]:
    p = REPO_ROOT / "agents" / agent / "agent.yaml"
    data: Dict[str, Any] = {}
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    data["environment"] = environment
    return data

def build_adapter(agent: str, environment: str) -> tuple[AgentAdapter, Dict[str, Any]]:
    cfg = load_agent_cfg(agent, environment)
    provider = str(cfg.get("provider","mock")).lower()

    if provider == "azure_openai":
        adapter = AzureOpenAIAdapter({
            "deployment": cfg.get("azure_openai", {}).get("deployment"),
            "api_version": cfg.get("azure_openai", {}).get("api_version"),
            "endpoint": cfg.get("azure_openai", {}).get("endpoint"),
            "temperature": cfg.get("temperature", 0),
            "pricing": cfg.get("pricing", {}),
        })
        return adapter, {"provider": adapter.provider, **cfg}

    adapter = MockAgent()
    return adapter, {"provider": "mock", **cfg}
