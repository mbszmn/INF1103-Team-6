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

	# Return errors without prompting, so other callers can validate too
    def validate_ticket_input(self, data):
        return self._validator.validate(data)

    def collect_ticket_input(self):
        data = {
            "username": self._read_validated_input("username", "Name / Username: "),
            "student_id": self._read_validated_input(
                "student_id", "Student ID (type staff if you are staff): "
            ),
            "device": self._read_validated_input(
                "device", "Device model (e.g. Dell Latitude 5430): "
            ),
            "title": self._read_validated_input("title", "Ticket title: "),
            "description": self._read_validated_input(
                "description", "Describe the problem: "
            ),
            "steps_attempted": input(
                "steps already attempted (press Enter if none): "
            ).strip(),
            "error_message": input("Error message (press Enter if none): ").strip(),
            "user_priority": self._read_validated_input(
                "user_priority", "How urgent is it for you? (Low / Medium / High / Critical): "
            ),
        }

        errors = self.validate_ticket_input(data)
        if errors:
            raise ValueError("\n".join(errors))
        return data

    def display_message(self, message):
        print(message)

    def show_welcome(self):
        print("========================================")
        print("AI SIT HELPDESK TICKET TRIAGE SYSTEM")
        print("========================================\n")

    def get_menu_option(self):
        print("\n----------- MENU -----------")
        print("1. Submit New Ticket")
        print("2. View All Tickets")
        print("3. Search Ticket by ID")
        print("4. Close Ticket")
        print("5. Reopen Ticket")
        print("6. Export Tickets to CSV")
        print("7. Exit")
        print("----------------------------")
        return input("Enter option: ").strip()

    def get_ticket_id(self, prompt="Enter ticket ID: "):
        return input(prompt).strip()

    def display_submission_result(self, ticket):
        analysis = ticket["ai_analysis"]
        print(f"\nTicket {ticket['ticket_id']} successfully processed and saved!")
        print(f"Category: {analysis['category']} | Priority: {ticket['final_priority']}")
        steps = analysis.get("troubleshooting", [])
        if steps:
            print("\nSuggested Immediate Troubleshooting Steps:")
            for number, step in enumerate(steps, 1):
                print(f"  {number}. {step}")