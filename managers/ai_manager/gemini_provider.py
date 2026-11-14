import logging
from google import genai
from google.genai import types
from managers.base_ai_provider import BaseAIProvider

logger = logging.getLogger(__name__)
logging.getLogger("google.genai").setLevel(logging.ERROR)


class GeminiProvider(BaseAIProvider):
    # Concrete AI provider backed by Google GenAI SDK

    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        super().__init__(model_name)
        self._client = self._initialise_client()

    def _initialise_client(self):
        try:
            return genai.Client()
        except Exception as e:
            logger.warning("Could not initialize Gemini client (Missing API Key): %s", e)
            return None

    def is_available(self) -> bool:
        return self._client is not None

    def _call_api(self, prompt: str) -> str:
        if not self._client:
            raise RuntimeError("Gemini client is not initialized.")

        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        return response.text