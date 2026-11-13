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


def validate_ai_response(ai_response):
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


def apply_security_rule(ai_response):
    """Escalate tickets identified as security-related."""
    result = ai_response.copy()

    if (
        ai_response["category"] == "Security"
        and ai_response["security_related"] is True
    ):
        result["requires_escalation"] = True
        result["action"] = "ESCALATE"

    elif ai_response["security_related"] is True:
        result["requires_escalation"] = True
        result["action"] = "ESCALATE"

    return result


def apply_confidence_rule(ai_response):
    """Send low-confidence AI results for manual review."""
    result = ai_response.copy()

    if ai_response["confidence"] < 0.70:
        result["requires_manual_review"] = True

        if result.get("action") != "ESCALATE":
            result["action"] = "MANUAL_REVIEW"

    return result


def apply_priority_rule(ai_response):
    """Place critical tickets at the top of the support queue."""
    result = ai_response.copy()

    if ai_response["priority"] == "Critical":
        result["queue_position"] = "TOP"

    return result


def fallback_classification(description):
    """Classify a ticket using keywords when the AI service is unavailable."""
    text = description.lower()

    if any(keyword in text for keyword in ["wifi", "internet", "network"]):
        category = "Network"
    elif any(keyword in text for keyword in ["password", "login", "account"]):
        category = "Account"
    elif any(keyword in text for keyword in ["laptop", "keyboard", "screen"]):
        category = "Hardware"
    elif any(keyword in text for keyword in ["software", "application", "program"]):
        category = "Software"
    elif any(keyword in text for keyword in ["virus", "phishing", "suspicious"]):
        category = "Security"
    else:
        category = "Other"

    return {
        "category": category,
        "priority": "Medium",
        "confidence": 0.0,
        "summary": description,
        "affected_system": "Unknown",
        "security_related": category == "Security",
        "requires_escalation": category == "Security",
        "requires_manual_review": True,
        "troubleshooting": [],
        "action": "MANUAL_REVIEW",
    }


def process_ticket(ai_response):
    """Validate an AI response and apply all Logic Manager rules."""
    validation_errors = validate_ai_response(ai_response)

    if validation_errors:
        return {
            "action": "REJECT",
            "errors": validation_errors,
        }

    result = apply_security_rule(ai_response)
    result = apply_confidence_rule(result)
    result = apply_priority_rule(result)

    return result