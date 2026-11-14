from filters.all_of_filter import AllOfFilter
from filters.field_filter import FieldFilter
from filters.keyword_filter import KeywordFilter
from filters.ticket_filter import TicketFilter
from managers.logic_manager import VALID_CATEGORIES
from models.ticket import Ticket


class TicketFilterFactory:
    # factory: the one place that decides which filter class to make from the user's answers

    @staticmethod
    def create(criterion: str, value: str) -> TicketFilter:
        value = value.strip()
        if criterion == "status":
            return FieldFilter("status", TicketFilterFactory.__pick(value, Ticket.STATUSES, "Status"))
        if criterion == "priority":
            return FieldFilter("final_priority", TicketFilterFactory.__pick(value, Ticket.PRIORITIES, "Priority"))
        if criterion == "category":
            categories = tuple(sorted(VALID_CATEGORIES))
            return FieldFilter("category", TicketFilterFactory.__pick(value, categories, "Category"))
        if criterion == "keyword":
            return KeywordFilter(value)
        raise ValueError(f"Unknown filter {criterion!r}.")

    @staticmethod
    def from_answers(answers: dict[str, str]) -> AllOfFilter:
        # blank answers are skipped, the rest are joined so a ticket must match all of them
        filters: list[TicketFilter] = []
        for criterion, value in answers.items():
            if value.strip() != "":
                filters.append(TicketFilterFactory.create(criterion, value))
        return AllOfFilter(filters)

    @staticmethod
    def __pick(value: str, allowed: tuple[str, ...], label: str) -> str:
        for option in allowed:
            if option.lower() == value.lower():
                return option
        raise ValueError(f"{label} must be one of: {', '.join(allowed)}.")
