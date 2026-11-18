class AIResponseValidator:
    # Checks that the AI reply contains all 8 required fields

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
        # Use custom keys if provided, otherwise use the default 8 keys
        self._required_keys = (
            list(required_keys) if required_keys is not None else list(self.DEFAULT_REQUIRED_KEYS)
        )

    def validate_schema(self, data: dict) -> bool:
        # Return True only if data is a dictionary with every required key
        if not isinstance(data, dict):
            return False
        return all(
            key in data
            and (key not in self.KEY_TYPES or isinstance(data[key], self.KEY_TYPES[key]))
            for key in self._required_keys
        )