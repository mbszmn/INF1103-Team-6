from abc import ABC, abstractmethod
import json
import logging
import time
from managers.ai_response_validator import AIResponseValidator

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    #Abstract contract for AI providers with built-in retry and exponential backoff

    def __init__(self, model_name: str):
        self._model_name = model_name

    def get_model_name(self) -> str:
        return self._model_name

    def is_available(self) -> bool:
        # Check whether the provider is ready to accept requests
        return True

    def generate_json(
        self,
        prompt: str,
        validator: AIResponseValidator,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> dict | None:
        #Execute API call with retries, exponential backoff, and schema validation
        for attempt in range(max_retries):
            try:
                raw_response = self._call_api(prompt)
                parsed_data = json.loads(raw_response)

                if validator.validate_schema(parsed_data):
                    return parsed_data

                logger.warning(
                    "Attempt %d/%d returned invalid schema (missing required keys).",
                    attempt + 1,
                    max_retries,
                )
            except Exception as e:
                logger.warning("Attempt %d/%d failed: %s", attempt + 1, max_retries, e)

            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info("Retrying in %.1f seconds...", delay)
                time.sleep(delay)

        return None

    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        """Send prompt to the underlying AI service and return raw JSON text."""