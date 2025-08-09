from __future__ import annotations
import json, subprocess, shlex
from pathlib import Path
from typing import Dict, List, Any
import yaml

from ..services.orchestrator import RUNS_DIR
from ..runners.functional import CREATE_SUPPORT_CASE_SCHEMA

REPO_ROOT = Path(__file__).resolve().parents[2]

# ...existing code from instructions...
# (Full code as provided in your instructions above)
