from abc import ABC, abstractmethod

VALID_CATEGORIES: set[str] = {
    "Network",
    "Hardware",
    "Software",
    "Account",
    "Security",
    "Other",
}

VALID_PRIORITIES: set[str] = {
    "Low",
    "Medium",
    "High",
    "Critical",
}


class TicketClassifier(ABC):
    """Abstract base class for ticket classification."""

    @abstractmethod
    def classify(self, ticket: dict) -> str:
        """Classify a ticket and return its category."""
        pass


class KeywordClassifier(TicketClassifier):
    """Classify tickets using keywords in the ticket details."""

    KEYWORDS: dict[str, list[str]] = {
        "Security": [
            "virus", "phishing", "malware", "suspicious",
            "hacked", "ransomware", "unauthorised access",
            "data breach", "spam", "malicious link",
            "compromised account",
        ],
        
        "Network": [
            "wifi", "wi-fi", "internet", "network",
            "connection", "disconnected", "connectivity",
            "ethernet", "lan", "router", "hotspot",
            "vpn", "slow connection", "cannot connect",
        ],

        "Account": [
            "password", "login", "log in", "sign in",
            "account", "locked out", "forgot password",
            "reset password", "username", "authentication",
            "mfa", "otp", "verification",
        ],

        "Hardware": [
            "laptop", "keyboard", "screen", "monitor",
            "mouse", "printer", "webcam", "microphone",
            "speaker", "charger", "battery", "usb",
            "motherboard", "overheating", "power button",
        ],

        "Software": [
            "software", "application", "app", "program",
            "installation", "install", "update", "crash",
            "freezing", "not responding", "error message",
            "microsoft office", "word", "excel",
            "powerpoint", "browser",
        ]
    }

    def classify(self, ticket: dict) -> str:
        text: str = " ".join([
            ticket.get("title", ""),
            ticket.get("description", ""),
            ticket.get("device", ""),
            ticket.get("error_message", ""),
        ]).lower()

        for category, keywords in self.KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category

        return "Other"


class LogicManager:
    """Manage ticket classification and business logic."""

    def __init__(self) -> None:
        self.classifier: TicketClassifier = KeywordClassifier()

    def classify_ticket(self, ticket: dict) -> str:
        """Classify a ticket using the keyword classifier."""
        return self.classifier.classify(ticket)

    def validate_ai_response(self, ai_response: dict) -> list[str]:
        """Validate the structure and values of an AI-enriched ticket."""

        required_fields: list[str] = [
            "extracted_hardware",
            "extracted_software",
            "sentiment_score",
            "summary",
            "troubleshooting",
        ]

        if not isinstance(ai_response, dict):
            return ["AI response must be a dictionary."]

        errors: list[str] = []

        for field in required_fields:
            if field not in ai_response:
                errors.append(f"Missing required field: {field}")

        if errors:
            return errors

        for field in ["extracted_hardware", "extracted_software"]:
            if not isinstance(ai_response[field], list):
                errors.append(f"{field} must be a list.")
            elif not all(isinstance(item, str) for item in ai_response[field]):
                errors.append(f"{field} must contain only strings.")

        sentiment = ai_response["sentiment_score"]

        if not isinstance(sentiment, int) or isinstance(sentiment, bool):
            errors.append("Sentiment score must be an integer.")
        elif not 1 <= sentiment <= 10:
            errors.append("Sentiment score must be between 1 and 10.")

        if not isinstance(ai_response["summary"], str) or not ai_response["summary"].strip():
            errors.append("Summary cannot be empty.")

        if not isinstance(ai_response["troubleshooting"], list):
            errors.append("Troubleshooting must be a list.")
        elif not all(isinstance(step, str) for step in ai_response["troubleshooting"]):
            errors.append("Troubleshooting must contain only strings.")

        if "ai_failed" in ai_response and not isinstance(ai_response["ai_failed"], bool):
            errors.append("ai_failed must be True or False.")

        return errors
    
    def apply_security_rule(self, ticket: dict, ai_response: dict) -> dict:
        """Escalate tickets classified as security-related."""

        result: dict = ai_response.copy()

        category: str = self.classify_ticket(ticket)

        result["category"] = category
        result["security_related"] = category == "Security"
        result["requires_escalation"] = category == "Security"

        if result["requires_escalation"]:
            result["action"] = "ESCALATE"

        return result

    def apply_priority_rule(self, ticket: dict, ai_response: dict) -> dict:
        """Place critical tickets at the top of the support queue."""

        result: dict = ai_response.copy()

        priority: str = ticket.get("user_priority", "Medium")

        if priority not in VALID_PRIORITIES:
            result["requires_manual_review"] = True

            if result.get("action") != "ESCALATE":
                result["action"] = "MANUAL_REVIEW"

            return result

        result["priority"] = priority

        if priority == "Critical":
            result["queue_position"] = "TOP"

        return result
    
    def apply_manual_review_rule(self, ai_response: dict) -> dict:
        """Send failed or insufficient AI analysis for manual review."""

        result: dict = ai_response.copy()

        ai_failed: bool = result.get("ai_failed", False)
        sentiment = result.get("sentiment_score", 10)
        troubleshooting: list[str] = result.get("troubleshooting", [])

        if (
            ai_failed
            or result.get("requires_manual_review", False)
            or (sentiment <= 3 and not troubleshooting)
        ):
            result["requires_manual_review"] = True

            if result.get("action") != "ESCALATE":
                result["action"] = "MANUAL_REVIEW"

        else:
            result["requires_manual_review"] = False

        return result

    def process_ticket(self, ticket: dict, ai_response: dict) -> dict:
        """Validate AI analysis and apply all business rules."""

        validation_errors: list[str] = self.validate_ai_response(ai_response)

        if validation_errors:
            return {
                "action": "REJECT",
                "errors": validation_errors,
            }

        result: dict = self.apply_security_rule(ticket, ai_response)
        result = self.apply_priority_rule(ticket, result)
        result = self.apply_manual_review_rule(result)

        return result