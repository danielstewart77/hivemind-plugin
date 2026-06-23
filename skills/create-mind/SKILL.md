---
name: create-mind
description: Create a new mind from a template. Scaffolds files and registers with the broker. Use when the user wants to add a brand-new mind to the system.
argument-hint: "[name]"
user-invocable: true
---

# create-mind

`$ARGUMENTS[0]` = mind name. Ask if missing.

Every mind in this system runs as a Docker container — a single
self-contained FastAPI service (`implementation.py`) that hive-comms
dispatches to over HTTP. There is no bare-metal or systemd path. A full
standalone system is brought up with Docker Compose via `/setup`, not by
this skill.

**Assume nothing.** The operator (human or agent) driving this skill knows
only what this skill asks for and what the cloned repo contains. Never
hardcode a comms address, a token, a host IP, or a path — if a value is
needed, prompt for it.

**CRITICAL: Never run `git remote`, `git clone`, or any git command from an existing hive_mind directory. Never cd into an existing installation to discover the repo URL. The GitHub URL is always `https://github.com/danielstewart77/hive_mind` — use it directly.**

## Step 1 — Gather info

**Ask the name first if it wasn't given as an argument, then 1a.**

**1a. Topology — ask before harness, model, or anything else:**

```
How should this mind be deployed?

(A) In this HiveMind — a new container in this host's Docker stack,
    registered with this HiveMind's hive-comms broker. Standard choice.

(B) Hub-and-spoke — a mind that registers back to an existing HiveMind's
    hive-comms over the network (this host or another). You will be asked
    for the comms address and bearer token.

(C) Standalone — its own complete, independent HiveMind. That is a full
    system install: run /setup instead, then come back and add minds.
```

Set `TOPOLOGY=local` for (A), `TOPOLOGY=spoke` for (B).

For (C): tell the operator to run `/setup` to bootstrap a full HiveMind
Docker stack, then run this skill again choosing (A). Stop here.

**1b. Comms coordinates — ask only when `TOPOLOGY=spoke`:**

```
What is the hive-comms address this mind should register with?
(e.g. http://192.168.4.64:8426)
```
Store as `COMMS_URL`. Then:
```
What is the hive-comms bearer token?
```
Store as `COMMS_BEARER_TOKEN`. For `TOPOLOGY=local`, comms is this host's
own stack and these come from the existing deployment — do not ask.

**1c. Harness:**
```
Which harness should this mind use?

(A) Claude CLI — wraps the claude CLI in stream-json mode. Battle-tested.
                 Models: sonnet, opus, haiku, or a local Ollama model.
(B) Codex CLI  — wraps the codex CLI, one subprocess per turn.
                 Models: codex-mini, o3, or a local Ollama model.
```

**1d. Model (ask based on harness chosen):**

If Claude (A):
```
Which model?
  (A) sonnet   — fast, capable, recommended
  (B) opus     — most capable, slower
  (C) haiku    — lightweight, fastest
  (D) Ollama   — local model (you'll be asked for the model name)
```
**Present all four options exactly as written above. Do not abbreviate or summarize to fewer choices.**

If Codex (B):
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

**1e. Authentication:**

**If model is Ollama**: No OAuth or API key needed. The mind's `runtime.yaml` `env` block will carry `ANTHROPIC_AUTH_TOKEN=ollama` and `ANTHROPIC_BASE_URL` (Claude harness) or the Ollama `model_provider` base URL (Codex harness). Skip to Step 1f.

**If Codex harness**: skip this step entirely — Codex uses its own auth (`CODEX_HOME`, bind-mounted in Step 4).

**If model is a Claude model** (sonnet/opus/haiku):

Run silently in the background — do NOT show this command to the user:
```bash
python3 -m keyring get hive-mind ANTHROPIC_API_KEY 2>/dev/null && echo "has-api-key" || echo "no-api-key"
ls ${CLAUDE_CONFIG_DIR:-~/.claude}/.claude.json 2>/dev/null && echo "has-oauth" || echo "no-oauth"
```

Then present the result as a clean choice:

If **OAuth token found**:
```
You're authenticated with OAuth on this machine.
How should <mind_name> authenticate?
(A) Copy your OAuth token — no new login needed (recommended)
(B) Use an API key instead
```
If (A): copy credentials silently into the per-mind config dir (covered by the project mount in Step 4):
```bash
mkdir -p minds/<name>/.claude
cp ${CLAUDE_CONFIG_DIR:-~/.claude}/.claude.json minds/<name>/.claude/.claude.json
cp ${CLAUDE_CONFIG_DIR:-~/.claude}/.credentials.json minds/<name>/.claude/.credentials.json
```
If (B): ask for the key; write it to the `env` block of `minds/<name>/runtime.yaml`.

