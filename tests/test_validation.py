from agentq import Status, Task, TaskQueue
from agentq.validation import ValidatorRegistry, not_empty, python_parses
from agentq.workers import flaky_python_worker


def no_sleep(_s: float) -> None:
    pass


def make_queue() -> TaskQueue:
    validators = ValidatorRegistry()
    validators.register("python", not_empty)
    validators.register("python", python_parses)
    return TaskQueue(sleep=no_sleep, validators=validators)


def test_bad_output_is_requeued_and_then_passes():
    q = make_queue()
    q.submit(Task(id="t1", kind="python", spec="add two numbers"))
    q.run_all(flaky_python_worker)
    t = q.get("t1")
    assert t.status is Status.DONE
    assert t.attempts == 2
    assert any("not valid Python" in e for e in t.errors)


def test_output_that_never_validates_ends_failed():
    q = make_queue()
    q.submit(Task(id="t1", kind="python", spec="x"))
    q.run_all(lambda task: "def broken(:\n")
    t = q.get("t1")
    assert t.status is Status.FAILED
    assert t.errors


def test_kinds_without_validators_are_unaffected():
    q = make_queue()
    q.submit(Task(id="t1", kind="docs", spec="x"))
    q.run_all(lambda task: "")
    assert q.get("t1").status is Status.DONE
