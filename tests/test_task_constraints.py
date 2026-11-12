"""Acceptance tests for the validation checkpoint described in TASK.md."""

from __future__ import annotations

import pytest

from agentq import RetryPolicy, Status, Task, TaskQueue

pytestmark = pytest.mark.task_constraints


def no_sleep(_s: float) -> None:
    pass


def always_pass(_task: Task) -> list[str]:
    return []


def always_fail(_task: Task) -> list[str]:
    return ["validation failed: intentional"]


def kind_mismatch_guard(task: Task) -> list[str]:
    """Would only be registered for a specific kind; used to prove kind routing."""
    return [f"unexpected kind {task.kind!r}"]


def test_validators_for_kind_run_after_worker_returns():
    """TASK.md #1: after a worker returns, run validators registered for the kind."""
    calls: list[str] = []

    def tracking_validator(task: Task) -> list[str]:
        calls.append(task.kind)
        return []

    def worker(task: Task) -> str:
        return f"output for {task.spec}"

    q = TaskQueue(
        sleep=no_sleep,
        validators={"python": [tracking_validator], "docs": [kind_mismatch_guard]},
    )
    q.submit(Task(id="t1", kind="python", spec="x"))
    q.run_once(worker)

    assert calls == ["python"]


def test_all_validators_pass_marks_done():
    """TASK.md #2: if every validator passes, the task is DONE."""

    def worker(task: Task) -> str:
        return "ok"

    q = TaskQueue(sleep=no_sleep, validators={"python": [always_pass]})
    q.submit(Task(id="t1", kind="python", spec="x"))
    q.run_once(worker)
    t = q.get("t1")

    assert t.status is Status.DONE
    assert t.output == "ok"
    assert t.errors == []


def test_validator_failure_requeues_with_messages():
    """TASK.md #3: on validator failure, requeue with failure messages attached."""

    def worker(task: Task) -> str:
        return "candidate output"

    q = TaskQueue(
        retry=RetryPolicy(max_attempts=3),
        sleep=no_sleep,
        validators={"python": [always_fail]},
    )
    q.submit(Task(id="t1", kind="python", spec="x"))
    q.run_once(worker)
    t = q.get("t1")

    assert t.status is Status.PENDING
    assert "validation failed: intentional" in t.errors

    # Requeued: a second run_once must pick the same task up again.
    q.run_once(worker)
    assert t.attempts == 2


def test_persistent_validation_failure_does_not_loop_forever():
    """TASK.md #4: a task that keeps failing must not loop forever."""

    def worker(task: Task) -> str:
        return "still wrong"

    q = TaskQueue(
        retry=RetryPolicy(max_attempts=2),
        sleep=no_sleep,
        validators={"python": [always_fail]},
    )
    q.submit(Task(id="t1", kind="python", spec="x"))
    q.run_all(worker)
    t = q.get("t1")

    assert t.status is Status.FAILED
    assert t.attempts == 2
    # Queue drained: another run_once finds nothing left to run.
    assert q.run_once(worker) is None


def test_failed_task_exposes_validation_errors_to_callers():
    """TASK.md #5: callers can see why a task ended up FAILED."""

    def worker(task: Task) -> str:
        return "bad"

    q = TaskQueue(
        retry=RetryPolicy(max_attempts=1),
        sleep=no_sleep,
        validators={"python": [always_fail]},
    )
    q.submit(Task(id="t1", kind="python", spec="x"))
    q.run_all(worker)
    t = q.get("t1")

    assert t.status is Status.FAILED
    assert any("validation failed" in err for err in t.errors)
