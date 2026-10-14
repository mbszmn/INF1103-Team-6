from datetime import datetime


def create_ticket(
    ticket_id,
    username,
    student_id,
    device,
    title,
    description,
    steps_attempted = "",
    user_priority = "Medium",
    error_message = "",
):
    """Create a new ticket as a dictionary."""

    current_time = datetime.now().isoformat(timespec="seconds")

    return {
        "ticket_id": ticket_id,
        "username": username,
        "student_id": student_id,
        "device": device,
        "title": title,
        "description": description,
        "steps_attempted": steps_attempted,
        "user_priority": user_priority,
        "error_message": error_message,
        "ai_analysis": {},
        "final_priority": "Medium",
        "status": "Open",
        "escalated": False,
        "requires_manual_review": False,
        "created_at": current_time,
        "updated_at": current_time,
    }