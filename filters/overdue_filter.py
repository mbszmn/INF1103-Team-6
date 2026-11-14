from filters.ticket_filter import TicketFilter
from models.ticket import Ticket


class OverdueFilter(TicketFilter):
    # Matches unresolved tickets that have exceeded the 24-hour SLA window

    def matches(self, ticket: Ticket) -> bool:
        return not ticket.is_closed and ticket.is_overdue

    def describe(self) -> str:
        return "Unresolved tickets overdue (>24h)"