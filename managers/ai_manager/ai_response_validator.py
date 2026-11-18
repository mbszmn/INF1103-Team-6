class AIResponseValidator:
    """Validates that parsed AI JSON contains all 8 required keys with valid types."""

    DEFAULT_REQUIRED_KEYS = (
        "category",
        "priority",
        "confidence",
        "summary",
        "affected_system",
        "security_related",
        "requires_escalation",
        "troubleshooting",
    )

    KEY_TYPES = {
        "troubleshooting": list,
        "security_related": bool,
        "requires_escalation": bool,
    }

    def __init__(self, required_keys: list[str] | None = None):
        self._required_keys = (
            list(required_keys) if required_keys is not None else list(self.DEFAULT_REQUIRED_KEYS)
        )

    def validate_schema(self, data: dict) -> bool:
        if not isinstance(data, dict):
            return False
        return all(
            key in data
            and (key not in self.KEY_TYPES or isinstance(data[key], self.KEY_TYPES[key]))
            for key in self._required_keys
        )