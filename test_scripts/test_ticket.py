import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from errors.ticket_error import TicketError
from models.ticket import Ticket

PHASE_1_RECORD = {
    "ticket_id": "0002",
    "username": "Chian",
    "device": "Macbook",
    "title": "network issue",
    "description": "unable to connect to school wifi",
    "steps_attempted": "restarted laptop",
    "user_priority": "High",
    "error_message": "",
    "ai_analysis": {
        "category": "Network",
        "priority": "Medium",
        "confidence": 0.0,
        "summary": "unable to connect to school wifi",
        "troubleshooting": [],
    },
    "final_priority": "Medium",
    "status": "Open",
    "escalated": False,
    "requires_manual_review": True,
    "created_at": "2026-10-02T03:20:11",
    "updated_at": "2026-10-02T03:20:11",
}


def test_new_ticket_starts_open_with_one_history_line(make_ticket):
    ticket = make_ticket(user_priority="High")
    assert ticket.status == "Open"
    assert ticket.final_priority == "High"
    assert ticket.category == "Unassigned"
    assert [(change.old_status, change.new_status) for change in ticket.history] == [("", "Open")]


def test_fields_cannot_be_changed_from_outside(make_ticket):
    ticket = make_ticket()
    with pytest.raises(AttributeError):
        ticket.status = "Closed"
    with pytest.raises(AttributeError):
        ticket.ticket_id = "9999"
    ticket.ai_analysis["category"] = "Security"
    assert ticket.category == "Unassigned"
    assert isinstance(ticket.history, tuple)


def test_close_and_reopen_follow_the_rule(make_ticket):
    ticket = make_ticket()
    ticket.close()
    assert ticket.is_closed
    with pytest.raises(TicketError, match="already closed"):
        ticket.close()
    ticket.reopen()
    assert ticket.status == "Reopened"
    with pytest.raises(TicketError, match="is not closed"):
        ticket.reopen()
    steps = [(change.old_status, change.new_status) for change in ticket.history]
    assert steps == [("", "Open"), ("Open", "Closed"), ("Closed", "Reopened")]


def test_closed_ticket_cannot_be_changed_until_reopened(make_ticket):
    ticket = make_ticket()
    ticket.close()
    with pytest.raises(TicketError, match="reopen it first"):
        ticket.attach_analysis({"category": "Network"})
    ticket.reopen()
    ticket.attach_analysis({"category": "Network"})
    assert ticket.category == "Network"


def test_attach_analysis_sets_priority_escalation_and_review(make_ticket):
    ticket = make_ticket(user_priority="Low")
    ticket.attach_analysis({
        "category": "Security",
        "priority": "Critical",
        "requires_escalation": True,
        "requires_manual_review": True,
    })
    assert ticket.final_priority == "Critical"
    assert ticket.escalated is True
    assert ticket.requires_manual_review is True
    assert ticket.category == "Security"


def test_bad_priority_from_logic_keeps_the_user_priority(make_ticket):
    ticket = make_ticket(user_priority="High")
    ticket.attach_analysis({"category": "Network", "priority": "Urgent", "requires_escalation": "yes"})
    assert ticket.final_priority == "High"
    assert ticket.escalated is False


def test_unknown_user_priority_is_refused():
    with pytest.raises(ValueError, match="Unknown priority"):
        Ticket("0001", "Alex", "2600001", "Dell", "WiFi", "Cannot connect", user_priority="Urgent")


@pytest.mark.parametrize(
    ("typed", "expected"),
    [("1", "0001"), (" 0001 ", "0001"), ("42", "0042"), ("12345", "12345"), ("abc", "abc"), ("²", "²")],
)
def test_normalise_id(typed, expected):
    assert Ticket.normalise_id(typed) == expected


def test_round_trip_keeps_every_field(make_ticket):
    ticket = make_ticket(steps_attempted="restarted", error_message="0x80070005", user_priority="Critical")
    ticket.attach_analysis({"category": "Software", "priority": "Critical", "troubleshooting": ["Reinstall"]})
    ticket.close()
    ticket.reopen()
    copy = Ticket.from_dict(json.loads(json.dumps(ticket.to_dict())))
    assert copy.to_dict() == ticket.to_dict()
    assert [change.describe() for change in copy.history] == [change.describe() for change in ticket.history]


def test_phase_1_ticket_without_student_id_or_history_still_loads():
    ticket = Ticket.from_dict(dict(PHASE_1_RECORD))
    assert ticket.student_id == ""
    assert ticket.history == ()
    assert ticket.category == "Network"
    assert ticket.final_priority == "Medium"
    assert ticket.user_priority == "High"
    assert ticket.requires_manual_review is True


def test_number_ticket_id_from_a_hand_edited_file_is_padded():
    record = dict(PHASE_1_RECORD, ticket_id=7)
    assert Ticket.from_dict(record).ticket_id == "0007"


@pytest.mark.parametrize(
    "record",
    [
        [],
        "not a ticket",
        {"ticket_id": "0001"},
        dict(PHASE_1_RECORD, status="Lost"),
        dict(PHASE_1_RECORD, user_priority="Urgent"),
    ],
    ids=["list", "text", "missing keys", "unknown status", "unknown priority"],
)
def test_damaged_records_are_refused(record):
    with pytest.raises(ValueError):
        Ticket.from_dict(record)


@given(username=st.text(), title=st.text(), description=st.text(), error=st.text())
def test_any_text_survives_saving_to_json_and_loading(username, title, description, error):
    ticket = Ticket("0001", username, "2600001", "Dell", title, description, error_message=error)
    loaded = Ticket.from_dict(json.loads(json.dumps(ticket.to_dict())))
    assert loaded.to_dict() == ticket.to_dict()
