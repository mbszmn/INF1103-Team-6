from datetime import datetime, timedelta
from pathlib import Path

from filters.overdue_filter import OverdueFilter
from filters.ticket_filter_factory import TicketFilterFactory
from managers.data_manager import DataManager
from models.ticket import Ticket
from storage.json_ticket_repository import JsonTicketRepository
from views.ticket_formatter import TicketFormatter


def _make_ticket(
    ticket_id: str,
    hours_ago: float,
    priority: str = "Medium",
    closed: bool = False,
) -> Ticket:
    created = (datetime.now() - timedelta(hours=hours_ago)).isoformat(timespec="seconds")
    ticket = Ticket(
        ticket_id=ticket_id,
        username="alex",
        student_id="2600001",
        device="Dell Latitude 5430",
        title=f"Ticket {ticket_id}",
        description="Cannot connect to campus Wi-Fi.",
        user_priority=priority,
        created_at=created,
    )
    ticket.refresh_overdue_status()
    if closed:
        ticket.close()
    return ticket


def test_ticket_flags_overdue_only_after_24_hours():
    fresh_ticket = _make_ticket("0001", hours_ago=12)
    overdue_ticket = _make_ticket("0002", hours_ago=25)

    assert fresh_ticket.is_overdue is False
    assert overdue_ticket.is_overdue is True


def test_closed_ticket_is_not_flagged_overdue():
    closed_old_ticket = _make_ticket("0003", hours_ago=48, closed=True)
    assert closed_old_ticket.is_overdue is False


def test_overdue_filter_and_factory():
    created_filter = TicketFilterFactory.create("status", "overdue")
    assert isinstance(created_filter, OverdueFilter)

    overdue_only = TicketFilterFactory.from_answers({"status": "overdue"})
    assert "overdue" in overdue_only.describe().lower()

    fresh_medium = _make_ticket("0001", hours_ago=5, priority="Medium")
    overdue_low = _make_ticket("0002", hours_ago=30, priority="Low")
    fresh_critical = _make_ticket("0003", hours_ago=1, priority="Critical")
    closed_overdue = _make_ticket("0004", hours_ago=50, priority="Critical", closed=True)

    assert overdue_only.matches(fresh_medium) is False
    assert overdue_only.matches(overdue_low) is True
    assert overdue_only.matches(fresh_critical) is False
    assert overdue_only.matches(closed_overdue) is False

    # Combining overdue status + Critical priority via AllOfFilter
    overdue_and_critical = TicketFilterFactory.from_answers({"status": "overdue", "priority": "Critical"})
    overdue_critical = _make_ticket("0005", hours_ago=28, priority="Critical")
    assert overdue_and_critical.matches(overdue_low) is False
    assert overdue_and_critical.matches(overdue_critical) is True


def test_data_manager_persists_overdue_flag_on_load_and_formats_badge(tmp_path: Path):
    repo = JsonTicketRepository(tmp_path / "tickets.json")
    stale_ticket = _make_ticket("0001", hours_ago=26, priority="Low")
    critical_ticket = _make_ticket("0002", hours_ago=2, priority="Critical")
    normal_ticket = _make_ticket("0003", hours_ago=3, priority="Medium")
    repo.save_all([stale_ticket, critical_ticket, normal_ticket])

    manager = DataManager(repo)
    assert manager.load() == 3

    results = manager.query(OverdueFilter())
    assert [t.ticket_id for t in results] == ["0001"]
    assert manager.find("0001").to_dict()["overdue"] is True

    formatter = TicketFormatter()
    list_output = formatter.format_list(results, "Overdue Tickets")
    assert "[OVERDUE >24H]" in list_output
    assert "SLA Status: OVERDUE (>24h unresolved)" in formatter.format_detail(manager.find("0001"))