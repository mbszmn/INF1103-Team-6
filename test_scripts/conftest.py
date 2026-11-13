import os
from collections.abc import Callable
from pathlib import Path

import pytest
from hypothesis import settings

from exporters.csv_ticket_exporter import CsvTicketExporter
from exporters.summary_report_exporter import SummaryReportExporter
from helpdesk_app import HelpdeskApp
from managers.data_manager import DataManager
from managers.io_manager import IOManager
from managers.logic_manager import LogicManager
from models.ticket import Ticket
from storage.json_ticket_repository import JsonTicketRepository

# CI gets the same random examples every run so a failure can be repeated
settings.register_profile("ci", derandomize=True, max_examples=50)
settings.register_profile("dev", max_examples=50)
settings.load_profile("ci" if os.environ.get("CI") else "dev")

GOOD_AI_REPLY = {
    "extracted_hardware": ["WiFi adapter"],
    "extracted_software": [],
    "sentiment_score": 7,
    "summary": "Cannot connect to campus WiFi",
    "troubleshooting": ["Check the WiFi adapter", "Reconnect to campus WiFi"],
}

OFFLINE_AI_REPLY = {
    "ai_failed": True,
    "extracted_hardware": [],
    "extracted_software": [],
    "sentiment_score": 5,
    "summary": "AI was not available",
    "troubleshooting": ["Please wait for IT support."],
}

TICKET_ANSWERS = [
    "Alex", "2600001", "Dell Latitude 5430", "WiFi problem",
    "Cannot connect to school WiFi", "Restarted laptop", "", "High",
]


class FakeAIManager:
    # stands in for the real AI manager, so no test ever calls Gemini or needs an API key

    def __init__(self):
        self.reply: dict[str, object] = dict(GOOD_AI_REPLY)
        self.calls: list[dict[str, str]] = []

    def analyse_ticket(self, title: str, description: str, device: str, error_message: str,
                       steps_attempted: str) -> dict[str, object]:
        self.calls.append({
            "title": title,
            "description": description,
            "device": device,
            "error_message": error_message,
            "steps_attempted": steps_attempted,
        })
        return dict(self.reply)


@pytest.fixture
def make_ticket() -> Callable[..., Ticket]:
    def build(ticket_id: str = "0001", **changes: str) -> Ticket:
        details = {
            "username": "Alex",
            "student_id": "2600001",
            "device": "Dell Latitude 5430",
            "title": "WiFi problem",
            "description": "Cannot connect to school WiFi",
        }
        details.update(changes)
        return Ticket(ticket_id=ticket_id, **details)
    return build


@pytest.fixture
def ticket_file(tmp_path: Path) -> Path:
    return tmp_path / "tickets.json"


@pytest.fixture
def data_manager(ticket_file: Path) -> DataManager:
    manager = DataManager(JsonTicketRepository(ticket_file))
    manager.load()
    return manager


@pytest.fixture
def fake_ai() -> FakeAIManager:
    return FakeAIManager()


@pytest.fixture
def offline_reply() -> dict[str, object]:
    # what the AI manager gives back when there is no key or all three tries failed
    return dict(OFFLINE_AI_REPLY)


@pytest.fixture
def ticket_answers() -> list[str]:
    return list(TICKET_ANSWERS)


@pytest.fixture
def app(tmp_path: Path, fake_ai: FakeAIManager) -> HelpdeskApp:
    return HelpdeskApp(
        io_manager=IOManager(),
        ai_manager=fake_ai,
        logic_manager=LogicManager(),
        data_manager=DataManager(JsonTicketRepository(tmp_path / "tickets.json")),
        exporters=[CsvTicketExporter(), SummaryReportExporter()],
        export_folder=tmp_path,
    )
