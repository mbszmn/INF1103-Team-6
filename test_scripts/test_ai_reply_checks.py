import json
from types import SimpleNamespace

import pytest

from managers.ai_manager import AIManager
from managers.ai_manager import gemini_provider
from managers.ai_manager.gemini_provider import GeminiProvider
from managers.logic_manager import LogicManager

# the brief asks for tests where the AI gives a reply in the right shape but with wrong values,
# these go through the real LogicManager and the real GeminiProvider with a fake Google client

GOOD_REPLY = {
    "category": "Network",
    "priority": "High",
    "confidence": 0.9,
    "summary": "Cannot connect to campus WiFi",
    "affected_system": "WiFi adapter",
    "security_related": False,
    "requires_escalation": False,
    "troubleshooting": ["Forget the network and join it again"],
}
TICKET = {"title": "WiFi problem", "description": "Cannot connect to the school WiFi", "device": "Dell"}


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_error"),
    [
        ("category", "network", "Invalid category: network"),
        ("category", "Printer", "Invalid category: Printer"),
        ("priority", "Urgent", "Invalid priority: Urgent"),
        ("confidence", "0.9", "Confidence score must be a number."),
        ("confidence", True, "Confidence score must be a number."),
        ("confidence", 1.5, "Confidence score must be between 0 and 1."),
        ("confidence", -0.1, "Confidence score must be between 0 and 1."),
        ("security_related", "false", "security_related must be True or False."),
        ("requires_escalation", 1, "requires_escalation must be True or False."),
        ("summary", "   ", "Summary cannot be empty."),
        ("affected_system", None, "Affected system cannot be empty."),
        ("troubleshooting", "Restart the laptop", "Troubleshooting must be a list."),
        ("troubleshooting", ["Restart", 42], "Each troubleshooting step must be text."),
        ("ai_failed", "no", "ai_failed must be True or False."),
    ],
)
def test_a_reply_with_a_wrong_value_is_rejected_with_the_reason(field, bad_value, expected_error):
    reply = dict(GOOD_REPLY, **{field: bad_value})
    result = LogicManager().process_ticket(TICKET, reply)
    assert result["action"] == "REJECT"
    assert result["errors"] == [expected_error]


@pytest.mark.parametrize("reply", [None, "not json", ["Network"]], ids=["nothing", "text", "list"])
def test_a_reply_that_is_not_a_dictionary_is_rejected(reply):
    assert LogicManager().validate_ai_response(reply) == ["AI response must be a dictionary."]
    assert LogicManager().process_ticket(TICKET, reply)["action"] == "REJECT"


def test_the_good_reply_passes_every_check():
    assert LogicManager().validate_ai_response(dict(GOOD_REPLY)) == []


class FakeClient:
    # stands in for google.genai.Client so no test ever calls the real Gemini API,
    # client.models.generate_content() is the only call GeminiProvider makes
    def __init__(self, reply_text="", error=None):
        self.models = self
        self.calls = []
        self.__reply_text = reply_text
        self.__error = error

    def generate_content(self, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self.__error is not None:
            raise self.__error
        return SimpleNamespace(text=self.__reply_text)


def gemini_with(monkeypatch, client):
    monkeypatch.setattr(gemini_provider.genai, "Client", lambda: client)
    return GeminiProvider(model_name="gemini-test")


def test_gemini_asks_for_json_and_gives_back_the_text(monkeypatch):
    client = FakeClient(reply_text=json.dumps(GOOD_REPLY))
    provider = gemini_with(monkeypatch, client)

    assert provider.is_available() is True
    assert json.loads(provider._call_api("the prompt")) == GOOD_REPLY
    [call] = client.calls
    assert call["model"] == "gemini-test"
    assert call["contents"] == "the prompt"
    assert call["config"].response_mime_type == "application/json"


def test_gemini_without_a_client_raises_instead_of_sending(monkeypatch):
    def no_key():
        raise ValueError("Missing key inputs argument!")

    monkeypatch.setattr(gemini_provider.genai, "Client", no_key)
    provider = GeminiProvider()
    assert provider.is_available() is False
    with pytest.raises(RuntimeError, match="not initialized"):
        provider._call_api("the prompt")


@pytest.mark.parametrize(
    "error",
    [TimeoutError("The read operation timed out"), ConnectionError("Network is unreachable")],
    ids=["timeout", "no connection"],
)
def test_a_timeout_or_lost_connection_ends_in_the_offline_reply(monkeypatch, error):
    monkeypatch.setattr("managers.ai_manager.base_ai_provider.time.sleep", lambda seconds: None)
    client = FakeClient(error=error)
    manager = AIManager(provider=gemini_with(monkeypatch, client))

    reply = manager.analyse_ticket(title="WiFi problem", description="Cannot connect to the school WiFi")

    assert len(client.calls) == 3
    assert reply["ai_failed"] is True
    assert reply["category"] == "Network"
    result = LogicManager().process_ticket(TICKET, reply)
    assert result["requires_manual_review"] is True
    assert result["action"] == "MANUAL_REVIEW"


def test_gemini_reply_with_a_wrong_value_is_rejected_by_the_logic_manager(monkeypatch):
    # the reply has all 8 keys so the AI manager accepts it, then the logic manager checks the values
    client = FakeClient(reply_text=json.dumps(dict(GOOD_REPLY, priority="urgent")))
    manager = AIManager(provider=gemini_with(monkeypatch, client))

    reply = manager.analyse_ticket(title="WiFi problem", description="Cannot connect to the school WiFi")

    assert len(client.calls) == 1
    assert LogicManager().process_ticket(TICKET, reply) == {
        "action": "REJECT",
        "errors": ["Invalid priority: urgent"],
    }
