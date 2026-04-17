---
name: create-mind
description: Create a new mind from a template. Scaffolds MIND.md and implementation.py, then registers with the broker. Use when the user wants to add a brand-new mind to the system.
argument-hint: "[name] [--standalone]"
user-invocable: true
---

# create-mind

`$ARGUMENTS[0]` = mind name. Ask if missing.
`$ARGUMENTS[1]` = `--standalone` if creating an isolated (non-networked) mind. Default: connected.

Set `STANDALONE=true` if `--standalone` is present. Do not ask about this upfront — ask in Step 5.

## Step 1 — Gather info

Ask only for the name up front. Do NOT ask about network topology yet.

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
**Present all four options exactly as written above. Do not abbreviate or summarize to fewer choices.**

If Codex (C or D):
```
Which model?
  (A) codex-mini  — lightweight
  (B) o3          — most capable
  (C) Ollama      — local model (you'll be asked for the model name)
```

If Ollama: ask for the server address first, then query available models:

1. Ask: "What is the Ollama server address?" (e.g. `http://localhost:11434`)
2. Query available models:
```bash
curl -sf <ollama-address>/api/tags | python3 -c "import sys,json; [print(f'  ({chr(65+i)}) {m[\"name\"]}') for i,m in enumerate(json.load(sys.stdin).get('models',[]))]"
```
3. Present the numbered list and ask the user to pick one.
4. Store the chosen model name and server address. If the curl fails, ask the user to type the model name manually.

**1c. Authentication:**

**If model is Ollama** (regardless of harness — Claude CLI or SDK):
Do NOT copy OAuth files. Instead, inject these env vars into the container block in MIND.md:
```yaml
environment:
  ANTHROPIC_AUTH_TOKEN: "ollama"
  ANTHROPIC_BASE_URL: "http://<ollama-host>:11434"
```
The Ollama server address was already collected in Step 1b — use it here. No OAuth or API key needed. Skip to Step 1d.

**If model is a Claude model** (sonnet/opus/haiku), detect what the host is currently using:
```bash
python3 -m keyring get hive-mind ANTHROPIC_API_KEY 2>/dev/null && echo "has-api-key" || echo "no-api-key"
ls ${CLAUDE_CONFIG_DIR:-~/.claude-config}/.claude.json 2>/dev/null && echo "has-oauth" || echo "no-oauth"
```

**If Codex harness**: skip this step entirely — Codex uses its own auth.

If **OAuth token found**:
```
You're authenticated with OAuth on this machine.
How should <mind_name> authenticate?
(A) Copy your OAuth token — no new login needed (recommended)
(B) Use an API key instead
```
If (A):
```bash
cp ${CLAUDE_CONFIG_DIR}/.claude.json minds/<name>/.claude/.claude.json
cp ${CLAUDE_CONFIG_DIR}/.credentials.json minds/<name>/.claude/.credentials.json
```
Claude Code stores OAuth tokens in `.credentials.json`, NOT `.claude.json`.
Both files must be copied or auth will fail with "Not logged in."
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

**1d. Soul seed — ask these two questions one at a time:**

1. "What is <mind_name>'s role and function? What does it do, what does it monitor or act on, what problems does it solve?"
2. "Would you like to give <mind_name> a character backstory or manifesto — personality, tone, identity?"
   - If yes: ask open-ended. Let them write as much or as little as they want.
     Incorporate everything (role + character) into the soul seed.
   - If no: soul seed = name + role only.

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

Ask:

```
Should this mind run in its own isolated container?

(A) Own container (recommended) — each mind gets its own Docker container.
    Best when you have multiple minds or want to control exactly which files
    each mind can read and write. Lets you scope access per-mind.

(B) Shared container — the mind runs as a subprocess inside the main
    hive_mind container. Simpler setup, fine for a single mind or when
    you don't need per-mind access control. Inherits all mounts from the
    main container.
```

**If (A) own container:**

Show the proposed mounts and ask to confirm or customize. Never say "defaults only"
— always list explicit paths.

The project directory is the primary mount. If it is mounted, `minds/<name>/.claude`
is already inside it — no separate per-mind config mount is needed.

```
Proposed mounts (host bind mounts — files are visible directly on your drive):

  /usr/src/app  ←  <install_dir>  (rw)  — project code, tools, skills, and all mind configs

Host bind mounts are recommended over Docker named volumes. Host mounts let you
see exactly what the mind reads and writes.

Would you like to:
  (A) Use this mount
  (B) Customize — add, remove, or change paths
```

If the user does NOT mount the full project directory, offer this fallback instead:
```
  /home/hivemind/.claude-config  ←  <install_dir>/minds/<name>/.claude  (rw)  — per-mind config only
```

Note: for Ollama-backed minds, no OAuth mount is needed — auth comes from env vars only.
For Claude OAuth minds, OAuth credentials live in `minds/<name>/.claude/` which is
already covered by the project directory mount above.

If the user wants a different set, let them list paths freely.

Ask: "Does this mind connect to any external APIs or services that need API keys?
(Examples: Asana, Gmail, a custom REST API, Slack.) Claude authentication was
handled in Step 1c above. If no external APIs, just say no."

If yes: ask for the service name and key for each, store via keyring, and note
them in the MIND.md frontmatter so the container picks them up.
If no: skip.

Write the `container:` block into the MIND.md frontmatter.
Note: `/add-mind` will call `/generate-compose` to update docker-compose.yml.

**If (B) shared container:**
The mind runs as a subprocess inside the main hive_mind container. It inherits all
mounts from that container with no additional isolation.

## Step 5 — Network topology

Ask now (not before):

```
Should this mind join the Hive Mind network?

(A) Connected (recommended for most cases)
    This mind joins the broker and becomes part of your Hive Mind system.
    Ada can delegate tasks to it, you can message it through Telegram,
    and other minds can route work to it. Whether this is your first mind
    or your fifth, choose this if it's meant to be part of your setup.
    Example: adding a coding mind, a research mind, or a specialist agent
    alongside an existing Ada.

(B) Isolated — completely independent, no network connection
    This mind runs on its own with no broker, no routing, and no
    relationship to the rest of the system. It can't receive messages
    from other minds and won't appear in the network.
    Example: spinning up a private Claude instance for a client or a
    project that must be fully air-gapped from your main Hive Mind.
    If you're unsure, you almost certainly want (A).
```

**If (A) connected (formerly "federated"):**
Delegate to `/add-mind <name>` (it will detect Scenario C — directory exists — and handle compose generation, registration, and routability check).

**If (B) isolated (formerly "standalone"):**
Delegate to `/generate-compose <name> --standalone` to generate a minimal `docker-compose.yml` with only the mind container and a lightweight message handler. No broker, no gateway, no Neo4j.

After compose generation:
```bash
docker compose up -d --build
```

Confirm the mind container is running:
```bash
docker compose ps
```

Note: isolated minds cannot be registered with the broker. Skip the broker registration step entirely.

## Step 6 — Report

- Template used
- Topology: federated or standalone
- Files created
- Registration and routability status (federated only)
- Container status (standalone)
