from abc import ABC, abstractmethod

from models.ticket import Ticket


class TicketRepository(ABC):
    # interface: anything that keeps tickets between runs must be able to load and save them

    @abstractmethod
    def load_all(self) -> list[Ticket]:
        pass

    @abstractmethod
    def save_all(self, tickets: list[Ticket]) -> None:
        pass
