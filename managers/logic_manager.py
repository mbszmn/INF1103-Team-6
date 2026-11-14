from classifiers.ticket_classifier import TicketClassifier
from classifiers.keyword_classifier import KeywordClassifier

VALID_CATEGORIES: list[str] = ["Network", "Hardware", "Software", "Account", "Security", "Other",]

VALID_PRIORITIES: list[str] = ["Low", "Medium", "High", "Critical",]


class LogicManager:
    """Manage ticket classification and business logic."""

    FALLBACK_TROUBLESHOOTING: dict[str, list[str]] = {
        "Network": [
            "Check whether Wi-Fi is enabled and Airplane Mode is off.",
            "Try reconnecting to the network or restarting your device.",
            "Check if other devices can connect to the internet.",
        ],

        "Hardware": [
            "Check that the power cable and connections are secure.",
            "Look for any visible damage or signs of overheating.",
            "If safe to do so, restart the device and see whether the problem persists.",
        ],

        "Software": [
            "Save your work, then close and reopen the application.",
            "Take note of any error messages.",
            "Check if there are any available updates.",
        ],

        "Account": [
            "Double-check your username and password.",
            "Make sure Caps Lock is off when entering your password.",
            "Try resetting your password through SIT's approved process.",
        ],

        "Security": [
            "Do not click suspicious links or open unknown attachments.",
            "Do not reply to or interact with the suspicious message.",
            "Report it to IT support through the official channel.",
        ],

        "Other": [
            "Try restarting the affected device or application.",
            "Take note of any error messages.",
            "If the problem continues, wait for IT support to assist.",
        ],
    }

    def __init__(self) -> None:
        self.classifier: TicketClassifier = KeywordClassifier()

    def classify_ticket(self, ticket: dict) -> str:
        """Classify a ticket using the keyword classifier."""
        return self.classifier.classify(ticket)

    def validate_ai_response(self, ai_response: dict) -> list[str]:
        """Validate the structure and values of an AI-enriched ticket."""

        required_fields: list[str] = [
            "category",
            "priority",
            "confidence",
            "summary",
            "affected_system",
            "security_related",
            "requires_escalation",
            "troubleshooting",
        ]

        if not isinstance(ai_response, dict):
            return ["AI response must be a dictionary."]

        errors: list[str] = []

        for field in required_fields:
            if field not in ai_response.keys():
                errors.append("Missing required field: " + field)

        if errors:
            return errors

        if ai_response["category"] not in VALID_CATEGORIES:
            errors.append("Invalid category: " + str(ai_response["category"]))

        if ai_response["priority"] not in VALID_PRIORITIES:
            errors.append("Invalid priority: " + str(ai_response["priority"]))

        confidence = ai_response["confidence"]

        if type(confidence) != int and type(confidence) != float:
            errors.append("Confidence score must be a number.")
        elif confidence < 0 or confidence > 1:
            errors.append("Confidence score must be between 0 and 1.")

        if type(ai_response["security_related"]) != bool:
            errors.append("security_related must be True or False.")

        if type(ai_response["requires_escalation"]) != bool:
            errors.append("requires_escalation must be True or False.")

        if type(ai_response["summary"]) != str or ai_response["summary"].strip() == "":
            errors.append("Summary cannot be empty.")

        if type(ai_response["affected_system"]) != str or ai_response["affected_system"].strip() == "":
            errors.append("Affected system cannot be empty.")

        if type(ai_response["troubleshooting"]) != list:
            errors.append("Troubleshooting must be a list.")
        else:
            for step in ai_response["troubleshooting"]:
                if type(step) != str:
                    errors.append("Each troubleshooting step must be text.")

        if "ai_failed" in ai_response.keys() and type(ai_response["ai_failed"]) != bool:
            errors.append("ai_failed must be True or False.")

        return errors

    def fallback_classification(self, ticket: dict) -> dict:
        """Classify a ticket using keywords when AI is unavailable."""

        category: str = self.classify_ticket(ticket)

        description: str = ticket.get("description", "")
        device: str = str(ticket.get("device") or "Unknown")

        return {
            "category": category,
            "priority": "Medium",
            "confidence": 0.0,
            "summary": description if description else "AI analysis unavailable.",
            "affected_system": device,
            "security_related": category == "Security",
            "requires_escalation": category == "Security",
            "requires_manual_review": True,
            "troubleshooting": self.get_fallback_troubleshooting(category),
            "action": "MANUAL_REVIEW",
            "ai_failed": True,
            "support_message": (
                "Our AI service is temporarily unavailable. "
                "Your ticket has been flagged for manual review by "
                "the IT support team. In the meantime, you can try "
                "the general troubleshooting steps provided above. "
                "These suggestions may not resolve every issue. "
                "If the problem persists, please wait for IT "
                "support to review your ticket."
            ),
        }

    def get_fallback_troubleshooting(self, category: str) -> list[str]:
        """Return general troubleshooting steps based on ticket category."""

        return self.FALLBACK_TROUBLESHOOTING.get(
            category,
            self.FALLBACK_TROUBLESHOOTING["Other"]
        ).copy()
    
    def apply_security_rule(self, ai_response: dict) -> dict:
        """Escalate tickets classified as security-related."""

        result: dict = ai_response.copy()

        if result["security_related"] is True or result["category"] == "Security":
            result["security_related"] = True
            result["requires_escalation"] = True
            result["action"] = "ESCALATE"

        return result

    def apply_confidence_rule(self, ai_response: dict) -> dict:
        """Send failed or low-confidence AI results for manual review."""

        result: dict = ai_response.copy()

        ai_failed: bool = False

        if "ai_failed" in result.keys():
            ai_failed = result["ai_failed"]

        confidence = result["confidence"]

        if ai_failed or confidence < 0.70:
            result["requires_manual_review"] = True

            if "action" not in result.keys() or result["action"] != "ESCALATE":
                result["action"] = "MANUAL_REVIEW"
        else:
            result["requires_manual_review"] = False

        return result


    def apply_priority_rule(self, ai_response: dict) -> dict:
        """Place critical tickets at the top of the support queue."""

        result: dict = ai_response.copy()

        if result["priority"] == "Critical":
            result["queue_position"] = "TOP"

        return result
    

    def process_ticket(self, ticket: dict, ai_response: dict) -> dict:
        """Validate AI analysis and apply all business rules."""

        if not isinstance(ai_response, dict):
            return {
                "action": "REJECT",
                "errors": ["AI response must be a dictionary."],
            }

        if ai_response.get("ai_failed") is True:
            result: dict = self.fallback_classification(ticket)

        else:
            validation_errors: list[str] = self.validate_ai_response(ai_response)

            if validation_errors:
                return {
                    "action": "REJECT",
                    "errors": validation_errors,
                }

            result = ai_response.copy()

        result = self.apply_security_rule(result)
        result = self.apply_confidence_rule(result)
        result = self.apply_priority_rule(result)

        return result