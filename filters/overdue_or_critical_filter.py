from filters.ticket_filter import TicketFilter
from models.ticket import Ticket


class OverdueOrCriticalFilter(TicketFilter):
    # Matches unresolved tickets that are either overdue (more than 24h) or Critical priority

    def matches(self, ticket: Ticket) -> bool:
        if ticket.is_closed:
            return False
        return ticket.is_overdue or ticket.final_priority == "Critical"

    def describe(self) -> str:
        return "Unresolved tickets overdue (>24h) or Critical priority"