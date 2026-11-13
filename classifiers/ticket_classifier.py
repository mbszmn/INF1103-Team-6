from abc import ABC, abstractmethod


class TicketClassifier(ABC):
    """Abstract base class for ticket classification."""

    @abstractmethod
    def classify(self, ticket: dict) -> str:
        """Classify a ticket and return its category."""
        pass