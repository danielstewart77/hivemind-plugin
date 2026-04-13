---
name: code-review-genius
description: "Performs a structured code review against story requirements using 9 quality dimensions. Reads STORY-DESCRIPTION.md and IMPLEMENTATION.md, reviews all changed files, and produces CODE-REVIEW.md with findings and a remediation plan. Use when code is implemented and needs review before PR."
argument-hint: [documents-path]
user-invocable: true
model: opus
---

# Code Review Genius

`$ARGUMENTS[0]` = documents path; ask if missing. Output: `<docs>/CODE-REVIEW.md`. Read-only — no code changes.

## 9 Review Dimensions
1. Correctness — logic matches requirements, edge cases handled
2. Readability — clear structure, naming, intent
3. Simplicity — no over-engineering
4. Consistency — matches codebase patterns
5. Maintainability — easy to modify/test
6. TDD Test Coverage — behavior-first tests, req-mapped, fail if impl removed
7. Error Handling — failures anticipated and safe
8. Performance — no obvious regressions
9. Security — no common vulnerabilities (OWASP top 10, injection, credential leaks)

## Severity
- **Critical** — must fix before merge (bugs, security, missing required behavior)
- **Major** — should fix (quality/test coverage gaps)
- **Minor** — nice to fix
- **Nit** — optional polish

## Workflow

**STEP 1 — Load Context**
1. Read `<docs>/STORY-DESCRIPTION.md` → extract acceptance criteria and tasks
2. Read `<docs>/IMPLEMENTATION.md` → extract technical approach and patterns
3. If either missing → EXIT

**STEP 2 — Identify Changed Files**
Run `git diff --name-only` against base branch. Group by: Core modules, Agents/Tools, Clients, Tests, Config, Other. Cross-reference with impl plan.

**STEP 3 — Deep Review**
For each file: read in full + read its corresponding test file(s) in `tests/`. Evaluate all 9 dimensions. Record findings with file path, line number, dimension, severity, description.
- TDD check: test file exists? Tests cover AC behaviors (not just "imports work")? Edge/failure cases covered? Tests would fail if impl removed? Right level (unit vs integration vs API)?
- Consistency check: read sibling files to verify naming, imports, patterns (`@tool` decorators, Pydantic models, error handling style).
- Security check: no hardcoded secrets, no `shell=True`, no `eval`/`exec`, input validation at boundaries, safe error messages (no stack traces to users).

**STEP 4 — AC Coverage**
Map each acceptance criterion → which file(s)/test(s) cover it. Flag: Not Implemented / Implemented but Untested / Partially Implemented.

**STEP 5 — Write CODE-REVIEW.md**
```markdown
# Code Review: Story #<N> - <title>

## Summary
<1-2 sentence assessment.>
**Verdict:** APPROVED | APPROVED WITH MINOR FIXES | CHANGES REQUESTED

## Acceptance Criteria Coverage
| # | Criterion | Status | Covered By |
|---|-----------|--------|------------|

## Files Reviewed
| File | Status | Findings |
|------|--------|----------|

## Findings
### Critical
#### C1: <title>
- **File:** `path:line`
- **Dimension:** <name>
- **Description:** <what/why>
- **Suggested Fix:** <how>
### Major
### Minor
### Nits

## Remediation Plan
### Step 1: <title>
- **File:** `path`
- **Action:** <specific change>
```

**STEP 6 — Exit**
Print: story title/number, verdict, finding counts (critical/major/minor/nit). EXIT.
