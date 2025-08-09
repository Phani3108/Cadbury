from __future__ import annotations
from typing import List
from ..models.dto import TestSpec, TestResult, AssertionResult

from ..adapters.base import AgentAdapter

CHAOS_PROMPTS = [
    {"id": "chaos-500-01", "prompt": "Simulate outage: tool returns 500 while creating support case."},
    {"id": "chaos-timeout-01", "prompt": "Simulate outage: tool returns 500 (timeout-like) and recover."}
]

class ToolRobustnessRunner:
    name = "tool_robustness"

    def __init__(self, adapter: AgentAdapter) -> None:
        self.agent = adapter

    def run(self, spec: TestSpec) -> List[TestResult]:
        out: List[TestResult] = []
        for item in CHAOS_PROMPTS:
            text, tool_calls, latency_ms, cost_usd = self.agent.invoke(item["prompt"], None)
            asserts: List[AssertionResult] = []
            # We expect a graceful fallback message in strict mode
            expects_fallback = ("retry" in text.lower()) or ("fall back" in text.lower()) or ("fallback" in text.lower()) or ("unavailable" in text.lower())
            asserts.append(AssertionResult(type="graceful_fallback", passed=expects_fallback, details={"response": text[:120]}))
            # Ensure the tool name is still consistent if used
            if tool_calls:
                ok = all(tc.get("name") == "create_support_case" for tc in tool_calls)
                asserts.append(AssertionResult(type="tool_consistency", passed=ok, details={}))
            passed = all(a.passed for a in asserts)
            out.append(TestResult(
                id=item["id"], pack=self.name, passed=passed, assertions=asserts,
                latency_ms=latency_ms, cost_usd=cost_usd, response_text=text, tool_calls=tool_calls
            ))
        return out
