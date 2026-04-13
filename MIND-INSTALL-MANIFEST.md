# Mind Install Manifest

This file is the authoritative reference for what gets distributed to each mind during setup.
It covers **skills**, **agents**, and **hooks** — everything in this plugin.

Referenced by: `setup-mind`, `setup-body`, `setup`. Not discovered by the Claude skill loader.

---

## Install Tiers

| Tier | Meaning |
|---|---|
| **core** | Installed automatically for every mind. Not presented during setup. |
| **a-la-carte** | Presented to the user during mind setup for optional selection. |
| **setup-only** | Used by the setup flow itself. Never installed per-mind. |

---

## Skills

### Core — Identity _(core, every mind)_

The memory and identity pipeline. Installed silently.

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

### Core — Utilities _(core, every mind)_

Foundational operational skills. Installed silently.

| Skill | Description |
|---|---|
| `current-time` | Timezone-aware clock |
| `secrets` | Keyring secret management |
| `notify` | Send notifications via Telegram, email, or file |
| `reminders` | Set, list, delete, and check one-time reminders |
| `check-reminders` | Check and fire due reminders (scheduler-triggered) |

### Development _(a-la-carte)_

For minds involved in software development workflows.

| Skill | Description |
|---|---|
| `code-genius` | Python coding with TDD, pytest, mypy, ruff, self-correction |
| `planning-genius` | TDD implementation plan from a story description |
| `master-code-review` | Security-aware code review orchestrator |
| `code-review-genius` | Structured code review against 9 quality dimensions |
| `story-start` | Kicks off a development story from a Planka card |
| `story-close` | Closes a story after PR merge, health check, card move |
| `create-story` | Create a Planka story card with proper structure |
| `orchestrator` | Pipeline orchestrator — works Planka cards end-to-end |
| `commit` | Git commit with conventional commit message |
| `design-session` | Multi-turn design and planning session |

### Research _(a-la-carte)_

For minds that browse the web or monitor external sources.

| Skill | Description |
|---|---|
| `browse` | Interactive web browsing via Playwright |
| `x-search` | Search X (Twitter) for tweets and thread replies |
| `x-ai-lurker` | Fetches top AI threads on X for a daily news report |
| `crypto-price` | CoinGecko cryptocurrency prices |
| `weather` | Open-Meteo weather by location |

### Productivity _(a-la-carte)_

For minds that manage tasks, boards, and inter-mind communication.

| Skill | Description |
|---|---|
| `planka` | Manage Planka Kanban board cards and projects |
| `remind-me` | Reads daily, weekly, and backlog reminder files |
| `send-message-to-mind` | Send an async message to another mind via the broker |
| `moderate` | Moderate a group conversation |

### Publishing _(a-la-carte)_

For minds that produce content or communicate externally.

| Skill | Description |
|---|---|
| `send-email` | Send email via Gmail with HITL approval |
| `post-to-linkedin` | Post to LinkedIn |
| `convert-to-pdf` | Convert documents to PDF |
| `mermaid-diagram-creator` | Create and validate Mermaid diagrams |
| `pdf-formatter` | Format and style PDF output |

### System / Ops _(a-la-carte)_

For minds that monitor and maintain the Hive Mind system.

| Skill | Description |
|---|---|
| `sitrep` | Military-style system situation report |
| `agent-logs` | Scan system log files for critical entries |
| `update-hivemind` | Check for and apply Hive Mind updates from origin/master |
| `update-documentation` | Sync README and docs to current codebase state |
| `sync-discord-slash-commands` | Sync user-invocable skills to Discord as slash commands |
| `remote-admin` | Manage SSH sessions on remote hosts via the remote-admin bridge service |

### Advanced _(a-la-carte)_

Power-user skills for extending the system itself.

| Skill | Description |
|---|---|
| `skill-creator-claude` | Guide for creating new Claude Code skills correctly |
| `tool-creator` | Create new Hive Mind stateless or stateful tools |
| `create-agents-claude` | Guide for creating Claude Code subagents correctly |
| `prune-config-memory` | Audit technical-config memories against the live codebase |
| `person-node-audit` | Audit and repair Person nodes in the knowledge graph |
| `create-data-class` | Create a new data class spec and register it in the index |

### Setup Only _(setup-only, never per-mind)_

Used by the setup flow. Never presented as mind options.

`setup`, `setup-prerequisites`, `setup-config`, `setup-auth`, `setup-nervous-system`,
`setup-provider`, `setup-body`, `setup-mind`, `setup-resolve-placeholders`,
`setup-personality`, `setup-remote`, `create-mind`, `add-mind`, `remove-mind`,
`update-mind`, `add-provider`, `remove-provider`, `update-provider`,
`generate-compose`, `seed-mind`

---

## Agents

### Core _(core, every mind)_

Installed silently alongside Core skills. These back the memory pipeline and identity reflection.

| Agent | Installed with | Description |
|---|---|---|
| `reflect` | Core — Identity | Background identity reflection — evaluates 5 criteria, writes to graph |
| `parse-memory` | Core — Identity | Parses input into a chunk manifest |
| `classify-memory` | Core — Identity | Classifies chunks against the data class index |
| `route-memory` | Core — Identity | Reads classified manifest, writes routing manifest |
| `save-memory` | Core — Identity | Executes memory writes from the routing manifest |

### Development _(a-la-carte, with Development skill group)_

| Agent | Description |
|---|---|
| `step-get-story` | Pull a story from Planka and set up documents |
| `step-planning` | Create a TDD implementation plan |
| `step-coding` | Implement code from plan using TDD |
| `step-review` | Structured code review against story requirements |
| `step-push-pr` | Push branch and create GitHub pull request |

### Productivity _(a-la-carte, with Productivity skill group)_

| Agent | Description |
|---|---|
| `poll-task-result` | Poll broker for inter-mind task results |

---

## Hooks

### Core _(core, every mind)_

Both hooks are installed silently for every mind during `setup-mind`. They are configured in the mind's Claude Code settings.

| Hook | Trigger | Script | Description |
|---|---|---|---|
| `soul_load` | SessionStart | `~/.claude-config/hooks/soul_load.sh` | Loads the mind's identity from the knowledge graph at session start |
| `soul_nudge` | Stop (every 5 turns) | `~/.claude-config/hooks/soul_nudge.sh` | Dispatches the `reflect` agent in the background to capture identity updates |

Hook scripts are installed to `~/.claude-config/hooks/` on the mind's host. They invoke `/self-reflect --load` and `/self-reflect --reflect` respectively.

---

## Summary by Install Tier

### Every mind gets (silently)

**Skills:** self-reflect, memory-manager, parse-memory, classify-memory, route-memory, save-memory, semantic-memory-save, knowledge-graph-save, pin-memory-action, notify-action, current-time, secrets, notify, reminders, check-reminders

**Agents:** reflect, parse-memory, classify-memory, route-memory, save-memory

**Hooks:** soul_load (SessionStart), soul_nudge (Stop/every 5 turns)

### Optional (a-la-carte by group)

Development, Research, Productivity, Publishing, System/Ops, Advanced — see group tables above for full lists.
