import io
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from exporters.csv_ticket_exporter import CsvTicketExporter
from exporters.summary_report_exporter import SummaryReportExporter
from helpdesk_app import HelpdeskApp
from managers.ai_manager import AIManager
from managers.data_manager import DataManager
from managers.io_manager import IOManager
from managers.logic_manager import LogicManager
from storage.json_ticket_repository import JsonTicketRepository

# main.py only builds the objects and hands them to the app, all the rules live in the classes
if __name__ == "__main__":
    # a strange character in a ticket should print as "?" instead of crashing the app
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(errors="replace")

    # load the api key frm .env file before the AI manager starts
    load_dotenv(override=True)

    if not os.getenv("GEMINI_API_KEY"):
        print("\n[SYSTEM WARNING]: GEMINI_API_KEY is missing from .env.")
        print("The system will launch in Offline Logic Fallback Mode.\n")

    data_folder = Path(os.environ.get("HELPDESK_DATA_DIR", Path(__file__).resolve().parent / "data"))

    # warnings show on screen, the full technical details go to data/helpdesk.log
    screen = logging.StreamHandler()
    screen.setLevel(logging.WARNING)
    screen.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    handlers: list[logging.Handler] = [screen]
    try:
        data_folder.mkdir(parents=True, exist_ok=True)
        log_file = logging.FileHandler(data_folder / "helpdesk.log", encoding="utf-8")
        log_file.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handlers.append(log_file)
    except OSError:
        print("[SYSTEM WARNING]: Could not open the log file, problems will only be shown on screen.")
    logging.basicConfig(level=logging.INFO, handlers=handlers)

    app = HelpdeskApp(
        io_manager=IOManager(),
        ai_manager=AIManager(),
        logic_manager=LogicManager(),
        data_manager=DataManager(JsonTicketRepository(data_folder / "tickets.json")),
        exporters=[CsvTicketExporter(), SummaryReportExporter()],
        export_folder=data_folder,
        version=os.environ.get("APP_VERSION", "dev"),
    )
    app.run()
