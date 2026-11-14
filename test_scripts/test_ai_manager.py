import pytest

from managers.ai_manager.ai_manager import AIManager
from managers.ai_manager.ai_response_validator import AIResponseValidator
from managers.ai_manager.base_ai_provider import BaseAIProvider
from managers.ai_manager.gemini_provider import GeminiProvider
from managers.ai_manager.mock_ai_provider import MockAIProvider
from managers.ai_manager.prompt_builder import PromptBuilder


class FailingAIProvider(BaseAIProvider):
    #Stub AI provider used to simulate offline state, API errors, or malformed JSON

    def __init__(
        self,
        raw_responses: list[str] | None = None,
        available: bool = True,
        raise_error: bool = False,
    ):
        super().__init__(model_name="failing-stub-model")
        self._raw_responses = list(raw_responses) if raw_responses else []
        self._available = available
        self._raise_error = raise_error
        self.call_count = 0

    def is_available(self) -> bool:
        return self._available

    def _call_api(self, prompt: str) -> str:
        self.call_count += 1
        if self._raise_error:
            raise ConnectionError("Simulated API network timeout")
        if self._raw_responses:
            return self._raw_responses.pop(0)
        return "not valid json"


def _sample_ticket() -> dict:
    return {
        "username": "alex",
        "student_id": "2600001",
        "title": "Campus Wi-Fi keeps disconnecting",
        "description": "My laptop drops SIT Wi-Fi every 5 minutes in the library.",
        "device": "Windows 11 Laptop",
        "error_message": "ERR_NETWORK_CHANGED",
        "steps_attempted": "Restarted Wi-Fi adapter",
        "user_priority": "Critical",
    }


def _valid_part1_payload() -> dict:
    return {
        "category": "Network",
        "priority": "High",
        "confidence": 0.91,
        "summary": "User experiences frequent Wi-Fi drops on Windows 11 laptop.",
        "affected_system": "SIT Wi-Fi",
        "security_related": False,
        "requires_escalation": False,
        "troubleshooting": [
            "Forget the SIT Wi-Fi profile and reconnect with your student credentials.",
            "Update the wireless network driver via Device Manager.",
        ],
    }


# --- 1. PromptBuilder Tests ---
def test_prompt_builder_includes_context_and_guardrail_without_bias_fields():
    builder = PromptBuilder()
    prompt = builder.build_triage_prompt(_sample_ticket())

    assert "[GUARDRAIL]" in prompt
    assert "Campus Wi-Fi keeps disconnecting" in prompt
    assert "Windows 11 Laptop" in prompt
    assert "ERR_NETWORK_CHANGED" in prompt
    assert "Restarted Wi-Fi adapter" in prompt
    # User priority and student ID are omitted to avoid bias and protect privacy
    assert "2600001" not in prompt


# --- 2. AIResponseValidator Tests---
def test_validator_accepts_complete_part1_schema():
    validator = AIResponseValidator()
    assert validator.validate_schema(_valid_part1_payload()) is True


@pytest.mark.parametrize(
    "missing_key",
    [
        "category",
        "priority",
        "confidence",
        "summary",
        "affected_system",
        "security_related",
        "requires_escalation",
        "troubleshooting",
    ],
)
def test_validator_rejects_missing_required_key(missing_key: str):
    validator = AIResponseValidator()
    payload = _valid_part1_payload()
    del payload[missing_key]

    assert validator.validate_schema(payload) is False


def test_validator_rejects_non_dict_input():
    validator = AIResponseValidator()
    assert validator.validate_schema(["not", "a", "dict"]) is False  # type: ignore[arg-type]


# --- 3. Provider & Polymorphism Tests ---
def test_gemini_provider_handles_missing_api_key_gracefully(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider = GeminiProvider(model_name="gemini-3.5-flash-lite")

    assert provider.get_model_name() == "gemini-3.5-flash-lite"
    assert provider.is_available() is False


def test_ai_manager_uses_mock_provider_polymorphically():
    expected = _valid_part1_payload()
    provider = MockAIProvider(canned_response=expected)
    manager = AIManager(provider=provider)

    ticket = _sample_ticket()
    result = manager.analyse_ticket(
        title=ticket["title"],
        description=ticket["description"],
        device=ticket["device"],
        error_message=ticket["error_message"],
        steps_attempted=ticket["steps_attempted"],
    )

    assert manager.get_model_name() == "mock-ai-model"
    assert result == expected
    assert result["confidence"] == 0.91


# --- 4. Retry & Offline Fallback Tests ---
def test_base_provider_retries_on_malformed_json_then_succeeds():
    validator = AIResponseValidator()
    valid_json = (
        '{"category": "Software", "priority": "Medium", "confidence": 0.88, '
        '"summary": "Excel crashes on launch.", "affected_system": "Microsoft Excel", '
        '"security_related": false, "requires_escalation": false, '
        '"troubleshooting": ["Open Excel in Safe Mode."]}'
    )
    flaky_provider = FailingAIProvider(
        raw_responses=["{bad json", '{"category": "Software"}', valid_json]
    )

    parsed = flaky_provider.generate_json(
        "test prompt", validator=validator, max_retries=3, base_delay=0.0
    )

    assert parsed is not None
    assert flaky_provider.call_count == 3
    assert parsed["category"] == "Software"
    assert parsed["confidence"] == 0.88


def test_ai_manager_falls_back_when_provider_offline():
    offline_provider = FailingAIProvider(available=False)
    manager = AIManager(provider=offline_provider)

    ticket = _sample_ticket()
    result = manager.analyse_ticket(
        title=ticket["title"],
        description=ticket["description"],
        device=ticket["device"],
    )

    assert offline_provider.call_count == 0
    assert result["category"] == "Network"
    assert result["priority"] == "Medium"
    assert result["confidence"] == 0.0
    assert result["security_related"] is False
    assert result["requires_escalation"] is False
    assert len(result["troubleshooting"]) > 0


def test_ai_manager_falls_back_after_exhausting_retries_on_security_ticket():
    broken_provider = FailingAIProvider(raise_error=True)
    manager = AIManager(provider=broken_provider)

    result = manager.analyse_ticket(
        title="Received suspicious phishing email",
        description="Clicked a suspicious link asking for SIT login credentials.",
        device="MacBook Air",
    )

    assert broken_provider.call_count == 3
    assert result["category"] == "Security"
    assert result["confidence"] == 0.0
    assert result["security_related"] is True
    assert result["requires_escalation"] is True
    assert len(result["troubleshooting"]) > 0