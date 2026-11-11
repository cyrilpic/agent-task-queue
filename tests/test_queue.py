import pytest

from agentq import RetryPolicy, Status, Task, TaskQueue
from agentq.workers import echo_worker


def no_sleep(_s: float) -> None:
    pass


def test_task_runs_to_done():
    q = TaskQueue(sleep=no_sleep)
    q.submit(Task(id="t1", kind="python", spec="add two numbers"))
    q.run_all(echo_worker)
    t = q.get("t1")
    assert t.status is Status.DONE
    assert "add two numbers" in t.output


def test_duplicate_ids_rejected():
    q = TaskQueue(sleep=no_sleep)
    q.submit(Task(id="t1", kind="python", spec="x"))
    with pytest.raises(ValueError):
        q.submit(Task(id="t1", kind="python", spec="y"))


def test_crashing_worker_is_retried_then_failed():
    calls = []

    def crash(task):
        calls.append(task.attempts)
        raise RuntimeError("boom")

    q = TaskQueue(retry=RetryPolicy(max_attempts=2), sleep=no_sleep)
    q.submit(Task(id="t1", kind="python", spec="x"))
    q.run_all(crash)
    t = q.get("t1")
    assert t.status is Status.FAILED
    assert calls == [1, 2]
    assert len(t.errors) == 2
