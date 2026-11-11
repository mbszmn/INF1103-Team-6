from managers.logic_manager import LogicManager

logic_manager = LogicManager()


# sample AI response
ai_response = {
    "extracted_hardware": ["laptop"],
    "extracted_software": [],
    "sentiment_score": 5,
    "summary": "Laptop is experiencing problems.",
    "troubleshooting": ["Restart the laptop"],
}


# Test 1: normal ticket
ticket = {
    "title": "Laptop problem",
    "description": "My laptop is not working properly.",
    "device": "Laptop",
    "user_priority": "Medium",
}

result = logic_manager.process_ticket(ticket, ai_response)

print("\nTest 1: normal ticket")
print(result)
assert result["category"] == "Hardware"
assert result["priority"] == "Medium"


# Test 2: security ticket
ticket = {
    "title": "Suspicious phishing email",
    "description": "I received a suspicious email.",
    "device": "Laptop",
    "user_priority": "High",
}

result = logic_manager.process_ticket(ticket, ai_response)

print("\nTest 2: security ticket")
print(result)
assert result["category"] == "Security"
assert result["requires_escalation"] is True
assert result["action"] == "ESCALATE"


# Test 3: critical priority
ticket = {
    "title": "Laptop problem",
    "description": "Laptop cannot start.",
    "device": "Laptop",
    "user_priority": "Critical",
}

result = logic_manager.process_ticket(ticket, ai_response)

print("\nTest 3: critical priority")
print(result)
assert result["priority"] == "Critical"
assert result["queue_position"] == "TOP"


# Test 4: manual review
low_sentiment_response = ai_response.copy()
low_sentiment_response["sentiment_score"] = 2
low_sentiment_response["troubleshooting"] = []

ticket = {
    "title": "Laptop problem",
    "description": "Nothing is working.",
    "device": "Laptop",
    "user_priority": "Medium",
}

result = logic_manager.process_ticket(ticket, low_sentiment_response)

print("\nTest 4: manual review")
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

failed_ai_response = ai_response.copy()
failed_ai_response["ai_failed"] = True
failed_ai_response["troubleshooting"] = []

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

print("\nAll 6 tests passed!")