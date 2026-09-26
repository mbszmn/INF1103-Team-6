import json
from datetime import datetime
from pathlib import Path

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

    def __init__(self, file_path: str = "data/tickets.json"):
            self.file_path = Path(file_path)
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            if not self.file_path.exists():
                self._write_all([])

    def _read_all(self) ->list[dict]:
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, list):
                raise ValueError("ERROR.")

            return data

        except (json.JSONDecodeError, ValueError):
            raise RuntimeError("Ticket storage is corrupted. Check data/tickets.json.")

    def _write_all(self, tickets: list[dict]) -> None:
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(tickets, file, indent=4, ensure_ascii=False)

    def generate_ticket_id(self) -> str:
        tickets = self._read_all()

        largest_number = 0

        for ticket in tickets:
            ticket_id = ticket.get("ticket_id", "")
            try:
                number = int(ticket_id)
                largest_number = max(largest_number, number)
            except(ValueError, IndexError):
                continue

        return f"{largest_number + 1:04d}"


    def create_ticket(self, user_input: dict) -> Ticket:
        return Ticket(
                ticket_id=self.generate_ticket_id(),
                username=user_input["username"],
                device=user_input["device"],
                title=user_input["title"],
                description=user_input["description"],
                steps_attempted=user_input.get("steps_attempted", ""),
                user_priority=user_input.get("user_priority", "Medium"),
                error_message=user_input.get("error_message", ""),
            )
    def save_new_ticket(self, ticket: Ticket) -> None:
        tickets = self._read_all()
        tickets.append(ticket.to_dict())
        self._write_all(tickets)

    def update_ticket(self, ticket: Ticket) -> None:
        tickets = self._read_all()
        found = False

        ticket.updated_at = datetime.now().isoformat(timespec="seconds")

        for index, existing_ticket in enumerate(tickets):
            if existing_ticket.get("ticket_id") == ticket.ticket_id:
                tickets[index] = ticket.to_dict()
                found = True
                break

        if not found:
            raise KeyError(f"Ticket {ticket.ticket_id} was not found.")

        self._write_all(tickets)