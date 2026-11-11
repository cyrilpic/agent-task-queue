"""Stub workers standing in for a coding agent."""

from agentq.models import Task


def echo_worker(task: Task) -> str:
    return f"# generated for: {task.spec}\n"


def flaky_python_worker(task: Task) -> str:
    """Returns broken Python on the first attempt, valid Python afterwards."""
    if task.attempts == 1:
        return "def add(a, b)\n    return a + b\n"
    return "def add(a, b):\n    return a + b\n"
