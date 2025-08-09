from .base import Runner, RunContext, TestSpec, TestResult
from typing import List


from ..adapters.base import AgentAdapter

class SafetyRunner:
    def __init__(self, adapter: AgentAdapter):
        self.agent = adapter
    async def run(self, run_ctx: RunContext, spec: TestSpec) -> List[TestResult]:
        # TODO: implement adversarial prompts, PII checks
        return []
