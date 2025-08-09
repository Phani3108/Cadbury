from typing import Any

class MockAgentAdapter:
    async def call(self, prompt: str, context: Any = None) -> dict:
        # Return canned response for demo
        return {
            "response": "This is a mock agent reply.",
            "tool_calls": [{"name": "create_support_case", "schema_ok": True}],
            "latency_ms": 500,
            "cost_usd": 0.001
        }
