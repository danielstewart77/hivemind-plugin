---
name: create-story
description: "Create a Planka story card with proper structure. Use when {{USER}} wants to create a new story/task on the board."
argument-hint: "[title]"
user-invocable: true
tools: Read, Write
---

# Create Story

## Board Reference

- **Project**: Hive Mind (`{{PLANKA_PROJECT_ID}}`)
- **Board**: Development (`{{PLANKA_BOARD_ID}}`)

### List IDs

| Column | ID |
|--------|----|
| Backlog | `{{PLANKA_BACKLOG_LIST_ID}}` |
| In Progress | `{{PLANKA_IN_PROGRESS_LIST_ID}}` |
| Done | `{{PLANKA_DONE_LIST_ID}}` |

### Label IDs

| Label | ID |
|-------|----|
| Ada | `{{PLANKA_ADA_LABEL_ID}}` |
| owner | `{{PLANKA_OWNER_LABEL_ID}}` |
| Low priority | `{{PLANKA_LOW_PRIORITY_LABEL_ID}}` |

## Procedure

1. **Get title.** Use `$ARGUMENTS` if provided, otherwise ask.

2. **Determine column.** Default: Backlog. Ask if it should go directly to In Progress.

3. **Determine label.** Ask: Ada, {{USER}}, or Low priority? Default: Ada for autonomous work, {{USER}} for things requiring host access or human decisions.

4. **Develop user acceptance criteria.** Before writing the spec, ask {{USER}} for a use scenario — a concrete example of how he'd use the feature end-to-end. Collaborate to turn that into a full set of acceptance criteria:
   - Walk through the scenario step by step
   - Identify edge cases and decision points (what happens when X?)
   - Ask clarifying questions until the criteria are specific and testable
   - The final acceptance criteria should read like a checklist someone could run through to verify the feature works

5. **Write or verify the spec.** Every story must have a spec file at `specs/<name>.md` before the card is created. The spec must include:
   - **User requirements** — what the user wants to accomplish, described from their perspective
   - **User acceptance criteria** — the full checklist developed in Step 4
   - **Technical specification** — how it works: architecture, tool functions, data flow
   - **Code references** — files that will be created or modified, with paths
   - **File locations** — where new code will live (e.g. `agents/browser.py`, `.claude/skills/browse/SKILL.md`)
   - **Implementation order** — numbered steps

   If the spec already exists, verify it covers all the above. If not, fill in the gaps.

6. **Write card description.** Include:
   - Overview (1-2 sentences)
   - Reference the spec: `Full spec: \`specs/<filename>.md\``
   - Components or scope (bulleted)
   - Key user acceptance criteria (summarized)

7. **Create card.** Call `planka_create_card` with list_id, name, description.

8. **Assign label.** Call `planka_assign_label` with card_id and label_id.

9. **Confirm.** Report the card title, column, and label assignment.

## Naming Convention

Use bracketed prefixes: `[Feature]`, `[Bug]`, `[DevOps]`, `[Security]`, `[Memory]`, `[Pipeline]`, `[Integration]`, `[UX]`, `[Roadmap]`.
