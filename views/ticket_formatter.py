from models.ticket import Ticket


class TicketFormatter:
    # turns tickets into text, the IO manager does the actual printing

    LINE = "-" * 48

    def format_detail(self, ticket: Ticket) -> str:
        lines = [
            TicketFormatter.LINE,
            f"Ticket ID: {ticket.ticket_id}",
            f"User: {ticket.username} | Student ID: {ticket.student_id or '-'}",
            f"Device model: {ticket.device}",
            f"Title: {ticket.title}",
            f"Description: {ticket.description}",
            f"Steps already tried: {ticket.steps_attempted or '-'}",
            f"Error message: {ticket.error_message or '-'}",
            f"User urgency: {ticket.user_priority}",
            f"Status: {ticket.status} | Priority: {ticket.final_priority}",
            f"Escalated: {ticket.escalated} | Manual review: {ticket.requires_manual_review}",
        ]
        # open for more than 24 hours without being closed
        if ticket.is_overdue:
            lines.append("SLA Status: OVERDUE (>24h unresolved)")
        analysis = ticket.ai_analysis
        if analysis:
            lines.append(f"AI Category: {ticket.category}")
            # the ai saves how sure it is as 0 to 1, so 0.85 shows as 85%
            confidence = analysis.get("confidence")
            if isinstance(confidence, (int, float)) and not isinstance(confidence, bool) and 0 <= confidence <= 1:
                note = " (AI was not available, keyword result)" if analysis.get("ai_failed") is True else ""
                lines.append(f"AI Confidence: {confidence:.0%}{note}")
            affected = analysis.get("affected_system")
            if isinstance(affected, str) and affected.strip() != "":
                lines.append(f"Affected system: {affected}")
            summary = analysis.get("summary")
            if isinstance(summary, str) and summary != "":
                lines.append(f"AI Summary: {summary}")
            hardware = self.__text_items(analysis.get("extracted_hardware"))
            if hardware:
                lines.append(f"Hardware mentioned: {', '.join(hardware)}")
            software = self.__text_items(analysis.get("extracted_software"))
            if software:
                lines.append(f"Software mentioned: {', '.join(software)}")
            steps = self.__text_items(analysis.get("troubleshooting"))
            if steps:
                lines.append("Recommended Troubleshooting Steps:")
                for number, step in enumerate(steps, start=1):
                    lines.append(f"  {number}. {step}")
        if ticket.history:
            lines.append("History:")
            for change in ticket.history:
                lines.append(f"  {change.describe()}")
        lines.append(f"Created: {ticket.created_at} | Updated: {ticket.updated_at}")
        lines.append(TicketFormatter.LINE)
        return "\n".join(lines)

    def format_list(self, tickets: list[Ticket], heading: str, empty_message: str = "No tickets yet.") -> str:
        lines = ["", heading, TicketFormatter.LINE]
        if not tickets:
            lines.append(empty_message)
        for ticket in tickets:
            line = (
                f"ID: {ticket.ticket_id} | {ticket.title} | "
                f"Priority: {ticket.final_priority} | Status: {ticket.status}"
            )
            if ticket.final_priority == "Critical" and not ticket.is_closed:
                line = "TOP | " + line
            if ticket.is_overdue:
                line += " | [OVERDUE >24H]"
            lines.append(line)
        lines.append(TicketFormatter.LINE)
        return "\n".join(lines)

    def __text_items(self, value: object) -> list[str]:
        # old or broken ai results may not be a list of text, only show the parts that are safe
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if isinstance(item, str | int | float)]
