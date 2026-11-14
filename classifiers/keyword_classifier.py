from classifiers.ticket_classifier import TicketClassifier


class KeywordClassifier(TicketClassifier):
    """Classify tickets using keywords in the ticket details."""

    KEYWORDS: dict[str, list[str]] = {
        "Security": [
            "virus", "phishing", "malware", "suspicious",
            "hacked", "ransomware", "unauthorised access",
            "unauthorized access", "credential theft",
            "data breach", "spam", "malicious link",
            "compromised account", "suspicious link",
            "click sus link", "unexpected attachment",
            "hack",
        ],
        
        "Network": [
            "wifi", "wi-fi", "internet", "network",
            "connection", "disconnected", "connectivity",
            "ethernet", "lan", "router", "hotspot",
            "vpn", "slow connection", "cannot connect", "offline",
            "no internet", "internet not working",
            "network error",
        ],

        "Account": [
            "password", "login", "log in", "sign in",
            "account", "locked out", "forgot password",
            "reset password", "username", "authentication",
            "mfa", "otp", "verification", "locked account",
            "2fa", "2 fa", "incorrect password",
            "account access", "cannot log in",
        ],

        "Hardware": [
            "laptop", "keyboard", "screen", "monitor",
            "mouse", "printer", "webcam", "microphone",
            "speaker", "charger", "battery", "usb",
            "motherboard", "overheating", "power button", "charging",
            "power failure", "black screen", "not charging",
            "device won't turn on",
        ],

        "Software": [
            "software", "application", "app", "program",
            "installation", "install", "update", "crash",
            "freezing", "not responding", "error message",
            "microsoft office", "word", "excel",
            "powerpoint", "browser",
            "failed to install",
        ]
    }

    def classify(self, ticket: dict) -> str:
        text: str = " ".join([
            str(ticket.get("title") or ""),
            str(ticket.get("description") or""),
            str(ticket.get("device") or ""),
            str(ticket.get("error_message") or ""),
        ]).lower()

        for category, keywords in self.KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category

        return "Other"