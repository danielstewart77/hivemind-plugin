# Configuration

Several skills contain instance-specific values that must be updated after installation.

## Planka Board IDs

The following skills reference Planka board, list, and label IDs that are specific to the original author's instance:

- `skills/orchestrator/SKILL.md`
- `skills/create-story/SKILL.md`
- `skills/planka/SKILL.md`
- `skills/story-start/SKILL.md`
- `skills/story-close/SKILL.md`

**After running `/hivemind:setup`, use `/hivemind:planka` to discover your own board and list IDs, then update the values in these skills.**

The IDs to replace are of the form `1720xxxxxxxxxxxxxxx` — search for them across the skills directory:

```bash
grep -r "172015\|172020\|172060" skills/ --include="*.md" -l
```

## MCP Server Path

Rename `mcp.json.template` to `.mcp.json` and replace the placeholder paths:

```json
{
  "mcpServers": {
    "hive-mind-tools": {
      "command": "/path/to/hive_mind/venv/bin/python",
      "args": ["/path/to/hive_mind/mcp_server.py"]
    }
  }
}
```

## Hook Scripts

Hooks reference scripts at `~/.claude-config/hooks/`. These are created by `/hivemind:setup-mind`. If hooks fail at startup, verify those scripts exist.
