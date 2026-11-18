import logging
from google import genai
from google.genai import types
from managers.ai_manager.base_ai_provider import BaseAIProvider

logger = logging.getLogger(__name__)
logging.getLogger("google.genai").setLevel(logging.ERROR)


class GeminiProvider(BaseAIProvider):
    # Connects to Google's Gemini AI service to analyze tickets
    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        super().__init__(model_name)
        self._client = self._initialise_client()

    def _initialise_client(self):
        # Create the Gemini client using the API key from the environment
        try:
            return genai.Client()
        except Exception as e:
            logger.warning("Could not initialize Gemini client: GEMINI_API_KEY is missing.")
            return None

    def is_available(self) -> bool:
        # Return True only if the Gemini client was set up without errors
        return self._client is not None

    def _call_api(self, prompt: str) -> str:
        # Stop immediately if the Gemini client is not ready
        if not self._client:
            raise RuntimeError("Gemini client is not initialized.")

        # Request a JSON reply with low randomness for consistent answers
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        # Raise an error if Gemini blocked or returned an empty reply
        if not response.text:
            raise ValueError("Gemini API returned an empty response.")
        return response.text