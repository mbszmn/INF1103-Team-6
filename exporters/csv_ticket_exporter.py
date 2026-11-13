import csv
import io

from exporters.ticket_exporter import TicketExporter
from models.ticket import Ticket


class CsvTicketExporter(TicketExporter):
    # strategy for excel: one row per ticket, the csv module handles commas, quotes and new lines in the text

    COLUMNS = (
        "ticket_id", "username", "student_id", "device", "title", "category",
        "final_priority", "status", "escalated", "requires_manual_review", "created_at", "updated_at",
    )

    @property
    def file_name(self) -> str:
        return "tickets.csv"

    @property
    def label(self) -> str:
        return "CSV file"

    @property
    def _encoding(self) -> str:
        # the extra mark at the start lets excel show non english letters properly
        return "utf-8-sig"

    def _render(self, tickets: list[Ticket]) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(CsvTicketExporter.COLUMNS)
        for ticket in tickets:
            writer.writerow([
                ticket.ticket_id,
                ticket.username,
                ticket.student_id,
                ticket.device,
                ticket.title,
                ticket.category,
                ticket.final_priority,
                ticket.status,
                ticket.escalated,
                ticket.requires_manual_review,
                ticket.created_at,
                ticket.updated_at,
            ])
        return buffer.getvalue()
