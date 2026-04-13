# Hive Mind — Claude Code Plugin

A Claude Code plugin that installs all Hive Mind skills, agents, and hooks. Install this plugin to get the full suite of multi-mind orchestration, setup, memory, and operational tools as native `/hivemind:<skill>` commands.

> The plugin distributes skills and agents. The Hive Mind server (gateway, broker, MCP tools) lives in a separate repo and is deployed during `/setup`.

---

## Installation

```bash
claude /plugin marketplace add danielstewart77/hivemind-plugin
```

Then run setup:

```bash
/hivemind:setup all
```

The `/setup` skill walks you through deploying the server infrastructure, configuring providers, setting up minds, and selecting optional skill groups.

---

## Prerequisites

- [Claude Code](https://claude.ai/code) installed
- Docker and Docker Compose (for server deployment)
- Git

---

## MCP Configuration

After setup, configure your MCP connection by copying the template:

```bash
cp mcp.json.template .mcp.json
```

Edit `.mcp.json` and replace the placeholders with paths to your cloned `hive_mind` repo and Python virtualenv.

---

## Skill Groups

Skills are organized into install groups. **Core skills are installed automatically** for every mind. Optional groups are selected during `/setup-mind`.

See [`skills/SKILL-CATALOG.md`](skills/SKILL-CATALOG.md) for the full catalog with install behavior, group definitions, and per-skill descriptions.

| Group | Install | Purpose |
|---|---|---|
| Core — Identity | Silent | Memory pipeline, identity reflection |
| Core — Utilities | Silent | Clock, secrets, notifications, reminders |
| Development | A la carte | Coding, planning, review, story management |
| Research | A la carte | Web browsing, X/Twitter, crypto, weather |
| Productivity | A la carte | Planka, inter-mind messaging, moderation |
| Publishing | A la carte | Email, LinkedIn, PDF, diagrams |
| System / Ops | A la carte | SITREP, logs, updates, Discord sync |
| Advanced | A la carte | Skill/tool creation, memory auditing |

---

## Skills

### Setup
| Skill | Description |
|---|---|
| `/hivemind:setup` | Master setup wizard — run this first |
| `/hivemind:setup-prerequisites` | Detect hardware, OS, and software prerequisites |
| `/hivemind:setup-config` | Generate configuration files |
| `/hivemind:setup-auth` | Set up Claude Code authentication |
| `/hivemind:setup-nervous-system` | Bootstrap and verify the nervous system |
| `/hivemind:setup-provider` | Configure AI providers |
| `/hivemind:setup-body` | Bootstrap communication surfaces and integrations |
| `/hivemind:setup-mind` | Set up minds with topology and skill selection |
| `/hivemind:setup-personality` | Define a mind's identity and seed it into the graph |
| `/hivemind:setup-resolve-placeholders` | Substitute `{{USER}}` and `{{PLANKA_*}}` across skill files |
| `/hivemind:setup-remote` | Install Hive Mind on a remote host via SSH |

### Mind Management
| Skill | Description |
|---|---|
| `/hivemind:create-mind` | Create a new mind from a template |
| `/hivemind:add-mind` | Connect an existing mind to the system |
| `/hivemind:update-mind` | Update a mind's configuration |
| `/hivemind:remove-mind` | Remove a mind from the system |
| `/hivemind:list-minds` | List all registered minds with status |
| `/hivemind:seed-mind` | Seed a mind's identity from its soul file |
| `/hivemind:generate-compose` | Generate docker-compose from MIND.md files |

### Provider Management
| Skill | Description |
|---|---|
| `/hivemind:add-provider` | Add a new AI provider |
| `/hivemind:update-provider` | Update an existing provider |
| `/hivemind:remove-provider` | Remove a provider |

### Memory — Core (auto-installed)
| Skill | Description |
|---|---|
| `/hivemind:memory-manager` | Orchestrate the full memory storage lifecycle |
| `/hivemind:semantic-memory-save` | Write a chunk to the Neo4j vector store |
| `/hivemind:knowledge-graph-save` | Write a chunk to the knowledge graph |
| `/hivemind:pin-memory-action` | Pin a memory chunk to MEMORY.md |
| `/hivemind:notify-action` | Handle a memory chunk with a future notification |
| `/hivemind:self-reflect` | Identity loading (--load) and async reflection dispatch (--reflect) |
| `/hivemind:create-data-class` | Create a new data class spec and register it |
| `/hivemind:prune-config-memory` | Audit technical-config memories against live codebase |

### Development
| Skill | Description |
|---|---|
| `/hivemind:planning-genius` | TDD implementation plan from a story description |
| `/hivemind:code-genius` | Python feature implementation with TDD and self-correction |
| `/hivemind:code-review-genius` | Structured code review against 9 quality dimensions |
| `/hivemind:master-code-review` | Security-aware code review orchestrator |
| `/hivemind:design-session` | Multi-turn design and planning session |
| `/hivemind:mermaid-diagram-creator` | Create and validate Mermaid diagrams |
| `/hivemind:orchestrator` | Pipeline orchestrator — works Planka cards end-to-end |
| `/hivemind:story-start` | Kick off a development story from a Planka card |
| `/hivemind:story-close` | Close a completed story after PR merge |
| `/hivemind:create-story` | Create a Planka story card with proper structure |
| `/hivemind:tool-creator` | Create new Hive Mind stateless or stateful tools |
| `/hivemind:skill-creator-claude` | Guide for creating Claude Code skills correctly |
| `/hivemind:create-agents-claude` | Guide for creating Claude Code subagents correctly |
| `/hivemind:update-documentation` | Sync README and docs to current codebase state |

### Communication & Publishing
| Skill | Description |
|---|---|
| `/hivemind:send-message-to-mind` | Send an async message to another mind via the broker |
| `/hivemind:moderate` | Moderate a group conversation |
| `/hivemind:send-email` | Send email via Gmail with HITL approval |
| `/hivemind:notify` | Send Telegram/email/file notifications |
| `/hivemind:post-to-linkedin` | Post to LinkedIn |
| `/hivemind:convert-to-pdf` | Convert documents to PDF |
| `/hivemind:pdf-formatter` | Format and style PDF output |
| `/hivemind:sync-discord-slash-commands` | Sync user-invocable skills to Discord slash commands |

### Research & External
| Skill | Description |
|---|---|
| `/hivemind:browse` | Interactive web browsing via Playwright |
| `/hivemind:x-search` | Search X (Twitter) for tweets and thread replies |
| `/hivemind:x-ai-lurker` | Fetch top AI threads on X for a daily news report |
| `/hivemind:crypto-price` | CoinGecko cryptocurrency prices |
| `/hivemind:weather` | Open-Meteo weather by location |

### Productivity & System
| Skill | Description |
|---|---|
| `/hivemind:planka` | Manage Planka Kanban board cards and projects |
| `/hivemind:reminders` | Set, list, and delete one-time reminders |
| `/hivemind:check-reminders` | Check and fire due reminders (scheduler-triggered) |
| `/hivemind:remind-me` | Read daily, weekly, and backlog reminder files |
| `/hivemind:secrets` | Manage secrets via the system keyring |
| `/hivemind:current-time` | Timezone-aware clock |
| `/hivemind:sitrep` | Military-style system situation report |
| `/hivemind:agent-logs` | Scan system log files for critical entries |
| `/hivemind:update-hivemind` | Check for and apply Hive Mind updates from origin/master |
| `/hivemind:person-node-audit` | Audit and repair Person nodes in the knowledge graph |

### Scheduling
| Skill | Description |
|---|---|
| `/hivemind:7am` | Morning briefing |
| `/hivemind:1pm` | Afternoon briefing |
| `/hivemind:3am` | Nightly autonomous session |

### Meta
| Skill | Description |
|---|---|
| `/hivemind:convert-claude-skill-to-codex` | Convert a Claude skill to Codex format |

---

## Agents

| Agent | Description |
|---|---|
| `reflect` | Background identity reflection — evaluates 5 criteria, writes to graph |
| `poll-task-result` | Poll broker for inter-mind task results |
| `step-get-story` | Pull a story from Planka and set up documents |
| `step-planning` | Create a TDD implementation plan |
| `step-coding` | Implement code from plan using TDD |
| `step-review` | Structured code review against story requirements |
| `step-push-pr` | Push branch and create GitHub pull request |
| `parse-memory` | Parse input into a chunk manifest |
| `classify-memory` | Classify chunks against the data class index |
| `route-memory` | Read classified manifest and write routing manifest |
| `save-memory` | Execute memory writes from the routing manifest |

---

## Hooks

The plugin includes two lifecycle hooks configured during `/setup-mind`:

- **SessionStart** — loads the mind's identity from the knowledge graph
- **Stop** — dispatches an async background reflection cycle to capture identity updates

Hook scripts are installed at `~/.claude-config/hooks/` and apply to the mind that runs them. Each mind manages its own identity independently.

---

## Server Repo

The Hive Mind server (FastAPI gateway, MCP tools, broker, mind containers) is in a separate repository:

```
https://github.com/danielstewart77/hive_mind
```

The `/hivemind:setup` skill clones and deploys it automatically.

---

## License

MIT
