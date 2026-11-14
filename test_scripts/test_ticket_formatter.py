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


def test_detail_shows_how_sure_the_ai_was_and_the_affected_system(make_ticket):
    ticket = make_ticket("0001")
    ticket.attach_analysis({"category": "Network", "confidence": 0.85, "affected_system": "Campus WiFi"})
    text = TicketFormatter().format_detail(ticket)
    assert "AI Confidence: 85%\n" in text
    assert "Affected system: Campus WiFi" in text

    # with no ai the keyword fallback saves confidence 0, so staff are told why
    offline = make_ticket("0002")
    offline.attach_analysis({"category": "Network", "confidence": 0.0, "ai_failed": True, "affected_system": "Unknown"})
    assert "AI Confidence: 0% (AI was not available, keyword result)" in TicketFormatter().format_detail(offline)


def test_detail_skips_a_confidence_that_is_not_between_0_and_1(make_ticket):
    for bad in [85, -0.5, "high", True, None]:
        ticket = make_ticket()
        ticket.attach_analysis({"category": "Other", "confidence": bad, "affected_system": "  "})
        text = TicketFormatter().format_detail(ticket)
        assert "AI Confidence" not in text
        assert "Affected system" not in text


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


def test_only_tickets_open_for_more_than_a_day_get_the_overdue_badge(make_ticket):
    fresh = make_ticket("0001")
    old = make_ticket("0002", created_at="2026-01-01T09:00:00")
    old.refresh_overdue_status()
    formatter = TicketFormatter()
    text = formatter.format_list([fresh, old], "All Tickets")
    assert "ID: 0001 | WiFi problem | Priority: Medium | Status: Open\n" in text
    assert "ID: 0002 | WiFi problem | Priority: Medium | Status: Open | [OVERDUE >24H]" in text
    assert "SLA Status" not in formatter.format_detail(fresh)
    assert "SLA Status: OVERDUE (>24h unresolved)" in formatter.format_detail(old)
