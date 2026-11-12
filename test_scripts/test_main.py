#python -m unittest discover -s test -p "test_main.py" -v


import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

from managers.io_manager import IOManager
from managers.logic_manager import LogicManager


class TestMainIO(unittest.TestCase):
    def setUp(self):
        # Replace these imports BEFORE loading main: the real AI module creates
        # a client at import time. These tests need no SDK, API key, or network.
        fake_ai = ModuleType("managers.ai_manager")
        fake_ai.analyse_ticket = Mock(return_value={
            # Match the current AI response schema expected by LogicManager.
            "extracted_hardware": ["WiFi adapter"],
            "extracted_software": [],
            "sentiment_score": 7,
            "summary": "Cannot connect to campus WiFi",
            "troubleshooting": ["Check the WiFi adapter", "Reconnect to campus WiFi"],
        })
        fake_dotenv = ModuleType("dotenv")
        fake_dotenv.load_dotenv = Mock()
        # This script is inside test/, while main.py is at the project root.
        path = Path(__file__).resolve().parents[1] / "main.py"
        spec = importlib.util.spec_from_file_location("main_under_test", path)
        self.app = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", {
            "managers.ai_manager": fake_ai, "dotenv": fake_dotenv,
        }):
            spec.loader.exec_module(self.app)

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.ticket_file = Path(temp.name) / "tickets.json"
        self.csv_file = Path(temp.name) / "tickets.csv"
        storage = patch.multiple(
            self.app.data_manager, DATA_FOLDER=temp.name,
            TICKET_FILE=str(self.ticket_file), CSV_FILE=str(self.csv_file),
        )
        storage.start()
        self.addCleanup(storage.stop)
        self.answers = ["Alex", "2600001", "Dell Latitude 5430", "WiFi problem",
                        "Cannot connect to school WiFi", "Restarted laptop", "", "High"]

    def test_submit_sends_input_to_ai_and_saves_processed_result(self):
        tickets = []
        output = io.StringIO()
        with patch("builtins.input", side_effect=self.answers), patch("sys.stdout", output):
            self.app.submit_ticket(tickets, IOManager(), LogicManager())
        self.app.analyse_ticket.assert_called_once_with(
            title="WiFi problem", description="Cannot connect to school WiFi",
            device="Dell Latitude 5430", error_message="", steps_attempted="Restarted laptop",
        )
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]["student_id"], "2600001")
        self.assertEqual(tickets[0]["final_priority"], "High")
        self.assertTrue(self.ticket_file.exists())
        saved = json.loads(self.ticket_file.read_text(encoding="utf-8"))
        self.assertEqual(saved, tickets)
        self.assertEqual(saved[0]["ai_analysis"]["category"], "Network")
        self.assertIn("1. Check the WiFi adapter", output.getvalue())

    def test_rejected_ai_response_is_not_saved(self):
        self.app.analyse_ticket.return_value = {}
        tickets = []
        with patch("builtins.input", side_effect=self.answers), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.submit_ticket(tickets, IOManager(), LogicManager())
        self.assertEqual(tickets, [])
        self.assertFalse(self.ticket_file.exists())
        self.assertIn("AI response failed validation", output.getvalue())

    def test_input_validation_error_is_reported_before_ai_call(self):
        manager = IOManager()
        with patch.object(manager, "collect_ticket_input", side_effect=ValueError("Invalid input")), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.submit_ticket([], manager, LogicManager())
        self.app.analyse_ticket.assert_not_called()
        self.assertIn("ERROR: Invalid input", output.getvalue())

    def test_failed_save_does_not_report_success(self):
        with patch("builtins.input", side_effect=self.answers), patch.object(self.app.data_manager, "add_ticket", return_value=False), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.submit_ticket([], IOManager(), LogicManager())
        self.assertNotIn("successfully processed and saved", output.getvalue())

    def test_all_menu_routes_with_temporary_files(self):
        answers = ["1"] + self.answers + [
            "2", "3", "0001", "3", "9999", "4", "0001", "5", "0001", "6", "7",
        ]
        with patch("builtins.input", side_effect=answers), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.main()
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
        self.app.analyse_ticket.assert_called_once()

    def test_invalid_menu_option_then_exit(self):
        with patch("builtins.input", side_effect=["wrong", "7"]), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.app.main()
        self.assertIn("Invalid option", output.getvalue())
        self.app.analyse_ticket.assert_not_called()


if __name__ == "__main__":
    unittest.main()