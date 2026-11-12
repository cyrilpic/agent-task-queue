import time
from collections import deque
from typing import Callable

from agentq.models import Status, Task
from agentq.retry import RetryPolicy

Worker = Callable[[Task], str]
Validator = Callable[[Task], list[str]]


class TaskQueue:
    def __init__(
        self,
        retry: RetryPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
        validators: dict[str, list[Validator]] | None = None,
    ):
        self._pending: deque[Task] = deque()
        self._tasks: dict[str, Task] = {}
        self.retry = retry or RetryPolicy()
        self._sleep = sleep
        self._validators = validators or {}

    def submit(self, task: Task) -> None:
        if task.id in self._tasks:
            raise ValueError(f"duplicate task id {task.id!r}")
        self._tasks[task.id] = task
        self._pending.append(task)

    def get(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def _next(self) -> Task | None:
        return self._pending.pop() if self._pending else None

    def _requeue_or_fail(self, task: Task) -> None:
        if self.retry.should_retry(task.attempts):
            self._sleep(self.retry.delay(task.attempts))
            task.status = Status.PENDING
            self._pending.append(task)
        else:
            task.status = Status.FAILED

    def _validate(self, task: Task) -> list[str]:
        failures: list[str] = []
        for validator in self._validators.get(task.kind, []):
            failures.extend(validator(task))
        return failures

    def run_once(self, worker: Worker) -> Task | None:
        task = self._next()
        if task is None:
            return None
        task.status = Status.RUNNING
        task.attempts += 1
        try:
            task.output = worker(task)
        except Exception as exc:  # worker crashed
            task.errors.append(f"worker error: {exc}")
            self._requeue_or_fail(task)
            return task

        failures = self._validate(task)
        if failures:
            task.errors.extend(failures)
            self._requeue_or_fail(task)
            return task

        task.status = Status.DONE
        return task

    def run_all(self, worker: Worker) -> None:
        while self._pending:
            self.run_once(worker)