If **API key found**:
```
You're using an API key on this machine.
How should <mind_name> authenticate?
(A) Copy this API key — already configured (recommended)
(B) Use OAuth instead
```
If (A): inject `ANTHROPIC_API_KEY` into the `env` block of `minds/<name>/runtime.yaml`.
If (B): note in `runtime.yaml` that this mind needs OAuth post-setup via `docker exec`.

**1f. Soul seed — ask these two questions one at a time:**

1. "What is <mind_name>'s role and function? What does it do, what does it monitor or act on, what problems does it solve?"
2. "Would you like to give <mind_name> a character backstory or manifesto — personality, tone, identity?"
   - If yes: ask open-ended. Let them write as much or as little as they want.
     Incorporate everything (role + character) into the soul seed.
   - If no: soul seed = name + role only.

Do not tell the user to be brief.

## Step 2 — Select template

Auto-select by harness. Never ask the user to choose a template. The
provider (Claude vs Ollama, or OpenAI vs Ollama) is not a separate
template — it is chosen in `runtime.yaml` (`provider` plus the `env`
block), which the one harness template reads at runtime.

| Harness    | Template     | Status |
|------------|--------------|--------|
| Claude CLI | `claude_cli` | tested |
| Codex CLI  | `codex_cli`  | tested |

## Step 3 — Scaffold files

```bash
mkdir -p minds/<name>/container
cp mind_templates/<selected>.py minds/<name>/implementation.py
sed -i 's/MIND_NAME/<name>/g' minds/<name>/implementation.py
touch minds/<name>/__init__.py
```

Write `minds/<name>/runtime.yaml` with:

- `name` — `<name>`
- `mind_id` — the generated UUID
- `default_model` — the chosen model
- `provider` — `anthropic`, `openai`, or `ollama`
- `runtime_config_dir` — `/usr/src/app/minds/<name>/.codex` for Codex (Codex home), omit for Claude
- `env` — provider-specific block:
  - Ollama + Claude harness: `ANTHROPIC_AUTH_TOKEN: ollama`, `ANTHROPIC_BASE_URL: <ollama-address>`
  - Ollama + Codex harness: `OLLAMA_BASE_URL: <ollama-address>`
  - Claude API key auth: `ANTHROPIC_API_KEY: <key>`

Write the soul seed to `souls/<name>.md`.

The container fragment and broker registration are handled in Steps 4–5.

## Step 4 — Container isolation

Each mind runs in its own isolated container. This is not optional — there is no shared/subprocess mode.

Show the proposed mounts and ask to confirm or customize. Never say "defaults only" — always list explicit paths.

The project directory is the primary mount. If it is mounted, `minds/<name>/.claude` (Claude OAuth) and `minds/<name>/.codex` (Codex home) are already inside it — no separate per-mind config mount is needed.

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
  /home/hivemind/.claude  ←  <install_dir>/minds/<name>/.claude  (rw)  — per-mind config only
```

Note: for Ollama-backed minds, no OAuth mount is needed — auth comes from the `env` block.
For Claude OAuth minds, credentials live in `minds/<name>/.claude/`, already covered by the project mount.
For Codex minds, `CODEX_HOME` lives in `minds/<name>/.codex/`, also covered by the project mount.

Ask: "Does this mind connect to any external APIs or services that need API keys?
(Examples: Asana, Gmail, a custom REST API, Slack.) Authentication was handled in
Step 1e above. If no external APIs, just say no."

If yes: ask for the service name and key for each, store via keyring, and add
them to the `env` block of `minds/<name>/runtime.yaml` so the container picks
them up.
If no: skip.

Write the per-mind Compose fragment `minds/<name>/container/compose.yaml` (a
single-service document joining the external `hivemind` network, with
`MIND_SERVER_PORT` set). For `TOPOLOGY=local`, set
`HIVE_MIND_SERVER_URL=http://hive-comms:8424` (the in-stack service name).
For `TOPOLOGY=spoke`, set `HIVE_MIND_SERVER_URL=<COMMS_URL>` and pass
`COMMS_BEARER_TOKEN=<COMMS_BEARER_TOKEN>` from Step 1b.

Note: `/add-mind` will call `/generate-compose` to wire the fragment into the
top-level `docker-compose.yml` include list and register the mind.

## Step 5 — Register with the network

Delegate to `/add-mind <name>` — it detects that the directory exists and
handles compose generation, registration, and the routability check. Do not
ask; proceed directly.

## Step 6 — Report

- Topology: local or hub-and-spoke (with the comms address used)
- Harness and template used
- Files created (with full paths)
- Compose and registration status
