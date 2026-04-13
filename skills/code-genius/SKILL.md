---
name: code-genius
description: "Implementation skill that executes plans step by step. Routes each step by type: code-required steps get TDD with pytest/mypy/ruff validation; harness-native steps are executed directly with the harness tools. Self-corrects up to 5 times per validation type."
argument-hint: "[documents-path]"
tools: Read, Write, Edit, Glob, Grep, Bash, Skill
model: opus
user-invocable: true
---

# Code Genius

## Config

- **MAX_RETRIES**: 5 per validation type
- `$ARGUMENTS[0]` = documents path (directory containing the plan); ask if missing
- Error tracking files (inside documents path): `PYTHON-ERROR-COUNT.md` and `FASTAPI-ERROR-COUNT.md` (format: `error-count: <number>`)

## INIT — Find Plan

Read or create `PYTHON-ERROR-COUNT.md` (default: `error-count: 0`) and `FASTAPI-ERROR-COUNT.md`.

Locate the implementation plan:

```
CODE-REVIEW.md exists? → use it (remediation mode)
else IMPLEMENTATION.md exists? → use it
else → tell user, suggest /planning-genius <docs-path>, EXIT
```

## STEP 1 — Read Plan and Classify

Read the selected plan document in full. Identify each step and its classification:
- **`(code-required)`** — needs TDD: write tests, write code, validate
- **`(harness-native)`** — execute directly with harness tools, verify, move on

If steps are not classified, read `specs/harness-native-operations.md` and apply the decision rule: can the harness do this with its native tools? If yes, treat as harness-native.

## STEP 2 — Execute Steps (in plan order)

For each step in the plan:

### If the step is `(code-required)`:

**2a. Write the test first** — before any production code:
- **Unit tests** → `tests/unit/test_<module>.py` — isolated, deps mocked with pytest fixtures/unittest.mock
- **Integration tests** → `tests/integration/test_<feature>.py` — real service coordination, DB ops
- **API tests** → `tests/api/test_<endpoint>.py` — FastAPI endpoints via `TestClient`

Tests must:
- Map directly to a requirement (acceptance criterion or task)
- Cover happy paths, edge cases, and failure modes
- Assert observable behavior (return values, API responses, raised exceptions, DB state) — not internal state or private methods
- Fail if the implementation were removed or broken

**2b. Implement to pass the tests** — minimum production code to make failing tests pass. No untested behavior.

**2c. Run step-level verification** — `pytest tests/ -v -k <test_pattern>` for the tests written in 2a. If failing, fix and retry before moving to the next step.

**2d. Mark complete and move on.**

### If the step is `(harness-native)`:

**2a. Execute the instructions directly** using harness tools:
- Create files → Write tool
- Edit files → Edit tool
- Delete files → Bash (`rm`)
- API calls → Bash (`curl`)
- Database queries → Bash (`sqlite3`, `psql`)
- Container operations → Bash (`docker`, `docker compose`)
- Data transformation → Bash (`jq`, `yq`, `python3 -c`)
- Any other CLI operation → Bash

**2b. Run the verification command** listed in the step (e.g. `grep`, `curl`, `ls`). If the verification fails, fix and retry.

**2c. Mark complete and move on.** No tests to write. No pytest to run.

Guidelines for all steps: follow PEP 8 and project conventions, use type hints, use context managers/comprehensions. Bug fixes require a regression test that fails without the fix.

## STEP 3 — Python Validation (code-required steps only)

Skip this step entirely if the plan had no code-required steps.

Check `pyproject.toml`/`setup.py`/`requirements.txt` to detect test framework.

```bash
# IMPORTANT: always use the project venv — /home/hivemind is noexec tmpfs
# bare python3/pytest will fail to load pydantic_core .so from user site-packages
/usr/src/app/venv/bin/python3 -m pytest -v
/usr/src/app/venv/bin/python3 -m mypy . --ignore-missing-imports
/usr/src/app/venv/bin/python3 -m ruff check . || pylint **/*.py
```

- All pass → STEP 4
- Failure:
  1. Read `PYTHON-ERROR-COUNT.md`, increment, write back
  2. If count >= 5 → STEP 7
  3. Else → categorize errors (type errors → fix hints; lint → fix style/imports; test failures → fix logic), fix, retry STEP 3

## STEP 4 — FastAPI Validation (skip if not FastAPI or no code-required steps)

Detect: `from fastapi import` in codebase, or `main.py`/`server.py` with a FastAPI app.

```bash
/usr/src/app/venv/bin/python3 -c "from server import app; print('FastAPI app loads')" 2>/dev/null || \
/usr/src/app/venv/bin/python3 -c "from app.main import app; print('FastAPI app loads')"
/usr/src/app/venv/bin/python3 -m pytest tests/api/ -v
```

- Pass → STEP 5
- Failure:
  1. Read `FASTAPI-ERROR-COUNT.md`, increment, write back
  2. If count >= 5 → STEP 7
  3. Else → fix (import paths, missing packages, route definitions, endpoint logic). Activate project venv if it exists. Install deps with `pip install -r requirements.txt` if missing. Retry STEP 4.

## STEP 5 — EXIT PASS

Report summary:
- Steps executed: N code-required, M harness-native
- Tests written: X
- Files created/modified: Y
- "Implementation complete. All validations passing."

## STEP 7 — EXIT FAIL

Report: "Validation failed after 5 attempts. <Python|FastAPI> build could not be fixed automatically. Errors are in <PYTHON|FASTAPI>-ERROR-COUNT.md."

## Rules

- **Classify before executing**: check each step's heading for `(code-required)` or `(harness-native)`. When unclassified, apply the harness-native decision rule.
- **Never write code for harness-native steps**: no Python files, no test files. Execute the operation with harness tools and verify.
- **Never skip tests for code-required steps**: Red → Green → Refactor. Always.
- **Unit**: pure functions, class methods, business logic — mock all external deps.
- **Integration**: DB queries, ORM, service coordination — use test DBs.
- **API**: HTTP endpoints, auth, error responses — use `TestClient`, not a real server.
- **Assert observable behavior only** — never internal variables or private methods.
- **Use `pytest.raises(SpecificException)`** for exception assertions.
- **Use `@pytest.mark.parametrize`** for boundary conditions.
- **Bug fixes require a regression test** that fails without the fix.
