import pytest

from filters.all_of_filter import AllOfFilter
from filters.field_filter import FieldFilter
from filters.keyword_filter import KeywordFilter
from filters.ticket_filter import TicketFilter
from filters.ticket_filter_factory import TicketFilterFactory
from models.ticket import Ticket


@pytest.fixture
def tickets(make_ticket) -> list[Ticket]:
    wifi = make_ticket("0001", user_priority="High")
    wifi.attach_analysis({"category": "Network", "priority": "High", "summary": "Campus WiFi keeps dropping"})
    phishing = make_ticket("0002", title="Strange email", description="Clicked a link in an email",
                           user_priority="Critical")
    phishing.attach_analysis({"category": "Security", "priority": "Critical"})
    old = Ticket.from_dict({
        "ticket_id": "0003", "username": "lara", "device": "Mac", "title": "network",
        "description": "slow internet in the library", "status": "Closed", "created_at": "2026-10-02T03:00:00",
    })
    return [wifi, phishing, old]


def test_field_filter_ignores_case(tickets):
    assert [ticket.ticket_id for ticket in tickets if FieldFilter("status", "open").matches(ticket)] == ["0001", "0002"]
    assert [ticket.ticket_id for ticket in tickets if FieldFilter("category", "SECURITY").matches(ticket)] == ["0002"]


def test_field_filter_refuses_unknown_fields():
    with pytest.raises(ValueError, match="Cannot filter"):
        FieldFilter("password", "x")


def test_keyword_filter_looks_in_the_text_and_the_ai_summary(tickets):
    assert [ticket.ticket_id for ticket in tickets if KeywordFilter("wifi").matches(ticket)] == ["0001"]
    assert [ticket.ticket_id for ticket in tickets if KeywordFilter("DROPPING").matches(ticket)] == ["0001"]
    assert [ticket.ticket_id for ticket in tickets if KeywordFilter("library").matches(ticket)] == ["0003"]


def test_keyword_filter_needs_a_word():
    with pytest.raises(ValueError, match="cannot be empty"):
        KeywordFilter("   ")


def test_all_of_filter_needs_every_part_to_match(tickets):
    both = AllOfFilter([FieldFilter("status", "Open"), KeywordFilter("email")])
    assert [ticket.ticket_id for ticket in tickets if both.matches(ticket)] == ["0002"]
    assert both.describe() == 'status is Open and text has "email"'


def test_empty_all_of_filter_matches_everything(tickets):
    everything = AllOfFilter([])
    assert all(everything.matches(ticket) for ticket in tickets)
    assert everything.describe() == "all tickets"


@pytest.mark.parametrize(
    "ticket_filter",
    [
        FieldFilter("status", "Closed"),
        FieldFilter("final_priority", "Critical"),
        FieldFilter("category", "Network"),
        KeywordFilter("wifi"),
        AllOfFilter([FieldFilter("status", "Open"), KeywordFilter("link")]),
        AllOfFilter([]),
    ],
    ids=["status", "priority", "category", "keyword", "all-of", "empty all-of"],
)
def test_every_filter_keeps_the_same_promise(ticket_filter, tickets):
    # LSP: any TicketFilter can be used in place of another, the caller never checks the type
    assert isinstance(ticket_filter, TicketFilter)
    for ticket in tickets:
        assert isinstance(ticket_filter.matches(ticket), bool)
    assert isinstance(ticket_filter.describe(), str)
    assert ticket_filter.describe() != ""


def test_the_interface_cannot_be_used_on_its_own():
    with pytest.raises(TypeError):
        TicketFilter()


@pytest.mark.parametrize(
    ("criterion", "value", "expected"),
    [
        ("status", "reopened", "status is Reopened"),
        ("priority", "critical", "priority is Critical"),
        ("category", " network ", "category is Network"),
        ("keyword", "printer", 'text has "printer"'),
    ],
)
def test_factory_makes_the_right_filter(criterion, value, expected):
    assert TicketFilterFactory.create(criterion, value).describe() == expected


@pytest.mark.parametrize(
    ("criterion", "value", "message"),
    [
        ("status", "opn", "Status must be one of: Open, Closed, Reopened."),
        ("priority", "urgent", "Priority must be one of: Low, Medium, High, Critical."),
        ("category", "printers", "Category must be one of"),
        ("colour", "red", "Unknown filter"),
    ],
)
def test_factory_explains_bad_answers(criterion, value, message):
    with pytest.raises(ValueError, match=message):
        TicketFilterFactory.create(criterion, value)


def test_factory_skips_blank_answers(tickets):
    ticket_filter = TicketFilterFactory.from_answers(
        {"status": "", "priority": "critical", "category": " ", "keyword": "link"}
    )
    assert ticket_filter.describe() == 'priority is Critical and text has "link"'
    assert [ticket.ticket_id for ticket in tickets if ticket_filter.matches(ticket)] == ["0002"]
