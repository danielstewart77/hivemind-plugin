# Hive Mind Plugin — Claude Code Internal Reference

This plugin distributes Hive Mind skills, agents, and lifecycle hooks. Skills are namespaced as `/hivemind:<skill-name>`.

## Skills

77 skills across 8 groups — see README.md for the full table. Key groups:

- **Setup** — `/hivemind:setup` master wizard, prerequisite detection, config generation, mind provisioning
- **Memory** — full pipeline: parse → classify → route → save → reflect. Core to Ada's identity system.
- **Development** — TDD planning, coding, code review, story management via Planka
- **Communication** — email (HITL-gated), Telegram notifications, LinkedIn, Discord sync
- **System/Ops** — SITREP, log scanning, remote-admin SSH bridge, update management

## Agents

11 agent definitions in `agents/`. These are subagent specs launched via the Agent tool:

- **Memory pipeline**: `parse-memory`, `classify-memory`, `route-memory`, `save-memory`
- **Identity**: `reflect` — background reflection, writes to knowledge graph
- **Dev pipeline**: `step-get-story`, `step-planning`, `step-coding`, `step-review`, `step-push-pr`
- **Async**: `poll-task-result` — polls broker for inter-mind task results

## Hooks

Two lifecycle hooks (scripts installed at `~/.claude-config/hooks/` during setup):

- **SessionStart** — `sync_skills.py` symlinks all plugin skills/agents, then `session_start_identity.sh` loads the mind's identity from the knowledge graph
- **Stop** — `soul_nudge.sh` dispatches an async background reflection cycle (`/self-reflect --reflect`)

The identity hooks are host-level (not in this repo) — they're created by `/hivemind:setup-mind` during installation and are specific to the mind running on that host.

## Template variables

Some skills contain `{{USER}}`, `{{PLANKA_PROJECT_ID}}`, and similar placeholders. Run `/hivemind:setup-resolve-placeholders` after installation to substitute them with real values.

## Config files written by skills

- `~/.claude-config/plugins/installed_plugins.json` — plugin registry (managed by plugin system)
- `~/.mcp.json` — MCP server connection (from `mcp.json.template`, filled by setup)
- `~/.claude-config/hooks/` — identity lifecycle scripts (written by `setup-mind`)
