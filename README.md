# agent-task-queue

A tiny in-memory task queue for coding agents. A task carries a spec; a worker
(here a stub standing in for a coding agent) turns the spec into an output.

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

See `TASK.md` for today's exercise.
