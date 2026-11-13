from models.ticket import Ticket
from views.ticket_formatter import TicketFormatter


def test_detail_shows_what_the_user_typed_the_ai_result_and_the_history(make_ticket):
    ticket = make_ticket(steps_attempted="Restarted laptop", error_message="No internet", user_priority="High")
    ticket.attach_analysis({
        "category": "Network",
        "priority": "High",
        "summary": "WiFi drops on campus",
        "extracted_hardware": ["WiFi adapter"],
        "extracted_software": ["Windows 11"],
        "troubleshooting": ["Forget the network", "Reconnect"],
    })
    ticket.close()
    text = TicketFormatter().format_detail(ticket)
    for expected in [
        "Ticket ID: 0001",
        "User: Alex | Student ID: 2600001",
        "Steps already tried: Restarted laptop",
        "Error message: No internet",
        "User urgency: High",
        "Status: Closed | Priority: High",
        "AI Category: Network",
        "AI Summary: WiFi drops on campus",
        "Hardware mentioned: WiFi adapter",
        "Software mentioned: Windows 11",
        "  1. Forget the network",
        "  2. Reconnect",
        "Open -> Closed",
    ]:
        assert expected in text


def test_detail_works_for_a_phase_1_ticket_with_missing_parts():
    ticket = Ticket.from_dict({
        "ticket_id": "0004", "username": "pl", "device": "hp", "title": "network",
        "description": "cannot connect", "status": "Open", "created_at": "2026-10-02T03:00:00",
    })
    text = TicketFormatter().format_detail(ticket)
    assert "Student ID: -" in text
    assert "History:" not in text
    assert "AI Category" not in text


def test_detail_skips_broken_ai_values_instead_of_crashing(make_ticket):
    ticket = make_ticket()
    ticket.attach_analysis({"category": "Other", "troubleshooting": [{"step": "restart"}, "Call IT"], "summary": 5})
    text = TicketFormatter().format_detail(ticket)
    assert "  1. Call IT" in text
    assert "AI Summary" not in text


def test_list_marks_open_critical_tickets_as_top_of_the_queue(make_ticket):
    urgent = make_ticket("0001", user_priority="Critical")
    done = make_ticket("0002", user_priority="Critical")
    done.close()
    text = TicketFormatter().format_list([urgent, done], "All Tickets")
    assert "All Tickets" in text
    assert "TOP | ID: 0001 | WiFi problem | Priority: Critical | Status: Open" in text
    assert "\nID: 0002 | WiFi problem | Priority: Critical | Status: Closed" in text


def test_empty_list_shows_the_message():
    assert "No tickets yet." in TicketFormatter().format_list([], "All Tickets")
    assert "No tickets match." in TicketFormatter().format_list([], "Filter", "No tickets match.")
