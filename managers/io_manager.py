class IOManager:
    VALID_USER_PRIORITIES = {"Low", "Medium", "High", "Critical"}

    @staticmethod # means the function can be used without needing self or creating an object first
    def _required_input(prompt: str) -> str:
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("This field cannot be empty.")

    def collect_ticket_input(self) -> dict:
        username = self._required_input("Name / Username: ")
        device = self._required_input("Device: ")
        title = self._required_input("Ticket title: ")
        description = self._required_input("Describe the problem: ")

        steps_attempted = input("steps already attempted (press Enter if none): ").strip()

        error_message = input("Error message (press Enter if none): ").strip()

        while True:
            user_priority = input("How urgent is it for you? (Low / Medium / High / Critical): ").strip().title()

            if user_priority in self.VALID_USER_PRIORITIES:
                break
            print("Priority must be Low, Medium, High, or Critical.")

        data = {
                "username": username,
                "device": device,
                "title": title,
                "description": description,
                "steps_attempted": steps_attempted,
                "user_priority": user_priority,
                "error_message": error_message,
            }

        errors = self.validate_ticket_input(data)
        if errors:
            raise ValueError("\n".join(errors))

        return data

    def validate_ticket_input(self, data: dict) -> list[str]:
        errors = []

        required_fields = [
                "username",
                "device",
                "title",
                "description",
            ]

        for field in required_fields:
            if not str(data.get(field, "")).strip():
                errors.append(f"{field} cannot be empty.")

            description = str(data.get("description", "")).strip()
            if description and len(description) < 10:
                    errors.append(
                        "Description is too short. Please provide at least 10 characters."
                    )
            
        return errors