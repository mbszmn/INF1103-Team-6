VALID_USER_PRIORITIES = {"Low", "Medium", "High", "Critical"}

def _required_input(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


def collect_ticket_input():
    username = _required_input("Name / Username: ")
    while True:
        student_id = input("Student ID (type staff if you are staff): ").strip()
        if student_id.isdigit():
            break
        if student_id.lower() == "staff":
            student_id = "staff"
            break
        print("Student ID must be numbers only. Staff can type staff.")
    device = _required_input("Device model (e.g. Dell Latitude 5420): ")
    title = _required_input("Ticket title: ")
    description = _required_input("Describe the problem: ")

    steps_attempted = input("steps already attempted (press Enter if none): ").strip()

    error_message = input("Error message (press Enter if none): ").strip()

    while True:
        user_priority = input("How urgent is it for you? (Low / Medium / High / Critical): ").strip().title()

        if user_priority in VALID_USER_PRIORITIES:
            break
        print("Priority must be Low, Medium, High, or Critical.")

    data = {
            "username": username,
            "student_id": student_id,
            "device": device,
            "title": title,
            "description": description,
            "steps_attempted": steps_attempted,
            "user_priority": user_priority,
            "error_message": error_message,
        }

    errors = validate_ticket_input(data)
    if errors:
        raise ValueError("\n".join(errors))

    return data


def validate_ticket_input(data):
    errors = []

    required_fields = [
            "username",
            "student_id",
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
