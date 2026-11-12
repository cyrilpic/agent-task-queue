"""Validators that check a worker's output before a task is marked done."""

import ast
from collections import defaultdict
from typing import Callable

from agentq.models import Task

# A validator returns None when the output is fine, or a message saying what's wrong.
Validator = Callable[[Task], str | None]


class ValidatorRegistry:
    def __init__(self) -> None:
        self._by_kind: dict[str, list[Validator]] = defaultdict(list)

    def register(self, kind: str, validator: Validator) -> None:
        self._by_kind[kind].append(validator)

    def run(self, task: Task) -> list[str]:
        failures = []
        for validator in self._by_kind.get(task.kind, []):
            message = validator(task)
            if message:
                failures.append(message)
        return failures


def python_parses(task: Task) -> str | None:
    try:
        ast.parse(task.output or "")
    except SyntaxError as exc:
        return f"output is not valid Python: {exc.msg} (line {exc.lineno})"
    return None


def not_empty(task: Task) -> str | None:
    if not (task.output or "").strip():
        return "output is empty"
    return None
