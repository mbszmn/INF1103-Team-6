import logging
from collections.abc import Callable
from pathlib import Path

from errors.storage_error import StorageError
from errors.ticket_error import TicketError
from exporters.ticket_exporter import TicketExporter
from filters.ticket_filter_factory import TicketFilterFactory
from managers.ai_manager import AIManager
from managers.data_manager import DataManager
from managers.io_manager import IOManager
from managers.logic_manager import LogicManager
from views.ticket_formatter import TicketFormatter

logger = logging.getLogger(__name__)


class HelpdeskApp:
    # runs the menu and sends each new ticket through the IO, AI, logic and data managers in order

    EXIT_OPTION = "7"

    def __init__(
        self,
        io_manager: IOManager,
        ai_manager: AIManager,
        logic_manager: LogicManager,
        data_manager: DataManager,
        exporters: list[TicketExporter],
        export_folder: Path,
        version: str = "dev",
    ):
        # aggregation: the managers and exporters are made in main.py and passed in
        self.__io: IOManager = io_manager
        self.__ai: AIManager = ai_manager
        self.__logic: LogicManager = logic_manager
        self.__data: DataManager = data_manager
        self.__exporters: list[TicketExporter] = list(exporters)
        self.__export_folder: Path = Path(export_folder)
        self.__version: str = version
        # composition: the formatter is made here and only lives inside the app
        self.__formatter: TicketFormatter = TicketFormatter()
        # each menu option points at one method, so there is no long if/elif chain
        self.__actions: dict[str, Callable[[], None]] = {
            "1": self.submit_ticket,
            "2": self.view_all_tickets,
            "3": self.search_ticket,
            "4": self.close_ticket,
            "5": self.reopen_ticket,
            "6": self.export_tickets,
            "8": self.filter_tickets,
        }

    def run(self) -> None:
        self.__io.show_welcome()
        self.__io.display_message(f"Version {self.__version}")
        try:
            count = self.__data.load()
        except StorageError as error:
            self.__io.display_message(f"ERROR: {error}")
            return
        self.__io.display_message(f"{count} ticket(s) loaded.")
        try:
            while True:
                option = self.__io.get_menu_option()
                if option == HelpdeskApp.EXIT_OPTION:
                    self.__io.display_message("\nThank you for using the Helpdesk Ticket Triage System.")
                    return
                action = self.__actions.get(option)
                if action is None:
                    self.__io.display_message("Invalid option, please pick 1 to 8.")
                else:
                    self.__run_safely(action)
        except (KeyboardInterrupt, EOFError):
            self.__io.display_message("\nExiting the Helpdesk Ticket Triage System.")

    def __run_safely(self, action: Callable[[], None]) -> None:
        # last line of defence: every expected problem has its own message, this catches the
        # unexpected ones so one broken feature never closes the app, and the details go to the log
        try:
            action()
        except EOFError:
            raise
        except Exception:
            logger.exception("Menu option failed")
            self.__io.display_message(
                "Sorry, something went wrong with that option. "
                "The details were saved in the log file, please try again."
            )

    def submit_ticket(self) -> None:
        try:
            details = self.__io.collect_ticket_input()
            ticket = self.__data.create_ticket(details)
        except (ValueError, TicketError) as error:
            self.__io.display_message(f"ERROR: {error}")
            return

        self.__io.display_message("\nAnalysing ticket with AI...")
        analysis = self.__ai.analyse_ticket(
            title=ticket.title,
            description=ticket.description,
            device=ticket.device,
            error_message=ticket.error_message,
            steps_attempted=ticket.steps_attempted,
        )
        result = self.__logic.process_ticket(ticket.to_dict(), analysis)
        if result.get("action") == "REJECT":
            self.__io.display_message("ERROR: AI response failed validation rules.")
            return

        ticket.attach_analysis(result)
        try:
            self.__data.add(ticket)
        except (TicketError, StorageError) as error:
            self.__io.display_message(f"Ticket was not saved. {error}")
            return
        self.__io.display_submission_result(ticket.to_dict())
        support_message = result.get("support_message")
        if isinstance(support_message, str) and support_message != "":
            self.__io.display_message(f"\n{support_message}")
        if ticket.escalated:
            self.__io.display_message("This ticket has been escalated to the IT security team.")
        elif ticket.requires_manual_review:
            self.__io.display_message("This ticket will be checked by IT support staff.")

    def view_all_tickets(self) -> None:
        self.__io.display_message(self.__formatter.format_list(self.__data.queue(), "All Tickets"))

    def search_ticket(self) -> None:
        ticket_id = self.__io.get_ticket_id()
        try:
            ticket = self.__data.find(ticket_id)
        except TicketError as error:
            self.__io.display_message(str(error))
            return
        self.__io.display_message(self.__formatter.format_detail(ticket))

    def close_ticket(self) -> None:
        ticket_id = self.__io.get_ticket_id("Enter ticket ID to close: ")
        try:
            ticket = self.__data.close_ticket(ticket_id)
        except (TicketError, StorageError) as error:
            self.__io.display_message(str(error))
            return
        self.__io.display_message(f"Ticket {ticket.ticket_id} closed.")

    def reopen_ticket(self) -> None:
        ticket_id = self.__io.get_ticket_id("Enter ticket ID to reopen: ")
        try:
            ticket = self.__data.reopen_ticket(ticket_id)
        except (TicketError, StorageError) as error:
            self.__io.display_message(str(error))
            return
        self.__io.display_message(f"Ticket {ticket.ticket_id} reopened.")

    def export_tickets(self) -> None:
        # strategy: every exporter is used the same way, the app never checks which kind it has
        for exporter in self.__exporters:
            try:
                path = self.__data.export(exporter, self.__export_folder)
            except StorageError as error:
                self.__io.display_message(str(error))
            else:
                self.__io.display_message(f"{exporter.label} saved to {path}")

    def filter_tickets(self) -> None:
        answers = self.__io.collect_filter_criteria()
        try:
            ticket_filter = TicketFilterFactory.from_answers(answers)
        except ValueError as error:
            self.__io.display_message(f"ERROR: {error}")
            return
        matches = self.__data.query(ticket_filter)
        heading = f"Filter: {ticket_filter.describe()} ({len(matches)} of {len(self.__data.tickets)} tickets)"
        self.__io.display_message(self.__formatter.format_list(matches, heading, "No tickets match."))
