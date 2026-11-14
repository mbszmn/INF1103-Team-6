# Add the project root to sys.path so Python can find the managers folder.
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from managers.logic_manager import LogicManager

logic_manager = LogicManager()


# sample AI response
ai_response = {
    "category": "Hardware",
    "priority": "Medium",
    "confidence": 0.92,
    "summary": "Laptop is experiencing problems.",
    "affected_system": "Laptop",
    "security_related": False,
    "requires_escalation": False,
    "troubleshooting": [
        "Restart the laptop.",
        "Check the power connection.",
    ],
}


# Test 1: normal ticket
ticket = {
    "title": "Laptop problem",
    "description": "My laptop is not working properly.",
    "device": "Laptop",
    }

result = logic_manager.process_ticket(ticket, ai_response)

print("\nTest 1: normal ticket")
print(result)

assert result["category"] == "Hardware"
assert result["priority"] == "Medium"
assert result["requires_manual_review"] is False


# Test 2: security ticket
security_response = ai_response.copy()
security_response.update({
    "category": "Security",
    "security_related": True,
    "requires_escalation": False,
})

ticket = {
    "title": "Suspicious phishing email",
    "description": "I received a suspicious email.",
    "device": "Laptop",
}

result = logic_manager.process_ticket(ticket, security_response)

print("\nTest 2: security ticket")
print(result)

assert result["category"] == "Security"
assert result["requires_escalation"] is True
assert result["action"] == "ESCALATE"


# Test 3: critical priority
critical_response = ai_response.copy()
critical_response["priority"] = "Critical"

ticket = {
    "title": "Laptop problem",
    "description": "Laptop cannot start.",
    "device": "Laptop",
}

result = logic_manager.process_ticket(ticket, critical_response)

print("\nTest 3: critical priority")
print(result)

assert result["priority"] == "Critical"
assert result["queue_position"] == "TOP"


# Test 4: low confidence req manual review
low_confidence_response = ai_response.copy()
low_confidence_response["confidence"] = 0.50

ticket = {
    "title": "Laptop problem",
    "description": "Nothing is working.",
    "device": "Laptop",
}

result = logic_manager.process_ticket(ticket, low_confidence_response)

print("\nTest 4: low confidence")
print(result)

assert result["requires_manual_review"] is True
assert result["action"] == "MANUAL_REVIEW"


# Test 5: invalid AI response
invalid_response = {
    "summary": "Test response"
}

result = logic_manager.process_ticket(ticket, invalid_response)

print("\nTest 5: invalid AI response")
print(result)

assert result["action"] == "REJECT"

# Test 6: AI unavailable with category specific troubleshooting

failed_ai_response = {"ai_failed": True}

ticket = {
    "title": "Cannot connect to Wi-Fi",
    "description": "My laptop cannot connect to the internet.",
    "device": "Laptop",
    "user_priority": "Medium",
}

result = logic_manager.process_ticket(ticket, failed_ai_response)

print("\nTest 6: AI unavailable")
print(result)

assert result["category"] == "Network"
assert len(result["troubleshooting"]) == 3
assert result["requires_manual_review"] is True
assert result["action"] == "MANUAL_REVIEW"
assert "temporarily unavailable" in result["support_message"]

# Test 7: security category with security_related False

security_response = ai_response.copy()
security_response["category"] = "Security"
security_response["security_related"] = False

result = logic_manager.process_ticket(ticket, security_response)

print("\nTest 7: Security category with false security flag")
print(result)

assert result["security_related"] is True
assert result["requires_escalation"] is True
assert result["action"] == "ESCALATE"

# Test 8: security keyword takes priority over account keywords

ticket = {
    "title": "Phishing email asking for my password",
    "description": "I received a suspicious email.",
}

result = logic_manager.classify_ticket(ticket)

print("\nTest 8: Phishing email classification")
print(result)

assert result == "Security"

# Test 9: Invalid troubleshooting step

invalid_troubleshooting = ai_response.copy()
invalid_troubleshooting["troubleshooting"] = [
    {"step": 1},
    "Restart your laptop."
]

result = logic_manager.process_ticket(ticket, invalid_troubleshooting)

print("\nTest 9: Invalid troubleshooting step")
print(result)

print("\nAll 9 tests passed!")


def test_keyword_classifier():
    test_cases = [
        {
            "title": "My account has been hacked",
            "expected": "Security"
        },
        {
            "title": "I cannot connect to Wi-Fi",
            "expected": "Network"
        },
        {
            "title": "My laptop won't turn on",
            "expected": "Hardware"
        },
        {
            "title": "I cannot log in",
            "expected": "Account"
        },
        {
            "title": "Microsoft Word keeps crashing",
            "expected": "Software"
        },
    ]

    for test in test_cases:
        result = logic_manager.classify_ticket(test)

        assert result == test["expected"], (
            f"Expected {test['expected']}, got {result}"
        )

    print("All keyword classifier tests passed!")

test_keyword_classifier()