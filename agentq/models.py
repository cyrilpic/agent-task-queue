from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    kind: str
    spec: str
    status: Status = Status.PENDING
    attempts: int = 0
    output: str | None = None
    errors: list[str] = field(default_factory=list)
