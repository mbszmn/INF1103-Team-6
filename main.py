import logging
import os
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
    # load the api key frm .env file before the AI manager starts
    load_dotenv(override=True)

    if not os.getenv("GEMINI_API_KEY"):
        print("\n[SYSTEM WARNING]: GEMINI_API_KEY is missing from .env.")
        print("The system will launch in Offline Logic Fallback Mode.\n")

    logging.basicConfig(level=logging.WARNING, format="[%(levelname)s] %(message)s")
    data_folder = Path(os.environ.get("HELPDESK_DATA_DIR", Path(__file__).resolve().parent / "data"))

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
