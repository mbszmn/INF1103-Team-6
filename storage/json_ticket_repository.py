import json
import logging
import os
import shutil
from pathlib import Path

from errors.storage_error import StorageError
from models.ticket import Ticket
from storage.ticket_repository import TicketRepository

logger = logging.getLogger(__name__)


class JsonTicketRepository(TicketRepository):
    # keeps every ticket in one json file, saves to a temp file first so a crash never leaves half a file

    def __init__(self, file_path: Path):
        self.__file_path: Path = Path(file_path)

    @property
    def file_path(self) -> Path:
        return self.__file_path

    def load_all(self) -> list[Ticket]:
        if not self.__file_path.exists():
            return []
        try:
            records = json.loads(self.__file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            records = None
        except OSError as error:
            # stop here, starting empty would wipe the real file on the next save
            raise StorageError(
                f"Could not open {self.__file_path}. Close it in other programs and try again."
            ) from error

        if not isinstance(records, list):
            self.__move_damaged_file()
            return []

        tickets: list[Ticket] = []
        skipped = 0
        for record in records:
            try:
                tickets.append(Ticket.from_dict(record))
            except ValueError as error:
                skipped += 1
                logger.warning("Skipped a damaged ticket record: %s", error)
        if skipped > 0:
            self.__keep_copy_of_damaged_file(skipped)
        return tickets

    def save_all(self, tickets: list[Ticket]) -> None:
        temp_path = self.__file_path.with_name(self.__file_path.name + ".tmp")
        try:
            self.__file_path.parent.mkdir(parents=True, exist_ok=True)
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump([ticket.to_dict() for ticket in tickets], file, indent=4)
            os.replace(temp_path, self.__file_path)
        except OSError as error:
            temp_path.unlink(missing_ok=True)
            raise StorageError(
                f"Could not save tickets to {self.__file_path}. Close it in other programs and try again."
            ) from error

    def __backup_path(self) -> Path:
        return self.__file_path.with_name(self.__file_path.name + ".bak")

    def __move_damaged_file(self) -> None:
        backup = self.__backup_path()
        try:
            os.replace(self.__file_path, backup)
        except OSError as error:
            raise StorageError(f"{self.__file_path} is damaged and could not be moved to {backup}.") from error
        logger.warning("%s is damaged, moved it to %s and started with no tickets.", self.__file_path, backup)

    def __keep_copy_of_damaged_file(self, skipped: int) -> None:
        backup = self.__backup_path()
        try:
            shutil.copyfile(self.__file_path, backup)
        except OSError as error:
            raise StorageError(f"Could not copy the damaged {self.__file_path} to {backup}.") from error
        logger.warning("%d damaged ticket record(s) skipped, the original file was copied to %s.", skipped, backup)
