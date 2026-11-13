import csv
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from errors.storage_error import StorageError
from exporters.csv_ticket_exporter import CsvTicketExporter
from exporters.summary_report_exporter import SummaryReportExporter
from exporters.ticket_exporter import TicketExporter
from models.ticket import Ticket


def read_csv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.reader(file))


def test_csv_has_a_header_and_one_row_per_ticket(tmp_path, make_ticket):
    path = CsvTicketExporter().export([make_ticket("0001"), make_ticket("0002")], tmp_path)
    rows = read_csv(path)
    assert path.name == "tickets.csv"
    assert rows[0] == list(CsvTicketExporter.COLUMNS)
    assert [row[0] for row in rows[1:]] == ["0001", "0002"]


def test_csv_keeps_commas_quotes_new_lines_and_other_languages_in_one_cell(tmp_path, make_ticket):
    title = 'Excel says "not responding", then\ncloses, 文件 café'
    path = CsvTicketExporter().export([make_ticket(title=title, username='O"Brien')], tmp_path)
    rows = read_csv(path)
    assert len(rows) == 2
    assert rows[1][4] == title
    assert rows[1][1] == 'O"Brien'
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")


@given(title=st.text(alphabet=st.characters(exclude_categories=["Cs"], exclude_characters="\x00")))
def test_any_title_comes_back_the_same_from_the_csv(title):
    ticket = Ticket("0001", "Alex", "2600001", "Dell", title, "Cannot connect to school WiFi")
    with tempfile.TemporaryDirectory() as folder:
        rows = read_csv(CsvTicketExporter().export([ticket], Path(folder)))
    assert rows[1][4] == title


def test_a_broken_character_in_old_data_does_not_stop_the_export(tmp_path, make_ticket):
    path = CsvTicketExporter().export([make_ticket(title="bad \ud800 text")], tmp_path)
    assert read_csv(path)[1][4] == "bad ? text"


def test_summary_counts_tickets_and_lists_open_critical_ones(tmp_path, make_ticket):
    wifi = make_ticket("0001", user_priority="Medium")
    wifi.attach_analysis({"category": "Network", "priority": "Medium", "requires_manual_review": True})
    ransomware = make_ticket("0002", title="Ransomware", user_priority="Critical")
    ransomware.attach_analysis({"category": "Security", "priority": "Critical", "requires_escalation": True})
    fixed = make_ticket("0003", user_priority="Critical")
    fixed.close()

    report = SummaryReportExporter().export([wifi, ransomware, fixed], tmp_path).read_text(encoding="utf-8")
    assert "Total tickets: 3" in report
    assert "By status: Open 2 | Closed 1 | Reopened 0" in report
    assert "By priority: Critical 2 | High 0 | Medium 1 | Low 0" in report
    assert "By category: Network 1 | Security 1 | Unassigned 1" in report
    assert "Escalated and not closed: 1" in report
    assert "Waiting for manual review: 1" in report
    assert "0002  Ransomware  (Security, Open)" in report
    assert "0003" not in report.split("Critical tickets not closed yet:")[1]


def test_summary_says_none_when_nothing_is_critical(tmp_path, make_ticket):
    report = SummaryReportExporter().export([make_ticket()], tmp_path).read_text(encoding="utf-8")
    assert report.rstrip().endswith("none")


@pytest.mark.parametrize("exporter", [CsvTicketExporter(), SummaryReportExporter()], ids=["csv", "summary"])
def test_every_exporter_keeps_the_same_promise(tmp_path, make_ticket, exporter):
    # LSP and strategy: the app calls export() on any exporter without checking which one it is
    assert isinstance(exporter, TicketExporter)
    path = exporter.export([make_ticket()], tmp_path / "out")
    assert path == tmp_path / "out" / exporter.file_name
    assert path.read_text(encoding="utf-8-sig") != ""
    assert exporter.label != ""


@pytest.mark.parametrize("exporter", [CsvTicketExporter(), SummaryReportExporter()], ids=["csv", "summary"])
def test_export_to_a_place_that_cannot_be_written_raises(tmp_path, make_ticket, exporter):
    blocker = tmp_path / "not_a_folder"
    blocker.write_text("this is a file", encoding="utf-8")
    with pytest.raises(StorageError, match="Could not write"):
        exporter.export([make_ticket()], blocker)


def test_the_base_class_cannot_be_used_on_its_own():
    with pytest.raises(TypeError):
        TicketExporter()
