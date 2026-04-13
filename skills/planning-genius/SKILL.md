---
name: planning-genius
description: "Creates a precise implementation plan from a story description. Classifies each step as harness-native or code-required, then produces IMPLEMENTATION.md with the right approach for each. Use when you need a detailed implementation plan before coding."
argument-hint: [documents-path]
user-invocable: true
model: opus
---

# Planning Genius

`$ARGUMENTS[0]` = documents path; ask if missing.
Output: `<docs>/IMPLEMENTATION.md`. Planning only — no code changes.

## PHASE 1 — Read Story
Read `<docs>/STORY-DESCRIPTION.md`. Extract: title, number, acceptance criteria, tasks, constraints.
Missing → tell user to run `/get-story` first. EXIT.

## PHASE 1b — Read Project Standards (do not skip)
1. Read `specs/INDEX.md` to see all available specifications.
2. Always read these core standards:
   - `specs/security.md`
   - `specs/testing.md`
   - `specs/harness-native-operations.md`
3. Based on the story's scope, read any additional specs that are relevant (e.g. a story touching secrets → read `specs/secret-management.md`; a story adding tools → read `specs/tool-safety.md`).

All implementation steps must comply with loaded specs. Flag any conflict between the story requirements and these standards.

## PHASE 2 — Deep Codebase Exploration (do not skip)

**2a. Module context** — find affected module(s); read entry points (`server.py`, `mcp_server.py`), routing/endpoint definitions, and module structure (`core/`, `agents/`, `clients/`).

**2b. Analogous patterns** — find 2–3 existing features similar to the story. Read them in full. Note: module structure, class patterns, function signatures, error handling, config loading.

**2c. Shared infrastructure** — find shared services/utilities/models to reuse. Check existing API endpoints in `server.py`. Find shared helpers (`core/gateway_client.py`, `config.py`). Identify existing data models and Pydantic schemas.

**2d. Testing landscape** — read 1–2 representative test files of each type:
- Unit: `tests/unit/test_*.py` (isolated, deps mocked with pytest fixtures/unittest.mock)
- Integration: `tests/integration/test_*.py` (real service coordination, DB ops)
- API: `tests/api/test_*.py` (FastAPI endpoints via `TestClient`)
Note: framework (pytest), fixture patterns, mock patterns, naming conventions.

**2e. Dependencies** — if story needs new endpoints: identify existing vs needed routes, Pydantic models, request/response schemas. If story needs new MCP tools: check `agents/` for patterns.

**2f. Harness capability audit** — for each feature the story requires, ask: can the Claude Code harness accomplish this with its native tools (Bash, curl, Write, Edit, Grep, MCP tools, skills)? Identify which parts of the story are harness-native operations and which require runtime code. Refer to `specs/harness-native-operations.md` for the decision rule:
- **Harness-native:** file creation, deletion, config edits, API calls via curl, database queries via sqlite3/psql, data transformation via jq/yq, container management via docker, anything with a CLI equivalent.
- **Code-required:** continuous processes, in-memory state across requests, real-time event handling, specialized computation with no CLI equivalent.

## PHASE 3 — Design
Before writing the plan, resolve:
1. **Classify each step** — apply the harness-native decision rule. For each planned step, determine: can the harness do this? Mark it as `harness-native` or `code-required`.
2. For code-required steps: new files to create (path + purpose), existing files to modify (path + specific changes)
3. Data models/schemas needed (shapes based on existing patterns)
4. Dependency order (which pieces must exist before others)
5. For code-required steps: tests per step — unit for logic/services; integration for service coordination; API for endpoints
6. Every AC maps to at least one step (code or harness-native); every test maps to a requirement
7. Harness-native steps do not get tests — they are verified by the harness at execution time or implicitly by the runtime code that consumes their output

## PHASE 4 — Write IMPLEMENTATION.md

```markdown
# Implementation Plan: Story #<ID> - <Title>

## Overview
<2–3 sentences: what and why>

## Technical Approach
<Design decisions, which existing patterns are followed and why.
Note which steps are harness-native vs code-required and the reasoning.>

## Reference Patterns
| Pattern | Source File | Usage |

## Models & Schemas
<New Pydantic models or dataclasses with fields and types. Reference path.
Only for code-required steps.>

## Implementation Steps

### Step N: <description> (code-required)

**Files:**
- Create: `<path>` — <purpose>
- Modify: `<path>` — <what changes>

**Test First (unit):** `tests/unit/test_<module>.py`
- [ ] `<test>` — asserts <observable behavior>
- [ ] `<edge/failure test>` — asserts <behavior on bad input/error>

**Test First (integration):** `tests/integration/test_<feature>.py` *(if service coordination needed)*
- [ ] `<test>` — asserts <cross-module behavior>

**Test First (API):** `tests/api/test_<endpoint>.py` *(if endpoint needed)*
- [ ] `<test>` — asserts <HTTP response, status code, body>

**Then Implement:**
- [ ] <precise instruction referencing existing pattern file>
- [ ] <precise instruction>

**Verify:** `pytest tests/ -v -k <test_pattern>` — specific tests should pass.

---

### Step N: <description> (harness-native)

**Harness-native operation — no application code or tests needed.**

- [ ] <instruction — e.g. "Create `minds/ada/MIND.md` with frontmatter from config, body from soul file">
- [ ] <instruction — e.g. "Delete `souls/` directory">
- [ ] Verify: <verification command — e.g. "grep -r 'cli_harness' --include='*.py'" or "curl http://localhost:8420/broker/minds | jq">

---

## Integration Checklist
- [ ] Routes registered in `server.py` (if new endpoints)
- [ ] MCP tools decorated and discoverable (if new tools)
- [ ] Config additions in `config.py` / `config.yaml` (if config changes)
- [ ] Dependencies added to `requirements.txt` (if new packages)
- [ ] Secrets stored in keyring (not env/code)

## Build Verification
- [ ] `pytest -v` passes (if code-required steps exist)
- [ ] `mypy . --ignore-missing-imports` passes (if code-required steps exist)
- [ ] `ruff check .` passes (if code-required steps exist)
- [ ] All ACs addressed
```

## PHASE 5 — Update State & Exit
In `<docs>/STATE.md`: change `[state 2][ ]` → `[state 2][X]`.
Print: story title/number, step count (code-required / harness-native), new files count, modified files count, path to IMPLEMENTATION.md. EXIT PASS.

## Step Writing Rules
- **Classify first**: every step must be marked `(code-required)` or `(harness-native)` in its heading. Apply the decision rule from `specs/harness-native-operations.md`.
- **Harness-native steps**: describe what to do, not code to write. Instructions should reference harness tools (Write, Edit, Bash, curl, etc.). Include a verification command. No test files.
- **Code-required steps — TDD mandatory**: every step with runtime code needs test-first sub-step. Tests assert observable behavior only (return values, API responses, raised exceptions, DB state) — never internal state, private methods, or impl details.
- **Test file convention**: unit (`tests/unit/test_*.py`) for pure logic/service methods; integration (`tests/integration/test_*.py`) for cross-module coordination; API (`tests/api/test_*.py`) for FastAPI endpoints via TestClient.
- **Step order**: models/schemas → services/core logic → endpoints/tools → wiring/config → harness-native operations (file creation, cleanup, documentation). No forward references.
- **Precise**: name exact files, paths, fields, patterns to follow. Never vague ("create a service").
- **Reference existing code**: always name which file to use as a pattern.
- **Atomic steps**: one independently testable or verifiable concern per step.
