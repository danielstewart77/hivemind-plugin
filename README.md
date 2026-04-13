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

The `/setup` skill will walk you through deploying the server infrastructure.

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

Edit `.mcp.json` and replace the placeholders:

| Placeholder | Value |
|---|---|
| `${HIVE_MIND_DIR}` | Path to your cloned `hive_mind` repo |
| `${HIVE_MIND_VENV}` | Path to the Python virtualenv inside that repo |

Example:
```json
{
  "mcpServers": {
    "hive-mind-tools": {
      "command": "/home/you/dev/hive_mind/venv/bin/python",
      "args": ["/home/you/dev/hive_mind/mcp_server.py"]
    }
  }
}
```

---

## Skills

### Setup
| Skill | Description |
|---|---|
| `/hivemind:setup` | Master setup wizard |
| `/hivemind:setup-prerequisites` | Detect hardware, OS, and software prerequisites |
| `/hivemind:setup-config` | Generate configuration files |
| `/hivemind:setup-auth` | Set up Claude Code authentication |
| `/hivemind:setup-nervous-system` | Bootstrap and verify the nervous system |
| `/hivemind:setup-provider` | Configure AI providers |
| `/hivemind:setup-body` | Bootstrap communication surfaces |
| `/hivemind:setup-mind` | Set up minds |

### Mind Management
| Skill | Description |
|---|---|
| `/hivemind:add-mind` | Connect a mind to the system |
| `/hivemind:create-mind` | Create a new mind from a template |
| `/hivemind:update-mind` | Update a mind's configuration |
| `/hivemind:remove-mind` | Remove a mind from the system |
| `/hivemind:list-minds` | List all registered minds with status |
| `/hivemind:seed-mind` | Seed a mind's identity |

### Provider Management
| Skill | Description |
|---|---|
| `/hivemind:add-provider` | Add a new AI provider |
| `/hivemind:update-provider` | Update an existing provider |
| `/hivemind:remove-provider` | Remove a provider |

### Operations
| Skill | Description |
|---|---|
| `/hivemind:sitrep` | System situation report |
| `/hivemind:generate-compose` | Generate docker-compose from MIND.md files |
| `/hivemind:export-config` | Export current configuration |
| `/hivemind:update-hivemind` | Check for and apply Hive Mind updates |
| `/hivemind:agent-logs` | Scan system log files |

### Development
| Skill | Description |
|---|---|
| `/hivemind:planning-genius` | TDD implementation planning |
| `/hivemind:code-genius` | Python feature implementation |
| `/hivemind:code-review-genius` | Structured code review |
| `/hivemind:master-code-review` | Security-aware code review orchestrator |
| `/hivemind:tool-creator` | Create new Hive Mind tools |
| `/hivemind:skill-creator-claude` | Create new Claude Code skills |
| `/hivemind:create-agents-claude` | Create Claude Code subagents |
| `/hivemind:design-session` | Multi-turn design and planning session |
| `/hivemind:mermaid-diagram-creator` | Create and validate Mermaid diagrams |
| `/hivemind:update-documentation` | Update README and linked documentation |

### Workflow
| Skill | Description |
|---|---|
| `/hivemind:orchestrator` | Pipeline orchestrator |
| `/hivemind:story-start` | Kick off a development story |
| `/hivemind:story-close` | Close a completed story after PR merge |
| `/hivemind:create-story` | Create a Planka story card |

### Memory
| Skill | Description |
|---|---|
| `/hivemind:memory-manager` | Orchestrate the full memory storage lifecycle |
| `/hivemind:semantic-memory-save` | Write a chunk to the vector store |
| `/hivemind:knowledge-graph-save` | Write a chunk to the knowledge graph |
| `/hivemind:pin-memory-action` | Pin a memory chunk to MEMORY.md |
| `/hivemind:notify-action` | Handle a memory chunk with notification |
| `/hivemind:create-data-class` | Create a new data class spec |
| `/hivemind:self-reflect` | Ada's identity loading and reflection |

### Communication
| Skill | Description |
|---|---|
| `/hivemind:send-message-to-mind` | Send an async message to another mind |
| `/hivemind:moderate` | Moderate a group conversation |
| `/hivemind:send-email` | Send email via Gmail |
| `/hivemind:notify` | Send Telegram/email notifications |
| `/hivemind:sync-discord-slash-commands` | Sync skills to Discord slash commands |

### System
| Skill | Description |
|---|---|
| `/hivemind:secrets` | Manage secrets via keyring |
| `/hivemind:reminders` | Set and manage one-time reminders |
| `/hivemind:check-reminders` | Check and fire due reminders |
| `/hivemind:remind-me` | Read recurring reminder files |
| `/hivemind:planka` | Manage Planka Kanban board |

### Scheduling
| Skill | Description |
|---|---|
| `/hivemind:7am` | Morning briefing |
| `/hivemind:1pm` | Afternoon briefing |
| `/hivemind:3am` | Nightly autonomous session |

### External / Data
| Skill | Description |
|---|---|
| `/hivemind:weather` | Get weather for a location |
| `/hivemind:crypto-price` | Get cryptocurrency prices |
| `/hivemind:current-time` | Get current time for any timezone |
| `/hivemind:browse` | Browse the web interactively |
| `/hivemind:x-search` | Search X (Twitter) |
| `/hivemind:x-ai-lurker` | Fetch top AI threads on X |

### Meta
| Skill | Description |
|---|---|
| `/hivemind:convert-claude-skill-to-codex` | Convert a Claude skill to Codex format |
| `/hivemind:person-node-audit` | Audit Person nodes in the knowledge graph |

---

## Agents

| Agent | Description |
|---|---|
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

The plugin includes two lifecycle hooks:

- **SessionStart** — loads Ada's identity from the knowledge graph
- **Stop** — triggers a self-reflection cycle to capture identity updates

Hook scripts are expected at `~/.claude-config/hooks/`. These are installed as part of `/hivemind:setup-mind`.

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
