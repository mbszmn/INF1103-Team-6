class AIResponseValidator:
    # Validates that parsed AI JSON contains all 8 required keys

    DEFAULT_REQUIRED_KEYS = [
        "category",
        "priority",
        "confidence",
        "summary",
        "affected_system",
        "security_related",
        "requires_escalation",
        "troubleshooting",
    ]

    def __init__(self, required_keys: list[str] | None = None):
        self._required_keys = (
            list(required_keys) if required_keys is not None else list(self.DEFAULT_REQUIRED_KEYS)
        )

    def validate_schema(self, data: dict) -> bool:
        return isinstance(data, dict) and all(key in data for key in self._required_keys)