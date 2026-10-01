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
    """Validate the structure of an AI-enriched ticket."""
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

    return errors