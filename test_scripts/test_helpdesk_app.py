import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from errors.storage_error import StorageError
from exporters.csv_ticket_exporter import CsvTicketExporter
from managers.io_manager import IOManager
from managers.logic_manager import LogicManager

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DETAIL_FIELDS = ["username", "student_id", "device", "title", "description", "steps_attempted",
                 "error_message", "user_priority"]


def run_app(app, answers, capsys) -> str:
    with patch("builtins.input", side_effect=answers):
        app.run()
    return capsys.readouterr().out


def saved_tickets(folder: Path) -> list[dict]:
    return json.loads((folder / "tickets.json").read_text(encoding="utf-8"))


def test_new_ticket_goes_through_all_four_managers_and_is_saved(app, fake_ai, tmp_path, ticket_answers, capsys):
    output = run_app(app, ["1", *ticket_answers, "7"], capsys)

    assert fake_ai.calls == [{
        "title": "WiFi problem",
        "description": "Cannot connect to school WiFi",
        "device": "Dell Latitude 5430",
        "error_message": "",
        "steps_attempted": "Restarted laptop",
    }]
    [ticket] = saved_tickets(tmp_path)
    assert ticket["ticket_id"] == "0001"
    assert ticket["student_id"] == "2600001"
    assert ticket["final_priority"] == "High"
    assert ticket["ai_analysis"]["category"] == "Network"
    assert ticket["ai_analysis"]["summary"] == "Cannot connect to campus WiFi"
    assert ticket["requires_manual_review"] is False
    assert "Ticket 0001 successfully processed and saved!" in output
    assert "1. Check the WiFi adapter" in output


def test_with_no_ai_the_ticket_is_still_saved_with_general_steps(
    app, fake_ai, offline_reply, tmp_path, ticket_answers, capsys
):
    fake_ai.reply = offline_reply
    output = run_app(app, ["1", *ticket_answers, "7"], capsys)

    [ticket] = saved_tickets(tmp_path)
    assert ticket["requires_manual_review"] is True
    assert len(ticket["ai_analysis"]["troubleshooting"]) == 3
    assert "temporarily unavailable" in output
    assert "will be checked by IT support staff" in output


def test_security_ticket_is_escalated(app, tmp_path, ticket_answers, capsys):
    ticket_answers[3] = "Clicked a phishing link"
    output = run_app(app, ["1", *ticket_answers, "7"], capsys)

    [ticket] = saved_tickets(tmp_path)
    assert ticket["escalated"] is True
    assert ticket["ai_analysis"]["category"] == "Security"
    assert "escalated to the IT security team" in output


def test_ai_reply_that_fails_the_checks_is_not_saved(app, fake_ai, tmp_path, ticket_answers, capsys):
    fake_ai.reply = {"summary": "the other fields are missing"}
    output = run_app(app, ["1", *ticket_answers, "7"], capsys)

    assert "ERROR: AI response failed validation rules." in output
    assert not (tmp_path / "tickets.json").exists()


def test_input_error_is_shown_before_the_ai_is_asked(app, fake_ai, capsys):
    with patch.object(IOManager, "collect_ticket_input", side_effect=ValueError("Invalid input")):
        app.submit_ticket()
    assert "ERROR: Invalid input" in capsys.readouterr().out
    assert fake_ai.calls == []


def test_failed_save_is_reported_and_nothing_is_kept(app, ticket_answers, capsys, monkeypatch):
    def disk_full(self, tickets):
        raise StorageError("Could not save tickets.")

    monkeypatch.setattr("storage.json_ticket_repository.JsonTicketRepository.save_all", disk_full)
    output = run_app(app, ["1", *ticket_answers, "2", "7"], capsys)

    assert "Ticket was not saved. Could not save tickets." in output
    assert "successfully processed" not in output
    assert "No tickets yet." in output


def test_every_menu_option_works_together(app, tmp_path, ticket_answers, capsys):
    answers = [
        "1", *ticket_answers,
        "2",
        "3", "1",
        "3", "9999",
        "4", "1",
        "4", "1",
        "5", "1",
        "6",
        "8", "", "high", "", "wifi",
        "9",
        "7",
    ]
    output = run_app(app, answers, capsys)

    for expected in [
        "0 ticket(s) loaded.",
        "All Tickets",
        "Ticket ID: 0001",
        "Ticket 9999 not found.",
        "Ticket 0001 closed.",
        "Ticket 0001 is already closed.",
        "Ticket 0001 reopened.",
        "CSV file saved to",
        "Summary report saved to",
        'Filter: priority is High and text has "wifi" (1 of 1 tickets)',
        "Invalid option, please pick 1 to 8.",
        "Thank you for using the Helpdesk Ticket Triage System.",
    ]:
        assert expected in output
    [ticket] = saved_tickets(tmp_path)
    assert ticket["status"] == "Reopened"
    assert [change["new_status"] for change in ticket["history"]] == ["Open", "Closed", "Reopened"]
    assert (tmp_path / "tickets.csv").exists()
    assert (tmp_path / "ticket_summary.txt").exists()


