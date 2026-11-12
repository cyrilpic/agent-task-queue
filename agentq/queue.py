from collections import deque
from typing import Callable

import time

from agentq.models import Status, Task
from agentq.retry import RetryPolicy
from agentq.validation import ValidatorRegistry

Worker = Callable[[Task], str]


class TaskQueue:
    def __init__(
        self,
        retry: RetryPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
        validators: ValidatorRegistry | None = None,
        max_validation_retries: int = 3,
    ):
        self._pending: deque[Task] = deque()
        self._tasks: dict[str, Task] = {}
        self.retry = retry or RetryPolicy()
        self._sleep = sleep
        self.validators = validators or ValidatorRegistry()
        self.max_validation_retries = max_validation_retries

    def submit(self, task: Task) -> None:
        if task.id in self._tasks:
            raise ValueError(f"duplicate task id {task.id!r}")
        self._tasks[task.id] = task
        self._pending.append(task)

    def get(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def _next(self) -> Task | None:
        return self._pending.pop() if self._pending else None

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
            if self.retry.should_retry(task.attempts):
                self._sleep(self.retry.delay(task.attempts))
                task.status = Status.PENDING
                self._pending.append(task)
            else:
                task.status = Status.FAILED
            return task
        failures = self.validators.run(task)
        if failures:
            task.validation_attempts += 1
            task.errors.extend(failures)
            if task.validation_attempts <= self.max_validation_retries:
                task.status = Status.PENDING
                self._pending.append(task)
            else:
                task.status = Status.FAILED
            return task
        task.status = Status.DONE
        return task

    def run_all(self, worker: Worker) -> None:
        while self._pending:
            self.run_once(worker)
