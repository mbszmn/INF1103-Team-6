import json
from managers.ai_manager.base_ai_provider import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    # Offline mock AI provider for deterministic unit testing and offline demos

    def __init__(self, canned_response: dict | None = None, model_name: str = "mock-ai-model"):
        super().__init__(model_name)
        self._canned_response = canned_response or {
            "category": "Network",
            "priority": "Medium",
            "confidence": 0.92,
            "summary": "Unable to connect to campus Wi-Fi network.",
            "affected_system": "SIT Wi-Fi",
            "security_related": False,
            "requires_escalation": False,
            "troubleshooting": [
                "Forget the SIT Wi-Fi network and reconnect using your SIT credentials.",
                "Restart your wireless network adapter and test connectivity.",
            ],
        }

    def _call_api(self, prompt: str) -> str:
        return json.dumps(self._canned_response)