def test_filter_with_a_bad_answer_says_what_is_allowed(app, capsys):
    output = run_app(app, ["8", "opn", "", "", "", "7"], capsys)
    assert "ERROR: Status must be one of: Open, Closed, Reopened." in output


def test_damaged_ticket_file_is_backed_up_and_the_app_still_starts(app, tmp_path, capsys):
    (tmp_path / "tickets.json").write_text("{broken", encoding="utf-8")
    output = run_app(app, ["7"], capsys)
    assert "0 ticket(s) loaded." in output
    assert (tmp_path / "tickets.json.bak").read_text(encoding="utf-8") == "{broken"


def test_unreadable_ticket_file_stops_before_the_menu(app, capsys, monkeypatch):
    def locked(self):
        raise StorageError("Could not open tickets.json. Close it in other programs and try again.")

    monkeypatch.setattr("storage.json_ticket_repository.JsonTicketRepository.load_all", locked)
    output = run_app(app, [], capsys)
    assert "ERROR: Could not open tickets.json." in output
    assert "MENU" not in output


@pytest.mark.parametrize("stop", [KeyboardInterrupt, EOFError], ids=["ctrl-c", "input closed"])
def test_ctrl_c_or_closed_input_exits_without_a_traceback(app, capsys, stop):
    output = run_app(app, [stop], capsys)
    assert "Exiting the Helpdesk Ticket Triage System." in output


def test_unexpected_bug_is_logged_and_the_app_keeps_running(app, ticket_answers, capsys, caplog, monkeypatch):
    def broken(self, ticket, ai_response):
        raise RuntimeError("bug inside the logic manager")

    monkeypatch.setattr(LogicManager, "process_ticket", broken)
    output = run_app(app, ["1", *ticket_answers, "2", "7"], capsys)

    assert "Sorry, something went wrong with that option." in output
    assert "All Tickets" in output
    assert "Thank you for using the Helpdesk Ticket Triage System." in output
    assert "bug inside the logic manager" in caplog.text


def test_input_closing_in_the_middle_of_a_ticket_exits_cleanly(app, capsys):
    output = run_app(app, ["1", "Alex", "2600001", EOFError], capsys)
    assert "Exiting the Helpdesk Ticket Triage System." in output
    assert "Sorry, something went wrong" not in output


def test_bad_priority_is_reported_before_the_ai_is_asked(app, fake_ai, ticket_answers, capsys):
    details = dict(zip(DETAIL_FIELDS, ticket_answers, strict=True), user_priority="Urgent")
    with patch.object(IOManager, "collect_ticket_input", return_value=details):
        app.submit_ticket()
    assert "ERROR: Unknown priority 'Urgent'." in capsys.readouterr().out
    assert fake_ai.calls == []


def test_close_and_reopen_of_a_missing_ticket_say_so(app, capsys):
    output = run_app(app, ["5", "42", "4", "42", "7"], capsys)
    assert output.count("Ticket 0042 not found.") == 2


def test_one_export_failing_does_not_stop_the_other(app, capsys, monkeypatch):
    def locked(self, tickets, folder):
        raise StorageError("Could not write tickets.csv, close it if it is open in another program.")

    monkeypatch.setattr(CsvTicketExporter, "export", locked)
    output = run_app(app, ["6", "7"], capsys)
    assert "Could not write tickets.csv" in output
    assert "Summary report saved to" in output


def run_main(working_folder: Path, data_folder: Path) -> subprocess.CompletedProcess:
    env = dict(
        os.environ,
        GEMINI_API_KEY="",
        GOOGLE_API_KEY="",
        HELPDESK_DATA_DIR=str(data_folder),
        PYTHONIOENCODING="utf-8",
    )
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "main.py")],
        input="7\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=working_folder,
        env=env,
        timeout=120,
        check=False,
    )


def test_main_starts_and_exits_from_any_folder(tmp_path):
    # in CI there is no .env, so this also proves the app starts with no API key
    result = run_main(tmp_path, tmp_path / "data")
    assert result.returncode == 0, result.stderr
    assert "AI SIT HELPDESK TICKET TRIAGE SYSTEM" in result.stdout
    assert "0 ticket(s) loaded." in result.stdout
    assert "Thank you for using the Helpdesk Ticket Triage System." in result.stdout
    assert (tmp_path / "data" / "helpdesk.log").exists()


def test_main_shows_a_damaged_file_warning_and_logs_it(tmp_path):
    data_folder = tmp_path / "data"
    data_folder.mkdir()
    (data_folder / "tickets.json").write_text("{broken", encoding="utf-8")
    result = run_main(tmp_path, data_folder)
    assert result.returncode == 0, result.stderr
    assert "is damaged" in result.stderr
    assert "is damaged" in (data_folder / "helpdesk.log").read_text(encoding="utf-8")
    assert (data_folder / "tickets.json.bak").exists()
