import json
from managers.ai_manager.base_ai_provider import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    # Fake AI provider that returns preset replies for offline unit tests
    def __init__(self, canned_response: dict, model_name: str = "mock-ai-model"):
        super().__init__(model_name)
        self._canned_response = dict(canned_response)

    def _call_api(self, prompt: str) -> str:
        # Convert the preset dictionary into a JSON string without using the internet
        return json.dumps(self._canned_response)