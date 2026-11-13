import json
import shutil
from pathlib import Path

import pytest

from errors.storage_error import StorageError
from storage.json_ticket_repository import JsonTicketRepository

TEAM_TICKET_FILE = Path(__file__).resolve().parents[1] / "data" / "tickets.json"


def test_missing_file_gives_no_tickets(ticket_file):
    repository = JsonTicketRepository(ticket_file)
    assert repository.load_all() == []
    assert repository.file_path == ticket_file


def test_save_then_load_in_a_new_folder(tmp_path, make_ticket):
    path = tmp_path / "new_folder" / "tickets.json"
    repository = JsonTicketRepository(path)
    repository.save_all([make_ticket("0001"), make_ticket("0002")])
    assert [ticket.ticket_id for ticket in repository.load_all()] == ["0001", "0002"]
    assert not path.with_name("tickets.json.tmp").exists()


def test_text_that_is_not_json_is_moved_to_a_backup(ticket_file, caplog):
    ticket_file.write_text("not json", encoding="utf-8")
    assert JsonTicketRepository(ticket_file).load_all() == []
    assert not ticket_file.exists()
    assert ticket_file.with_name("tickets.json.bak").read_text(encoding="utf-8") == "not json"
    assert "is damaged" in caplog.text


@pytest.mark.parametrize("content", [b'{"ticket_id": "0001"}', b"\xff\xfe broken bytes", b"42"])
def test_json_that_is_not_a_list_is_also_moved(ticket_file, content):
    ticket_file.write_bytes(content)
    assert JsonTicketRepository(ticket_file).load_all() == []
    assert ticket_file.with_name("tickets.json.bak").read_bytes() == content


def test_bad_records_are_skipped_and_the_good_ones_still_load(ticket_file, make_ticket, caplog):
    records = [make_ticket("0001").to_dict(), {"title": "no id"}, 5, make_ticket("0003").to_dict()]
    ticket_file.write_text(json.dumps(records), encoding="utf-8")
    tickets = JsonTicketRepository(ticket_file).load_all()
    assert [ticket.ticket_id for ticket in tickets] == ["0001", "0003"]
    assert ticket_file.exists()
    assert json.loads(ticket_file.with_name("tickets.json.bak").read_text(encoding="utf-8")) == records
    assert "2 damaged ticket record(s) skipped" in caplog.text


def test_failed_save_keeps_the_old_file_and_leaves_no_temp_file(ticket_file, make_ticket, monkeypatch):
    repository = JsonTicketRepository(ticket_file)
    repository.save_all([make_ticket("0001")])
    before = ticket_file.read_text(encoding="utf-8")

    def locked(source, target):
        raise PermissionError("file is open in another program")

    monkeypatch.setattr("storage.json_ticket_repository.os.replace", locked)
    with pytest.raises(StorageError, match="Could not save"):
        repository.save_all([make_ticket("0001"), make_ticket("0002")])
    assert ticket_file.read_text(encoding="utf-8") == before
    assert not ticket_file.with_name("tickets.json.tmp").exists()


def test_unreadable_file_stops_instead_of_starting_empty(ticket_file, monkeypatch):
    ticket_file.write_text("[]", encoding="utf-8")

    def locked(self, *args, **kwargs):
        raise PermissionError("file is locked")

    monkeypatch.setattr(Path, "read_text", locked)
    with pytest.raises(StorageError, match="Could not open"):
        JsonTicketRepository(ticket_file).load_all()


def test_damaged_file_that_cannot_be_moved_raises(ticket_file, monkeypatch):
    ticket_file.write_text("not json", encoding="utf-8")

    def locked(source, target):
        raise PermissionError("file is locked")

    monkeypatch.setattr("storage.json_ticket_repository.os.replace", locked)
    with pytest.raises(StorageError, match="could not be moved"):
        JsonTicketRepository(ticket_file).load_all()


def test_backup_copy_that_fails_raises(ticket_file, make_ticket, monkeypatch):
    ticket_file.write_text(json.dumps([make_ticket().to_dict(), {}]), encoding="utf-8")

    def disk_full(source, target):
        raise OSError("disk full")

    monkeypatch.setattr("storage.json_ticket_repository.shutil.copyfile", disk_full)
    with pytest.raises(StorageError, match="Could not copy"):
        JsonTicketRepository(ticket_file).load_all()


def test_team_ticket_file_loads_and_saves_without_losing_anything(tmp_path):
    copy = tmp_path / "tickets.json"
    shutil.copyfile(TEAM_TICKET_FILE, copy)
    original = json.loads(copy.read_text(encoding="utf-8"))

    repository = JsonTicketRepository(copy)
    repository.save_all(repository.load_all())

    saved = json.loads(copy.read_text(encoding="utf-8"))
    assert len(saved) == len(original)
    for before, after in zip(original, saved, strict=True):
        for key, value in before.items():
            assert after[key] == value, f"ticket {before['ticket_id']} lost {key}"
