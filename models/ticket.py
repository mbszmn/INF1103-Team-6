from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any


@dataclass # Automatically creates common class methods like __init__() for storing data
class Ticket:
    ticket_id: str
    username: str
    device: str
    title: str
    description: str
    steps_attempted: str = ""
    user_priority: str = "Medium"
    error_message: str = ""

    ai_analysis: dict[str, Any] = field(default_factory=dict)

    final_priority: str = "Medium"
    status: str = "Open"
    escalated: bool = False
    requires_manual_review: bool = False

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict:
        return asdict(self)