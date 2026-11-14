from abc import ABC, abstractmethod
from pathlib import Path

from errors.storage_error import StorageError
from models.ticket import Ticket


class TicketExporter(ABC):
    # abstract class: export() is the same for every format, each child only decides the file name and the text

    def export(self, tickets: list[Ticket], folder: Path) -> Path:
        path = Path(folder) / self.file_name
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # errors="replace" so one broken character in old data cannot stop the whole export
            with path.open("w", encoding=self._encoding, errors="replace", newline="") as file:
                file.write(self._render(tickets))
        except OSError as error:
            raise StorageError(f"Could not write {path}, close it if it is open in another program.") from error
        return path

    @property
    @abstractmethod
    def file_name(self) -> str:
        pass

    @property
    @abstractmethod
    def label(self) -> str:
        pass

    @property
    def _encoding(self) -> str:
        return "utf-8"

    @abstractmethod
    def _render(self, tickets: list[Ticket]) -> str:
        pass
