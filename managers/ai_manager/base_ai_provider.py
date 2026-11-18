from abc import ABC, abstractmethod
import json
import logging
import time
from managers.ai_manager.ai_response_validator import AIResponseValidator

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    # Base blueprint for AI providers with built-in retries and wait delays
    def __init__(self, model_name: str):
        self._model_name = model_name

    def get_model_name(self) -> str:
        # Return the model name assigned to this provider
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
        # Call the AI up to max_retries times and check that the JSON is valid
        for attempt in range(max_retries):
            try:
                raw_response = self._call_api(prompt)
                parsed_data = json.loads(raw_response)

                # Stop early and return the result once all 8 keys are confirmed
                if validator.validate_schema(parsed_data):
                    return parsed_data

                logger.warning(
                    "Attempt %d/%d returned invalid schema (missing required keys).",
                    attempt + 1,
                    max_retries,
                )
            except Exception as e:
                logger.warning("Attempt %d/%d failed: %s", attempt + 1, max_retries, e)

            # Wait longer after each failed try (1s, 2s, 4s...) before retrying
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info("Retrying in %.1f seconds...", delay)
                time.sleep(delay)

        # Return None if every retry attempt failed
        return None

    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        # Send the prompt to the AI service and return the raw JSON text
        pass