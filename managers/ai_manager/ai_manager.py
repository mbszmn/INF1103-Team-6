import logging
from managers.ai_manager.ai_response_validator import AIResponseValidator
from managers.ai_manager.base_ai_provider import BaseAIProvider
from managers.ai_manager.gemini_provider import GeminiProvider
from managers.ai_manager.prompt_builder import PromptBuilder
from managers.logic_manager import LogicManager

logger = logging.getLogger(__name__)

class AIManager:
    # Coordinates prompt building, AI provider calls, validation, and keyword fallback

    def __init__(
        self,
        provider: BaseAIProvider | None = None,
        logic_manager: LogicManager | None = None,
        model_name: str = "gemini-3.5-flash-lite",
    ):
        self._provider = provider if provider is not None else GeminiProvider(model_name=model_name)
        self._logic_manager = logic_manager if logic_manager is not None else LogicManager()
        self._prompt_builder = PromptBuilder()
        self._validator = AIResponseValidator()

    def get_model_name(self) -> str:
        return self._provider.get_model_name()

    def analyse_ticket(
        self,
        title: str,
        description: str,
        device: str = "Unknown",
        error_message: str = "",
        steps_attempted: str = "",
    ) -> dict:
        ticket_data = {
            "title": title,
            "description": description,
            "device": device,
            "error_message": error_message,
            "steps_attempted": steps_attempted,
        }

        if not self._provider.is_available():
            logger.warning("AI provider is offline. Falling back to LogicManager rules.")
            return self._generate_fallback_dict(ticket_data)

        prompt = self._prompt_builder.build_triage_prompt(ticket_data)
        parsed_data = self._provider.generate_json(prompt, validator=self._validator)

        if parsed_data is not None:
            return parsed_data

        logger.error("AI service unavailable after retries. Using fallback classification.")
        return self._generate_fallback_dict(ticket_data)

    # to return a safe dictionary using LogicManager if AI fails
    def _generate_fallback_dict(self, ticket_data: dict) -> dict:
        category = self._logic_manager.classify_ticket(ticket_data)
        fallback_steps = self._logic_manager.get_fallback_troubleshooting(category)
        description = ticket_data.get("description", "")

        return {
            "category": category,
            "priority": "Medium",
            "confidence": 0.0,
            "summary": description,
            "affected_system": "Unknown",
            "security_related": category == "Security",
            "requires_escalation": category == "Security",
            "troubleshooting": fallback_steps,
        }