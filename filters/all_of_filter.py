from filters.ticket_filter import TicketFilter
from models.ticket import Ticket


class AllOfFilter(TicketFilter):
    # aggregation: holds filters made somewhere else, a ticket has to pass every one of them

    def __init__(self, filters: list[TicketFilter]):
        self.__filters: list[TicketFilter] = list(filters)

    def matches(self, ticket: Ticket) -> bool:
        return all(ticket_filter.matches(ticket) for ticket_filter in self.__filters)

    def describe(self) -> str:
        if not self.__filters:
            return "all tickets"
        return " and ".join(ticket_filter.describe() for ticket_filter in self.__filters)
