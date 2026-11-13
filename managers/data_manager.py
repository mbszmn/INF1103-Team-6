from pathlib import Path
from typing import Any

from errors.storage_error import StorageError
from errors.ticket_error import TicketError
from exporters.ticket_exporter import TicketExporter
from filters.ticket_filter import TicketFilter
from models.ticket import Ticket
from storage.ticket_repository import TicketRepository


class DataManager:
    # keeps the tickets in memory and asks the repository to save after every change

    QUEUE_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    REQUIRED_DETAILS = ("username", "student_id", "device", "title", "description")

    def __init__(self, repository: TicketRepository):
        # association: the repository is made outside and passed in, so tests can give a fake one
        self.__repository: TicketRepository = repository
        # aggregation: tickets can live without this manager (loaded from the file or handed in with add())
        self.__tickets: list[Ticket] = []

    @property
    def tickets(self) -> list[Ticket]:
        return list(self.__tickets)

    def load(self) -> int:
        self.__tickets = self.__repository.load_all()
        return len(self.__tickets)

    def next_ticket_id(self) -> str:
        # biggest id so far + 1, padded to 4 digits like 0001
        largest = 0
        for ticket in self.__tickets:
            if ticket.ticket_id.isascii() and ticket.ticket_id.isdigit():
                largest = max(largest, int(ticket.ticket_id))
        return Ticket.normalise_id(str(largest + 1))

    def create_ticket(self, details: dict[str, str]) -> Ticket:
        # gives the new ticket the next free id, it is only saved once add() is called
        missing = [field for field in DataManager.REQUIRED_DETAILS if str(details.get(field, "")).strip() == ""]
        if missing:
            raise TicketError(f"The ticket is missing: {', '.join(missing)}.")
        try:
            return Ticket(
                ticket_id=self.next_ticket_id(),
                username=details["username"],
                student_id=details["student_id"],
                device=details["device"],
                title=details["title"],
                description=details["description"],
                steps_attempted=details.get("steps_attempted", ""),
                error_message=details.get("error_message", ""),
                user_priority=details.get("user_priority", "Medium"),
            )
        except ValueError as error:
            raise TicketError(str(error)) from error

    def add(self, ticket: Ticket) -> None:
        if self.__find_or_none(ticket.ticket_id) is not None:
            raise TicketError(f"Ticket ID {ticket.ticket_id} already exists.")
        self.__tickets.append(ticket)
        try:
            self.__repository.save_all(self.__tickets)
        except StorageError:
            # memory has to match the file, so take it back out
            self.__tickets.remove(ticket)
            raise

    def find(self, ticket_id: str) -> Ticket:
        wanted = Ticket.normalise_id(ticket_id)
        ticket = self.__find_or_none(wanted)
        if ticket is None:
            raise TicketError(f"Ticket {wanted} not found.")
        return ticket

    def close_ticket(self, ticket_id: str) -> Ticket:
        ticket = self.find(ticket_id)
        before = ticket.to_dict()
        ticket.close()
        self.__save_or_undo(ticket, before)
        return ticket

    def reopen_ticket(self, ticket_id: str) -> Ticket:
        ticket = self.find(ticket_id)
        before = ticket.to_dict()
        ticket.reopen()
        self.__save_or_undo(ticket, before)
        return ticket

    def queue(self) -> list[Ticket]:
        # open tickets first, critical at the very top, then high, medium and low, oldest first
        return sorted(self.__tickets, key=self.__queue_position)

    def query(self, ticket_filter: TicketFilter) -> list[Ticket]:
        # association: the filter is only borrowed for this search, the data manager does not keep it
        return [ticket for ticket in self.queue() if ticket_filter.matches(ticket)]

    def export(self, exporter: TicketExporter, folder: Path) -> Path:
        # association: same idea, any exporter can be handed in and it is used the same way
        return exporter.export(self.queue(), folder)

    def __find_or_none(self, ticket_id: str) -> Ticket | None:
        for ticket in self.__tickets:
            if ticket.ticket_id == ticket_id:
                return ticket
        return None

    def __save_or_undo(self, ticket: Ticket, before: dict[str, Any]) -> None:
        try:
            self.__repository.save_all(self.__tickets)
        except StorageError:
            # the file did not change, so put the ticket back the way it was
            self.__tickets[self.__tickets.index(ticket)] = Ticket.from_dict(before)
            raise

    def __queue_position(self, ticket: Ticket) -> tuple[bool, int, str]:
        return (ticket.is_closed, DataManager.QUEUE_ORDER.get(ticket.final_priority, 4), ticket.ticket_id)
