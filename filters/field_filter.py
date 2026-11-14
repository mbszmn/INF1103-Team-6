from filters.ticket_filter import TicketFilter
from models.ticket import Ticket


class FieldFilter(TicketFilter):
    # matches one field exactly, like status is Open, upper or lower case does not matter

    LABELS = {"status": "status", "final_priority": "priority", "category": "category"}

    def __init__(self, field_name: str, expected: str):
        if field_name not in FieldFilter.LABELS:
            raise ValueError(f"Cannot filter tickets by {field_name!r}.")
        self.__field_name: str = field_name
        self.__expected: str = expected.strip()

    def matches(self, ticket: Ticket) -> bool:
        value = getattr(ticket, self.__field_name)
        return str(value).lower() == self.__expected.lower()

    def describe(self) -> str:
        return f"{FieldFilter.LABELS[self.__field_name]} is {self.__expected}"
