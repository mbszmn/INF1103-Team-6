from abc import ABC, abstractmethod

from models.ticket import Ticket


class TicketFilter(ABC):
    # interface: every filter must be able to check a ticket and say in words what it looks for

    @abstractmethod
    def matches(self, ticket: Ticket) -> bool:
        pass

    @abstractmethod
    def describe(self) -> str:
        pass
