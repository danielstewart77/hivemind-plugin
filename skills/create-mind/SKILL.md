---
name: create-mind
description: Create a new mind from a template. Scaffolds MIND.md and implementation.py, then registers with the broker. Use when the user wants to add a brand-new mind to the system.
argument-hint: "[name] [--standalone]"
user-invocable: true
---

# create-mind

`$ARGUMENTS[0]` = mind name. Ask if missing.
`$ARGUMENTS[1]` = `--standalone` if creating a standalone (non-federated) mind. Default: federated.

Set `STANDALONE=true` if `--standalone` is present.

## Step 1 — Gather info

Ask in this order:

**1a. Harness:**
```
Which harness should this mind use?

(A) Claude CLI  — wraps the claude CLI in stream-json mode. Battle-tested.
                  Models: sonnet, opus, haiku, Ollama
(B) Claude SDK  — uses the Claude Code SDK directly. More programmatic, agentic.
                  Models: sonnet, opus, haiku, Ollama
(C) Codex CLI   — Codex CLI. Models: codex-mini, o3, Ollama
(D) Codex SDK   — Codex SDK. Models: codex-mini, o3, Ollama (untested)
```

**1b. Model (ask based on harness chosen):**

If Claude (A or B):
```
Which model?
  (A) sonnet   — fast, capable, recommended
  (B) opus     — most capable, slower
  (C) haiku    — lightweight, fastest
  (D) Ollama   — local model (you'll be asked for the model name)
```

If Codex (C or D):
```
Which model?
  (A) codex-mini  — lightweight
  (B) o3          — most capable
  (C) Ollama      — local model (you'll be asked for the model name)
```

If Ollama: ask for the model name (e.g. `llama3`, `mistral`).

**1c. Authentication (Claude harness only — skip for Codex/Ollama-only):**

Detect what the host is currently using:
```bash
python3 -m keyring get hive-mind ANTHROPIC_API_KEY 2>/dev/null && echo "has-api-key" || echo "no-api-key"
ls ${CLAUDE_CONFIG_DIR:-~/.claude-config}/.claude.json 2>/dev/null && echo "has-oauth" || echo "no-oauth"
```

If **OAuth token found**:
```
You're authenticated with OAuth on this machine.
How should <mind_name> authenticate?
(A) Copy your OAuth token — no new login needed (recommended)
(B) Use an API key instead
```
If (A): `cp ${CLAUDE_CONFIG_DIR}/.claude.json minds/<name>/.claude/.claude.json`
If (B): ask for key or check keyring; write to container env in MIND.md.

If **API key found**:
```
You're using an API key on this machine.
How should <mind_name> authenticate?
(A) Copy this API key — already configured (recommended)
(B) Use OAuth instead
```
If (A): inject `ANTHROPIC_API_KEY` into the container env in MIND.md.
If (B): note in MIND.md that this mind needs OAuth post-setup. This is the only
case requiring a separate terminal step (`docker exec -it hive-mind-<name> claude`),
and only because the user explicitly chose OAuth when a key was available.

**1d. Soul seed — ask these questions one at a time:**

1. "What is <mind_name>'s role? What does it do — what problems does it solve?"
2. "What is <mind_name>'s identity? How does it present itself — personality,
   tone, and character? (This is separate from what it does.)"
3. "Would you like to write a backstory or manifesto for this character?"
   - If yes: ask open-ended. Let them write as much or as little as they want.
     Incorporate it into the soul seed.
   - If no: skip. Soul seed = name + role + identity.

Do not tell the user to be brief.

## Step 2 — Select template

Auto-select based on harness + model. Never ask the user to choose a template.

| Harness    | Model        | Template              | Status   |
|------------|--------------|-----------------------|----------|
| Claude CLI | Claude model | `claude_cli_claude`   | tested   |
| Claude CLI | Ollama       | `claude_cli_ollama`   | tested   |
| Claude SDK | Claude model | `claude_sdk_claude`   | tested   |
| Claude SDK | Ollama       | `claude_sdk_ollama`   | untested |
| Codex CLI  | Codex model  | `codex_cli_codex`     | tested   |
| Codex CLI  | Ollama       | `codex_cli_ollama`    | untested |
| Codex SDK  | Codex model  | `codex_sdk_codex`     | untested |
| Codex SDK  | Ollama       | `codex_sdk_ollama`    | untested |

If the selected template is untested, warn the user: "This combination is untested — it may need adjustments. Continuing anyway."

## Step 3 — Scaffold files

```bash
mkdir -p minds/<name>
cp mind_templates/<selected>.py minds/<name>/implementation.py
sed -i 's/MIND_NAME/<name>/g' minds/<name>/implementation.py
touch minds/<name>/__init__.py
```

Write `minds/<name>/MIND.md` with frontmatter from user's choices and soul seed from their description.

## Step 4 — Container isolation

Ask: "Should this mind run in its own isolated container? (recommended — gives each mind
granular control over what it can access)"

Default: **yes**. Own container is recommended because it lets you control exactly what
each mind can see and write. A shared container means all minds have the same access.

**If yes (own container):**

Show the proposed mounts and ask to confirm or customize. Never say "defaults only"
— always list explicit paths.

Start with the project folder as the first recommended mount — for most minds,
this is the most important one since it contains the codebase, tools, and skills:

```
Proposed mounts (host bind mounts — files are visible directly on your drive):

  /usr/src/app  ←  <install_dir>  (rw)  — project code, tools, and skills [recommended]
  /home/hivemind/.host-claude  ←  ~/.claude  (ro)  — host Claude auth
  /home/hivemind/.claude-config  ←  <install_dir>/minds/<name>/.claude  (rw)  — per-mind config

Host bind mounts are recommended over Docker named volumes. Host mounts let you
see exactly what the mind reads and writes. Docker named volumes are managed by
Docker in a system location — harder to inspect or back up.

Would you like to:
  (A) Use these mounts
  (B) Customize — add, remove, or change paths
```

If the user wants a different set, let them list paths freely.

Ask: "Does this mind connect to any external APIs or services that need API keys?
(Examples: Asana, Gmail, a custom REST API, Slack.) Claude authentication was
handled in Step 1c above. If no external APIs, just say no."

If yes: ask for the service name and key for each, store via keyring, and note
them in the MIND.md frontmatter so the container picks them up.
If no: skip.

Write the `container:` block into the MIND.md frontmatter.
Note: `/add-mind` will call `/generate-compose` to update docker-compose.yml.

**If no (shared container):**
The mind runs as a subprocess inside the main hive_mind container. It inherits all
mounts from that container with no additional isolation.

## Step 5 — Register or Generate Standalone Compose

**If federated:**
Delegate to `/add-mind <name>` (it will detect Scenario C — directory exists — and handle compose generation, registration, and routability check).

**If standalone:**
Delegate to `/generate-compose <name> --standalone` to generate a minimal `docker-compose.yml` with only the mind container and a lightweight message handler. No broker, no gateway, no Neo4j.

After compose generation:
```bash
docker compose up -d --build
```

Confirm the mind container is running:
```bash
docker compose ps
```

Note: standalone minds cannot be registered with the broker. Skip the broker registration step entirely.

## Step 6 — Report

- Template used
- Topology: federated or standalone
- Files created
- Registration and routability status (federated only)
- Container status (standalone)
