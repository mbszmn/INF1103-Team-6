class TicketInputValidator:

    _REQUIRED_FIELDS = ("username", "student_id", "device", "title", "description")
    _VALID_USER_PRIORITIES = ("Low", "Medium", "High", "Critical")

    # no __init__ because it does not need to store any data separately for each object

    def validate_field(self, field: str, value: str) -> str:
        # Return one error message, or an empty string when the field is valid
        if not isinstance(value, str):
            return f"{field} must be text."

        value = value.strip()
        if field in self._REQUIRED_FIELDS and not value:
            return f"{field} cannot be empty."

        if field == "student_id" and not (value.isdigit() or value.lower() == "staff"):
            return "Student ID must be numbers only. Staff can type staff."

        if field == "description" and len(value) < 10:
            return "Description is too short. Please provide at least 10 characters."

        if field == "user_priority" and value.title() not in self._VALID_USER_PRIORITIES:
            return "Priority must be Low, Medium, High, or Critical."

        return ""

    def validate(self, data: dict[str, str]) -> list[str]:
        # Check a ticket input dictionary without changing it or printing
        if not isinstance(data, dict):
            return ["Ticket input must be a dictionary."]

        errors: list[str] = []
        fields = self._REQUIRED_FIELDS + ("user_priority", "steps_attempted", "error_message")
        for field in fields:
            error = self.validate_field(field, data.get(field, ""))
            if error:
                errors.append(error)
        return errors