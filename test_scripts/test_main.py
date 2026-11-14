#python -m unittest discover -s test_scripts -p "test_main.py" -v

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from errors.storage_error import StorageError
from exporters.csv_ticket_exporter import CsvTicketExporter
from exporters.summary_report_exporter import SummaryReportExporter
from helpdesk_app import HelpdeskApp
from managers.data_manager import DataManager
from managers.io_manager import IOManager
from managers.logic_manager import LogicManager
from storage.json_ticket_repository import JsonTicketRepository


class TestMainIO(unittest.TestCase):
    def setUp(self):
        # A fake AI manager, so these tests need no SDK, API key, or network.
        self.ai = Mock()
        self.ai.analyse_ticket.return_value = {
            # Match the current AI response schema expected by LogicManager.
            "extracted_hardware": ["WiFi adapter"],
            "extracted_software": [],
            "sentiment_score": 7,
            "summary": "Cannot connect to campus WiFi",
            "troubleshooting": ["Check the WiFi adapter", "Reconnect to campus WiFi"],
        }

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.ticket_file = Path(temp.name) / "tickets.json"
        self.csv_file = Path(temp.name) / "tickets.csv"
        self.data = DataManager(JsonTicketRepository(self.ticket_file))
        self.app = HelpdeskApp(
            io_manager=IOManager(),
            ai_manager=self.ai,
            logic_manager=LogicManager(),
            data_manager=self.data,
            exporters=[CsvTicketExporter(), SummaryReportExporter()],
            export_folder=Path(temp.name),
        )
        self.answers = ["Alex", "2600001", "Dell Latitude 5430", "WiFi problem",
                        "Cannot connect to school WiFi", "Restarted laptop", "", "High"]

    def test_submit_sends_input_to_ai_and_saves_processed_result(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=self.answers), patch("sys.stdout", output):
            self.app.submit_ticket()
        self.ai.analyse_ticket.assert_called_once_with(
            title="WiFi problem", description="Cannot connect to school WiFi",
            device="Dell Latitude 5430", error_message="", steps_attempted="Restarted laptop",
        )
        self.assertEqual(len(self.data.tickets), 1)
        self.assertTrue(self.ticket_file.exists())
        saved = json.loads(self.ticket_file.read_text(encoding="utf-8"))
        self.assertEqual(saved, [ticket.to_dict() for ticket in self.data.tickets])
        self.assertEqual(saved[0]["student_id"], "2600001")
        self.assertEqual(saved[0]["final_priority"], "High")
        self.assertEqual(saved[0]["ai_analysis"]["category"], "Network")
        self.assertIn("1. Check the WiFi adapter", output.getvalue())

    def test_rejected_ai_response_is_not_saved(self):
        self.ai.analyse_ticket.return_value = {}
        with patch("builtins.input", side_effect=self.answers), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.submit_ticket()
        self.assertEqual(self.data.tickets, [])
        self.assertFalse(self.ticket_file.exists())
        self.assertIn("AI response failed validation", output.getvalue())

    def test_input_validation_error_is_reported_before_ai_call(self):
        with patch.object(IOManager, "collect_ticket_input", side_effect=ValueError("Invalid input")), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.submit_ticket()
        self.ai.analyse_ticket.assert_not_called()
        self.assertIn("ERROR: Invalid input", output.getvalue())

    def test_failed_save_does_not_report_success(self):
        with patch("builtins.input", side_effect=self.answers), patch.object(self.data, "add", side_effect=StorageError("disk full")), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.submit_ticket()
        self.assertNotIn("successfully processed and saved", output.getvalue())

    def test_all_menu_routes_with_temporary_files(self):
        answers = ["1"] + self.answers + [
            "2", "3", "0001", "3", "9999", "4", "0001", "5", "0001", "6", "7",
        ]
        with patch("builtins.input", side_effect=answers), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.run()
        text = output.getvalue()
        self.assertIn("All Tickets", text)
        self.assertIn("Ticket ID: 0001", text)
        self.assertIn("Ticket 9999 not found.", text)
        self.assertIn("Ticket 0001 closed.", text)
        self.assertIn("Ticket 0001 reopened.", text)
        self.assertIn("Thank you", text)
        self.assertTrue(self.csv_file.exists())
        saved = json.loads(self.ticket_file.read_text(encoding="utf-8"))
        self.assertEqual(saved[0]["status"], "Reopened")
        self.assertIn("0001", self.csv_file.read_text(encoding="utf-8"))
        self.ai.analyse_ticket.assert_called_once()

    def test_invalid_menu_option_then_exit(self):
        with patch("builtins.input", side_effect=["wrong", "7"]), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.run()
        self.assertIn("Invalid option", output.getvalue())
        self.ai.analyse_ticket.assert_not_called()


if __name__ == "__main__":
    unittest.main()
