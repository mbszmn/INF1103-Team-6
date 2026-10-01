VALID_CATEGORIES = {
    "Network",
    "Hardware",
    "Software",
    "Account",
    "Security",
    "Other",
}

VALID_PRIORITIES = {
    "Low",
    "Medium",
    "High",
    "Critical",
}


def validate_ai_response(ai_response: dict) -> list[str]:
    """Validate the structure and values of an AI-enriched ticket."""
    errors = []

    required_fields = [
        "category",
        "priority",
        "confidence",
        "summary",
        "affected_system",
        "security_related",
        "requires_escalation",
        "troubleshooting",
    ]

    for field in required_fields:
        if field not in ai_response:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    if ai_response["category"] not in VALID_CATEGORIES:
        errors.append(
            f"Invalid category: {ai_response['category']}"
        )

    if ai_response["priority"] not in VALID_PRIORITIES:
        errors.append(
            f"Invalid priority: {ai_response['priority']}"
        )

    confidence = ai_response["confidence"]
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        errors.append("Confidence must be a number.")
    elif not 0 <= confidence <= 1:
        errors.append("Confidence must be between 0 and 1.")

    if not isinstance(ai_response["security_related"], bool):
        errors.append("security_related must be True or False.")

    if not isinstance(ai_response["requires_escalation"], bool):
        errors.append("requires_escalation must be True or False.")

    if not isinstance(ai_response["summary"], str) or not ai_response["summary"].strip():
        errors.append("Summary cannot be empty.")

    if not isinstance(ai_response["affected_system"], str) or not ai_response["affected_system"].strip():
        errors.append("Affected system cannot be empty.")

    if not isinstance(ai_response["troubleshooting"], list):
        errors.append("Troubleshooting must be a list.")

    return errors


def apply_security_rule(ai_response: dict) -> dict:
    """Escalate tickets identified as security-related."""
    result = ai_response.copy()

    if ai_response["security_related"] is True:
        result["requires_escalation"] = True
        result["action"] = "ESCALATE"

    return result


def apply_confidence_rule(ai_response: dict) -> dict:
    """Send low-confidence AI results for manual review."""
    result = ai_response.copy()

    if ai_response["confidence"] < 0.70:
        result["requires_manual_review"] = True
        result["action"] = "MANUAL_REVIEW"

    return result