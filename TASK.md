# Exercise: a validation checkpoint

Today a task is marked `DONE` as soon as the worker returns an output, even
when that output is wrong.

Add a validation checkpoint between the worker and `DONE`:

1. After a worker returns, run the validators registered for the task's kind.
2. If every validator passes, the task is `DONE`.
3. If any validator fails, the task goes back on the queue with the failure
   messages attached, so the next attempt can see them.
4. A task that keeps failing must not loop forever.
5. Callers can see why a task ended up `FAILED`.

Use your coding agent of choice. Talk through what you're doing as you go.
There's no single right design; we care about how you get there and how you
check the result.
