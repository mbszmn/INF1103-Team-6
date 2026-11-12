# python -m unittest discover -s test -p "test_io_manager.py" -v

import copy
import io
import unittest
from unittest.mock import patch

# Add the project root to sys.path so Python can find the managers folder.
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from managers.io_manager import IOManager


class TestIOManager(unittest.TestCase):
    def setUp(self):
        self.io = IOManager()
        self.valid_data = {
            "username": "Alex",
            "student_id": "2600001",
            "device": "Dell Latitude 5430",
            "title": "WiFi problem",
            "description": "Cannot connect to school WiFi",
            "steps_attempted": "",
            "error_message": "",
            "user_priority": "High",
        }

    def collect(self, answers):
        with patch("builtins.input", side_effect=answers), patch("builtins.print"):
            return self.io.collect_ticket_input()

    def answers(self):
        return [self.valid_data[field] for field in (
            "username", "student_id", "device", "title", "description",
            "steps_attempted", "error_message", "user_priority",
        )]

    def test_collects_ticket_with_optional_fields_empty(self):
        self.assertEqual(self.collect(self.answers()), self.valid_data)

    def test_trims_input_and_normalises_staff_and_priority(self):
        answers = self.answers()
        answers[0] = "  Alex  "
        answers[1] = " STAFF "
        answers[-1] = " high "
        result = self.collect(answers)
        self.assertEqual(result["username"], "Alex")
        self.assertEqual(result["student_id"], "staff")
        self.assertEqual(result["user_priority"], "High")

    def test_reprompts_for_empty_required_field(self):
        self.assertEqual(self.collect(["", "  "] + self.answers()), self.valid_data)

    def test_reprompts_for_invalid_student_id(self):
        answers = self.answers()
        answers[1:1] = ["", "26ABC"]
        self.assertEqual(self.collect(answers), self.valid_data)

    def test_reprompts_for_short_description(self):
        answers = self.answers()
        answers[4:4] = ["", "broken"]
        self.assertEqual(self.collect(answers), self.valid_data)

    def test_reprompts_for_invalid_priority(self):
        answers = self.answers()
        answers[-1:-1] = ["", "Urgent"]
        self.assertEqual(self.collect(answers), self.valid_data)

    def test_accepts_valid_input(self):
        self.assertEqual(self.io.validate_ticket_input(self.valid_data), [])

    def test_reports_each_missing_required_field(self):
        errors = self.io.validate_ticket_input({})
        for field in ("username", "student_id", "device", "title", "description"):
            self.assertIn(f"{field} cannot be empty.", errors)

    def test_rejects_whitespace_required_fields(self):
        for field in ("username", "student_id", "device", "title", "description"):
            with self.subTest(field=field):
                data = self.valid_data.copy()
                data[field] = "  "
                self.assertIn(f"{field} cannot be empty.",
                              self.io.validate_ticket_input(data))


    def test_direct_validation_checks_student_description_and_priority(self):
        for field, value in (("student_id", "26ABC"), ("description", "short"),
                             ("user_priority", "Urgent")):
            with self.subTest(field=field):
                data = self.valid_data.copy()
                data[field] = value
                self.assertTrue(self.io.validate_ticket_input(data))

    def test_rejects_missing_priority(self):
        del self.valid_data["user_priority"]
        self.assertTrue(self.io.validate_ticket_input(self.valid_data))

    def test_rejects_non_text_values_without_crashing(self):
        for field in self.valid_data:
            for value in (None, 123, [], {}):
                with self.subTest(field=field, value=value):
                    data = self.valid_data.copy()
                    data[field] = value
                    self.assertIn(f"{field} must be text.",
                                  self.io.validate_ticket_input(data))

    def test_rejects_non_dictionary(self):
        self.assertEqual(self.io.validate_ticket_input(None),
                         ["Ticket input must be a dictionary."])

    def test_description_boundary(self):
        self.valid_data["description"] = "123456789"
        self.assertTrue(self.io.validate_ticket_input(self.valid_data))
        self.valid_data["description"] = "1234567890"
        self.assertEqual(self.io.validate_ticket_input(self.valid_data), [])

    def test_all_four_priorities_are_accepted(self):
        for priority in ("Low", "Medium", "High", "Critical"):
            with self.subTest(priority=priority):
                self.valid_data["user_priority"] = priority
                self.assertEqual(self.io.validate_ticket_input(self.valid_data), [])

    def test_validation_does_not_change_data(self):
        original = self.valid_data.copy()
        self.io.validate_ticket_input(self.valid_data)
        self.assertEqual(self.valid_data, original)


    def test_menu_and_ticket_id_trim_spaces(self):
        with patch("builtins.input", side_effect=[" 7 ", " 0001 "]), patch("builtins.print"):
            self.assertEqual(self.io.get_menu_option(), "7")
            self.assertEqual(self.io.get_ticket_id(), "0001")

    def test_display_message(self):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.io.display_message("Ticket saved.")
        self.assertEqual(output.getvalue(), "Ticket saved.\n")

    def test_show_welcome(self):
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.io.show_welcome()
        self.assertIn("AI SIT HELPDESK TICKET TRIAGE SYSTEM", output.getvalue())

    def test_displays_ai_steps_without_modifying_ticket(self):
        # Only supply the fields used by IOManager's submission display.
        ticket = {"ticket_id": "0001", "final_priority": "High"}
        ticket["ai_analysis"] = {
            "category": "Network", "summary": "WiFi unavailable",
            "troubleshooting": ["Check the adapter", "Reconnect to campus WiFi"],
        }
        original = copy.deepcopy(ticket)
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.io.display_submission_result(ticket)
        text = output.getvalue()
        self.assertIn("Ticket 0001 successfully processed and saved!", text)
        self.assertIn("Category: Network | Priority: High", text)
        self.assertIn("1. Check the adapter", text)
        self.assertIn("2. Reconnect to campus WiFi", text)
        self.assertEqual(ticket, original)

    def test_empty_troubleshooting_does_not_print_steps_heading(self):
        ticket = {"ticket_id": "0001", "final_priority": "Medium"}
        ticket["ai_analysis"] = {"category": "Network", "troubleshooting": []}
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.io.display_submission_result(ticket)
        self.assertNotIn("Suggested Immediate Troubleshooting", output.getvalue())

if __name__ == "__main__":
    unittest.main(verbosity=2)
