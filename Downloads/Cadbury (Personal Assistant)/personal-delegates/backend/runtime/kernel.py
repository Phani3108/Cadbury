"""
DelegateRuntime: lifecycle manager for all delegate workers.
MVP: manages pause/resume state. Full async worker loop comes in Week 3.
"""

from __future__ import annotations

from typing import Optional

_runtime: Optional["DelegateRuntime"] = None


def get_runtime() -> Optional["DelegateRuntime"]:
    return _runtime


def set_runtime(runtime: "DelegateRuntime") -> None:
    global _runtime
    _runtime = runtime


class DelegateRuntime:
    def __init__(self):
        self._paused: set[str] = set()

    async def pause(self, delegate_id: str) -> None:
        self._paused.add(delegate_id)

    async def resume(self, delegate_id: str) -> None:
        self._paused.discard(delegate_id)

    def is_paused(self, delegate_id: str) -> bool:
        return delegate_id in self._paused

    async def start(self) -> None:
        """Start all delegate workers. Expanded in Week 3."""
        pass

    async def stop(self) -> None:
        """Graceful shutdown of all workers."""
        pass
