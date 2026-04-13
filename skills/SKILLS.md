# Hive Mind Skills Manifest

This file is the authoritative index of all plugin skills, their groupings, and install behavior.
It is referenced by setup skills — not discovered by the Claude skill loader.

---

## Install Behavior

| Behavior | Meaning |
|---|---|
| **silent** | Installed automatically for every mind. Not presented during setup. |
| **a-la-carte** | Presented to the user during mind setup for optional selection. |
| **setup-only** | Used by the setup flow itself. Never installed per-mind. |

---

## Core — Identity

Installed silently for every mind. These skills form the memory and identity pipeline.

| Skill | Description |
|---|---|
| `self-reflect` | Identity loading (--load) and async reflection dispatch (--reflect) |
| `memory-manager` | Orchestrates the full memory storage lifecycle |
| `parse-memory` | Parses input into a chunk manifest for memory storage |
| `classify-memory` | Classifies each chunk against the data class index |
| `route-memory` | Routes classified chunks to their prescribed storage action |
| `save-memory` | Executes memory writes from the routing manifest |
| `semantic-memory-save` | Writes a chunk to the Neo4j vector store |
| `knowledge-graph-save` | Writes a chunk to the knowledge graph |
| `pin-memory-action` | Writes a chunk to MEMORY.md |
| `notify-action` | Handles memory chunks with a future notification action |

**Agents installed with this group:** `reflect`, `parse-memory`, `classify-memory`, `route-memory`, `save-memory`

---

## Core — Utilities

Installed silently for every mind. Foundational operational skills.

| Skill | Description |
|---|---|
| `current-time` | Timezone-aware clock |
| `secrets` | Keyring secret management |
| `notify` | Send notifications via Telegram, email, or file |
| `reminders` | Set, list, delete, and check one-time reminders |
| `check-reminders` | Check and fire due reminders (scheduler-triggered) |

---

## Development

A la carte. For minds involved in software development workflows.

| Skill | Description |
|---|---|
| `code-genius` | Python coding with TDD, pytest, mypy, ruff, self-correction |
| `planning-genius` | TDD implementation plan from a story description |
| `master-code-review` | Security-aware code review orchestrator |
| `code-review-genius` | Structured code review against 9 quality dimensions |
| `story-start` | Kicks off a development story from a Planka card |
| `story-close` | Closes a story after PR merge, health check, card move |
| `create-story` | Create a Planka story card with proper structure |
| `orchestrator` | Pipeline orchestrator — works Ada-labelled Planka cards end-to-end |
| `commit` | Git commit with conventional commit message |
| `design-session` | Multi-turn design and planning session |

---

## Research

A la carte. For minds that browse the web or monitor external sources.

| Skill | Description |
|---|---|
| `browse` | Interactive web browsing via Playwright |
| `x-search` | Search X (Twitter) for tweets and thread replies |
| `x-ai-lurker` | Fetches top AI threads on X for a daily news report |
| `crypto-price` | CoinGecko cryptocurrency prices |
| `weather` | Open-Meteo weather by location |

---

## Productivity

A la carte. For minds that manage tasks, boards, and inter-mind communication.

| Skill | Description |
|---|---|
| `planka` | Manage Planka Kanban board cards and projects |
| `remind-me` | Reads daily, weekly, and backlog reminder files |
| `send-message-to-mind` | Send an async message to another mind via the broker |
| `moderate` | Moderate a group conversation by routing messages to appropriate minds |

---

## Publishing

A la carte. For minds that produce content or communicate externally.

| Skill | Description |
|---|---|
| `send-email` | Send email via Gmail with HITL approval |
| `post-to-linkedin` | Post to LinkedIn |
| `convert-to-pdf` | Convert documents to PDF |
| `mermaid-diagram-creator` | Create and validate Mermaid diagrams |
| `pdf-formatter` | Format and style PDF output |

---

## System / Ops

A la carte. For minds that monitor and maintain the Hive Mind system.

| Skill | Description |
|---|---|
| `sitrep` | Military-style system situation report |
| `agent-logs` | Scan system log files for critical entries |
| `update-hivemind` | Check for and apply Hive Mind updates from origin/master |
| `update-documentation` | Sync README and docs to current codebase state |
| `sync-discord-slash-commands` | Sync user-invocable skills to Discord as slash commands |

---

## Advanced

A la carte. Power-user skills for extending the system itself.

| Skill | Description |
|---|---|
| `skill-creator-claude` | Guide for creating new Claude Code skills correctly |
| `tool-creator` | Create new Hive Mind stateless or stateful tools |
| `create-agents-claude` | Guide for creating Claude Code subagents correctly |
| `prune-config-memory` | Audit technical-config memories against the live codebase |
| `person-node-audit` | Audit and repair Person nodes in the knowledge graph |
| `create-data-class` | Create a new data class spec and register it in the index |

---

## Setup Only

Used by the setup flow. Never presented as per-mind skill options.

`setup`, `setup-prerequisites`, `setup-config`, `setup-auth`, `setup-nervous-system`,
`setup-provider`, `setup-body`, `setup-mind`, `setup-resolve-placeholders`,
`setup-personality`, `setup-remote`, `create-mind`, `add-mind`, `remove-mind`,
`update-mind`, `add-provider`, `remove-provider`, `update-provider`,
`generate-compose`, `seed-mind`
