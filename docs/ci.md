# CI and merge blocking

Workflow: `.github/workflows/ci.yml`

Jobs (run on every push, and on pull requests into `main` / `master`):

| Check name | What it runs |
|------------|--------------|
| `lint` | `ruff check` and `ruff format --check` |
| `test` | full `pytest` suite |
| `task-constraints` | `pytest -m task_constraints` (TASK.md acceptance) |

## Making failed tests block merge

GitHub Actions only reports check status. To make a red `test` (or any other
job) mark a PR **not mergeable**, configure a branch ruleset or classic branch
protection on `main` and `master`:

1. Require a pull request before merging.
2. Require these status checks to pass (exact job names):
   - `lint`
   - `test`
   - `task-constraints`
3. Prefer “Require branches to be up to date before merging.”
4. Avoid bypass allowances for the default role if merge blocking must be real.

With the validation checkpoint in place, all three jobs are expected to pass
on a clean tree.
