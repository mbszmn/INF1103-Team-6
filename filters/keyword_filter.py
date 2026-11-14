from filters.ticket_filter import TicketFilter
from models.ticket import Ticket


class KeywordFilter(TicketFilter):
    # matches when the word shows up anywhere in what the user typed or in the ai summary

    def __init__(self, keyword: str):
        if keyword.strip() == "":
            raise ValueError("Search word cannot be empty.")
        self.__keyword: str = keyword.strip()

    def matches(self, ticket: Ticket) -> bool:
        summary = ticket.ai_analysis.get("summary", "")
        text = " ".join([
            ticket.title,
            ticket.description,
            ticket.username,
            ticket.device,
            ticket.error_message,
            ticket.steps_attempted,
            str(summary),
        ])
        return self.__keyword.lower() in text.lower()

    def describe(self) -> str:
        return f'text has "{self.__keyword}"'
