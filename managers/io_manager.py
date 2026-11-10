from ticket.ticket_input_validator import TicketInputValidator

class IOManager:
    def __init__(self):
        self._validator = TicketInputValidator()

    def _read_validated_input(self, field: str, prompt: str) -> str:
        while True:
            value = input(prompt).strip()
            if field == "student_id" and value.lower() == "staff":
                value = "staff"
            elif field == "user_priority":
                value = value.title()

            error = self._validator.validate_field(field, value)
            if not error:
                return value
            print(error)
