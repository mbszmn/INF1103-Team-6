from collections import Counter
from datetime import datetime

from exporters.ticket_exporter import TicketExporter
from models.ticket import Ticket


class SummaryReportExporter(TicketExporter):
    # strategy for the helpdesk lead: counts by status, priority and category, plus what needs attention now

    @property
    def file_name(self) -> str:
        return "ticket_summary.txt"

    @property
    def label(self) -> str:
        return "Summary report"

    def _render(self, tickets: list[Ticket]) -> str:
        still_open = [ticket for ticket in tickets if not ticket.is_closed]
        critical = [ticket for ticket in still_open if ticket.final_priority == "Critical"]
        lines = [
            "AI SIT Helpdesk - Ticket Summary Report",
            f"Made on: {datetime.now().isoformat(timespec='seconds')}",
            f"Total tickets: {len(tickets)}",
            "",
            self.__count_line("By status", [ticket.status for ticket in tickets], Ticket.STATUSES),
            self.__count_line("By priority", [ticket.final_priority for ticket in tickets], Ticket.PRIORITIES[::-1]),
            self.__count_line("By category", [ticket.category for ticket in tickets], ()),
            "",
            f"Escalated and not closed: {sum(1 for ticket in still_open if ticket.escalated)}",
            f"Waiting for manual review: {sum(1 for ticket in still_open if ticket.requires_manual_review)}",
            "",
            "Critical tickets not closed yet:",
        ]
        if not critical:
            lines.append("  none")
        for ticket in critical:
            lines.append(f"  {ticket.ticket_id}  {ticket.title}  ({ticket.category}, {ticket.status})")
        return "\n".join(lines) + "\n"

    def __count_line(self, heading: str, values: list[str], order: tuple[str, ...]) -> str:
        counts = Counter(values)
        names = list(order) + sorted(name for name in counts if name not in order)
        return f"{heading}: " + " | ".join(f"{name} {counts[name]}" for name in names)
