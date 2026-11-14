from datetime import datetime
from typing import Any

from errors.ticket_error import TicketError
from models.status_change import StatusChange


class Ticket:
    # one helpdesk ticket, the fields are private so the status only changes through close() and reopen()

    STATUSES = ("Open", "Closed", "Reopened")
    PRIORITIES = ("Low", "Medium", "High", "Critical")
    REQUIRED_KEYS = ("ticket_id", "username", "device", "title", "description", "status", "created_at")

    def __init__(
        self,
        ticket_id: str,
        username: str,
        student_id: str,
        device: str,
        title: str,
        description: str,
        steps_attempted: str = "",
        error_message: str = "",
        user_priority: str = "Medium",
        created_at: str | None = None,
    ):
        if user_priority not in Ticket.PRIORITIES:
            raise ValueError(f"Unknown priority {user_priority!r}.")
        now = created_at if created_at is not None else Ticket.__now()
        self.__ticket_id: str = ticket_id
        self.__username: str = username
        self.__student_id: str = student_id
        self.__device: str = device
        self.__title: str = title
        self.__description: str = description
        self.__steps_attempted: str = steps_attempted
        self.__error_message: str = error_message
        self.__user_priority: str = user_priority
        self.__status: str = "Open"
        self.__ai_analysis: dict[str, object] = {}
        self.__final_priority: str = user_priority
        self.__escalated: bool = False
        self.__requires_manual_review: bool = False
        self.__created_at: str = now
        self.__updated_at: str = now
        # composition: the ticket makes its own history and the history goes when the ticket goes
        self.__history: list[StatusChange] = [StatusChange("", "Open", now)]

    def __repr__(self) -> str:
        return f"Ticket({self.__ticket_id!r}, {self.__title!r}, {self.__status})"

    @property
    def ticket_id(self) -> str:
        return self.__ticket_id

    @property
    def username(self) -> str:
        return self.__username

    @property
    def student_id(self) -> str:
        return self.__student_id

    @property
    def device(self) -> str:
        return self.__device

    @property
    def title(self) -> str:
        return self.__title

    @property
    def description(self) -> str:
        return self.__description

    @property
    def steps_attempted(self) -> str:
        return self.__steps_attempted

    @property
    def error_message(self) -> str:
        return self.__error_message

    @property
    def user_priority(self) -> str:
        return self.__user_priority

    @property
    def status(self) -> str:
        return self.__status

    @property
    def final_priority(self) -> str:
        return self.__final_priority

    @property
    def escalated(self) -> bool:
        return self.__escalated

    @property
    def requires_manual_review(self) -> bool:
        return self.__requires_manual_review

    @property
    def created_at(self) -> str:
        return self.__created_at

    @property
    def updated_at(self) -> str:
        return self.__updated_at

    @property
    def ai_analysis(self) -> dict[str, object]:
        # a copy, so code outside cannot change the saved ai result by accident
        return dict(self.__ai_analysis)

    @property
    def history(self) -> tuple[StatusChange, ...]:
        return tuple(self.__history)

    @property
    def category(self) -> str:
        category = self.__ai_analysis.get("category")
        if isinstance(category, str) and category != "":
            return category
        return "Unassigned"

    @property
    def is_closed(self) -> bool:
        return self.__status == "Closed"

    def attach_analysis(self, analysis: dict[str, object]) -> None:
        # keep the checked ai + logic result inside the ticket so both get saved together
        if self.is_closed:
            raise TicketError(f"Ticket {self.__ticket_id} is closed, reopen it first.")
        self.__ai_analysis = dict(analysis)
        priority = analysis.get("priority")
        if isinstance(priority, str) and priority in Ticket.PRIORITIES:
            self.__final_priority = priority
        self.__escalated = analysis.get("requires_escalation") is True
        self.__requires_manual_review = analysis.get("requires_manual_review") is True
        self.__updated_at = Ticket.__now()

    def close(self) -> None:
        if self.is_closed:
            raise TicketError(f"Ticket {self.__ticket_id} is already closed.")
        self.__change_status("Closed")

    def reopen(self) -> None:
        if not self.is_closed:
            raise TicketError(f"Ticket {self.__ticket_id} is not closed.")
        self.__change_status("Reopened")

    def to_dict(self) -> dict[str, Any]:
        # a plain json record, the same keys phase 1 saved plus the history list
        return {
            "ticket_id": self.__ticket_id,
            "username": self.__username,
            "student_id": self.__student_id,
            "device": self.__device,
            "title": self.__title,
            "description": self.__description,
            "steps_attempted": self.__steps_attempted,
            "user_priority": self.__user_priority,
            "error_message": self.__error_message,
            "ai_analysis": dict(self.__ai_analysis),
            "final_priority": self.__final_priority,
            "status": self.__status,
            "escalated": self.__escalated,
            "requires_manual_review": self.__requires_manual_review,
            "created_at": self.__created_at,
            "updated_at": self.__updated_at,
            "history": [change.to_dict() for change in self.__history],
        }

    @classmethod
    def from_dict(cls, record: object) -> "Ticket":
        # rebuild a saved ticket, older tickets with no student_id or history still load
        if not isinstance(record, dict):
            raise ValueError("A ticket record must be a JSON object.")
        missing = [key for key in cls.REQUIRED_KEYS if key not in record]
        if missing:
            raise ValueError(f"Ticket record is missing {', '.join(missing)}.")
        status = cls.__text(record["status"])
        if status not in cls.STATUSES:
            raise ValueError(f"Unknown status {status!r}.")
        created_at = cls.__text(record["created_at"])
        ticket = cls(
            ticket_id=cls.normalise_id(cls.__text(record["ticket_id"])),
            username=cls.__text(record["username"]),
            student_id=cls.__text(record.get("student_id")),
            device=cls.__text(record["device"]),
            title=cls.__text(record["title"]),
            description=cls.__text(record["description"]),
            steps_attempted=cls.__text(record.get("steps_attempted")),
            error_message=cls.__text(record.get("error_message")),
            user_priority=cls.__text(record.get("user_priority")) or "Medium",
            created_at=created_at,
        )
        ticket.__status = status
        analysis = record.get("ai_analysis")
        ticket.__ai_analysis = dict(analysis) if isinstance(analysis, dict) else {}
        final_priority = cls.__text(record.get("final_priority"))
        if final_priority in cls.PRIORITIES:
            ticket.__final_priority = final_priority
        ticket.__escalated = record.get("escalated") is True
        ticket.__requires_manual_review = record.get("requires_manual_review") is True
        ticket.__updated_at = cls.__text(record.get("updated_at")) or created_at
        ticket.__history = []
        history = record.get("history")
        if isinstance(history, list):
            for item in history:
                if isinstance(item, dict):
                    ticket.__history.append(StatusChange(
                        cls.__text(item.get("old_status")),
                        cls.__text(item.get("new_status")),
                        cls.__text(item.get("changed_at")),
                    ))
        return ticket

    @staticmethod
    def normalise_id(text: str) -> str:
        # "1" and " 0001 " both mean ticket 0001
        text = text.strip()
        if text.isascii() and text.isdigit():
            return text.zfill(4)
        return text

    def __change_status(self, new_status: str) -> None:
        now = Ticket.__now()
        self.__history.append(StatusChange(self.__status, new_status, now))
        self.__status = new_status
        self.__updated_at = now

    @staticmethod
    def __text(value: object) -> str:
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def __now() -> str:
        return datetime.now().isoformat(timespec="seconds")
