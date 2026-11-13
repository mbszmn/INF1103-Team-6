import csv

import pytest

from errors.storage_error import StorageError
from errors.ticket_error import TicketError
from exporters.csv_ticket_exporter import CsvTicketExporter
from filters.field_filter import FieldFilter
from managers.data_manager import DataManager
from models.ticket import Ticket
from storage.json_ticket_repository import JsonTicketRepository
from storage.ticket_repository import TicketRepository


class FailingRepository(TicketRepository):
    # a stand in repository that can be told to fail, any TicketRepository works with the data manager

    def __init__(self, tickets: list[Ticket]):
        self.saved: list[list[str]] = []
        self.fail_next_save = False
        self.__tickets = tickets

    def load_all(self) -> list[Ticket]:
        return list(self.__tickets)

    def save_all(self, tickets: list[Ticket]) -> None:
        if self.fail_next_save:
            raise StorageError("disk is full")
        self.saved.append([ticket.ticket_id for ticket in tickets])


def test_load_gives_the_number_of_tickets(make_ticket):
    manager = DataManager(FailingRepository([make_ticket("0001"), make_ticket("0002")]))
    assert manager.load() == 2


def test_first_id_is_0001_then_biggest_plus_one(data_manager, make_ticket):
    assert data_manager.next_ticket_id() == "0001"
    data_manager.add(make_ticket("0007"))
    data_manager.add(make_ticket("0003"))
    data_manager.add(make_ticket("OLD-1"))
    assert data_manager.next_ticket_id() == "0008"


def test_create_ticket_uses_the_next_id_but_does_not_save(data_manager, ticket_answers):
    fields = ["username", "student_id", "device", "title", "description", "steps_attempted",
              "error_message", "user_priority"]
    ticket = data_manager.create_ticket(dict(zip(fields, ticket_answers, strict=True)))
    assert ticket.ticket_id == "0001"
    assert ticket.title == "WiFi problem"
    assert ticket.user_priority == "High"
    assert data_manager.tickets == []


def test_create_ticket_refuses_missing_details(data_manager):
    with pytest.raises(TicketError, match="missing: student_id, device"):
        data_manager.create_ticket({"username": "Alex", "title": "WiFi", "description": "Cannot connect"})


def test_create_ticket_turns_a_bad_priority_into_a_ticket_error(data_manager, ticket_answers):
    fields = ["username", "student_id", "device", "title", "description", "steps_attempted",
              "error_message", "user_priority"]
    details = dict(zip(fields, ticket_answers, strict=True), user_priority="Urgent")
    with pytest.raises(TicketError, match="Unknown priority 'Urgent'"):
        data_manager.create_ticket(details)


def test_add_saves_to_the_file_and_refuses_a_duplicate_id(ticket_file, data_manager, make_ticket):
    data_manager.add(make_ticket("0001"))
    assert [ticket.ticket_id for ticket in JsonTicketRepository(ticket_file).load_all()] == ["0001"]
    with pytest.raises(TicketError, match="already exists"):
        data_manager.add(make_ticket("0001"))
    assert len(data_manager.tickets) == 1


def test_failed_save_takes_the_new_ticket_back_out(make_ticket):
    repository = FailingRepository([])
    manager = DataManager(repository)
    repository.fail_next_save = True
    with pytest.raises(StorageError):
        manager.add(make_ticket("0001"))
    assert manager.tickets == []
    assert manager.next_ticket_id() == "0001"


@pytest.mark.parametrize("typed", ["1", "0001", " 0001 ", "01"])
def test_find_accepts_short_ids_and_spaces(data_manager, make_ticket, typed):
    data_manager.add(make_ticket("0001"))
    assert data_manager.find(typed).ticket_id == "0001"


def test_find_missing_ticket(data_manager):
    with pytest.raises(TicketError, match="Ticket 9999 not found."):
        data_manager.find("9999")


def test_close_and_reopen_are_saved(ticket_file, data_manager, make_ticket):
    data_manager.add(make_ticket("0001"))
    data_manager.close_ticket("1")
    assert JsonTicketRepository(ticket_file).load_all()[0].status == "Closed"
    with pytest.raises(TicketError, match="already closed"):
        data_manager.close_ticket("1")
    data_manager.reopen_ticket("1")
    saved = JsonTicketRepository(ticket_file).load_all()[0]
    assert saved.status == "Reopened"
    assert [change.new_status for change in saved.history] == ["Open", "Closed", "Reopened"]


def test_open_ticket_cannot_be_reopened(data_manager, make_ticket):
    data_manager.add(make_ticket("0001"))
    with pytest.raises(TicketError, match="not closed"):
        data_manager.reopen_ticket("0001")


def test_failed_close_is_undone(make_ticket):
    repository = FailingRepository([make_ticket("0001")])
    manager = DataManager(repository)
    manager.load()
    repository.fail_next_save = True
    with pytest.raises(StorageError):
        manager.close_ticket("0001")
    assert manager.find("0001").status == "Open"
    assert len(manager.find("0001").history) == 1


def test_failed_reopen_is_undone(make_ticket):
    closed = make_ticket("0001")
    closed.close()
    repository = FailingRepository([closed])
    manager = DataManager(repository)
    manager.load()
    repository.fail_next_save = True
    with pytest.raises(StorageError):
        manager.reopen_ticket("0001")
    assert manager.find("0001").status == "Closed"


def test_queue_puts_open_critical_tickets_first_and_closed_ones_last(data_manager, make_ticket):
    data_manager.add(make_ticket("0001", user_priority="Low"))
    data_manager.add(make_ticket("0002", user_priority="Critical"))
    data_manager.add(make_ticket("0003", user_priority="Medium"))
    data_manager.add(make_ticket("0004", user_priority="Critical"))
    data_manager.close_ticket("0004")
    assert [ticket.ticket_id for ticket in data_manager.queue()] == ["0002", "0003", "0001", "0004"]


def test_query_uses_the_filter_it_is_given(data_manager, make_ticket):
    data_manager.add(make_ticket("0001", user_priority="High"))
    data_manager.add(make_ticket("0002", user_priority="Low"))
    found = data_manager.query(FieldFilter("final_priority", "high"))
    assert [ticket.ticket_id for ticket in found] == ["0001"]


def test_export_writes_the_queue_in_order(tmp_path, data_manager, make_ticket):
    data_manager.add(make_ticket("0001", user_priority="Low"))
    data_manager.add(make_ticket("0002", user_priority="Critical"))
    path = data_manager.export(CsvTicketExporter(), tmp_path / "exports")
    with path.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))
    assert [row[0] for row in rows[1:]] == ["0002", "0001"]


def test_tickets_list_is_a_copy(data_manager, make_ticket):
    data_manager.add(make_ticket("0001"))
    data_manager.tickets.clear()
    assert len(data_manager.tickets) == 1
