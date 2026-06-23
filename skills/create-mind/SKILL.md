---
name: create-mind
description: Create a new mind from a template. Scaffolds files and registers with the broker. Use when the user wants to add a brand-new mind to the system.
argument-hint: "[name] [--standalone]"
user-invocable: true
---

# create-mind

`$ARGUMENTS[0]` = mind name. Ask if missing.
`$ARGUMENTS[1]` = `--standalone` if creating an isolated (non-networked) mind. Default: connected.

Set `STANDALONE=true` if `--standalone` is present.

**CRITICAL: Never run `git remote`, `git clone`, or any git command from an existing hive_mind directory. Never cd into an existing installation to discover the repo URL. The GitHub URL is always `https://github.com/danielstewart77/hive_mind` — use it directly.**

## Step 1 — Gather info

**The very first questions — ask these before harness, model, or anything else.**
If the name was given as an argument, skip asking for it and go straight to 1a.

**1a. Location — where does this mind run?**

```
Where will this mind run?

(A) In this HiveMind — Docker container inside the existing hive_mind stack.
    Standard choice. Managed alongside Ada and other minds.

(B) On this system, outside HiveMind — bare-metal service on this host,
    in a directory outside the hive_mind repo.
    Use when the mind needs full host access (filesystem, Docker daemon,
    system config) that container isolation would prevent.

(C) On a remote system — different host, accessed via SSH.
    (Delegates to /setup-remote after gathering info here.)
```

Set `LOCATION=docker` for (A), `LOCATION=local_external` for (B), `LOCATION=remote` for (C).

**1b. Connectivity — ask immediately after 1a (for A and B; skip for C):**

```
Should this mind connect to this HiveMind, or run fully independently?

(A) Hub-and-spoke — registers with this HiveMind's broker. Ada can delegate
    to it; it appears in the mind registry. Standard for collaborative minds.

(B) Fully standalone — its own complete HiveMind system: server, broker,
    MCP stack, everything. Does not register with this broker at all.
    Use when the mind must operate independently even if this HiveMind is down.
    Example: an operator mind that may need to restart or repair this system.
```

Set `STANDALONE=true` if (B). For standalone: this is a full HiveMind installation,
not just a single mind. Steps 3–5 change significantly — see below.

Set `BARE_METAL=true` if LOCATION is `local_external` or `remote`.

---

**1b. Harness:**
```
Which harness should this mind use?

(A) Claude CLI  — wraps the claude CLI in stream-json mode. Battle-tested.
                  Models: sonnet, opus, haiku, Ollama
(B) Claude SDK  — uses the Claude Code SDK directly. More programmatic, agentic.
                  Models: sonnet, opus, haiku, Ollama
(C) Codex CLI   — Codex CLI. Models: codex-mini, o3, Ollama
(D) Codex SDK   — Codex SDK. Models: codex-mini, o3, Ollama (untested)
```

**1c. Model (ask based on harness chosen):**

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

**1d. Authentication:**

**If model is Ollama**: No OAuth or API key needed. Note that the bare-metal `.env` (or container env) will need `ANTHROPIC_AUTH_TOKEN=ollama` and `ANTHROPIC_BASE_URL`. Skip to Step 1e.

**If Codex harness**: skip this step entirely — Codex uses its own auth.

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
If (A) and Docker: copy credentials silently:
```bash
cp ${CLAUDE_CONFIG_DIR}/.claude.json minds/<name>/.claude/.claude.json
cp ${CLAUDE_CONFIG_DIR}/.credentials.json minds/<name>/.claude/.credentials.json
```
If (A) and bare-metal: note in `.env` stub that OAuth files must be copied to the install path.
If (B): ask for key; write to env.

If **API key found**:
```
You're using an API key on this machine.
How should <mind_name> authenticate?
(A) Copy this API key — already configured (recommended)
(B) Use OAuth instead
```
If (A): inject `ANTHROPIC_API_KEY` into env (container block or `.env` depending on deployment type).
If (B) and Docker: note in `runtime.yaml` that this mind needs OAuth post-setup via `docker exec`.
If (B) and bare-metal: note in `.env` stub that OAuth must be set up manually.

**1e. Soul seed — ask these two questions one at a time:**

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

**If STANDALONE=true (fully standalone HiveMind installation):**

This is not a single mind — it's a full HiveMind system. The scaffold is:

1. Clone the hive_mind repo to `<INSTALL_PATH>`:
   ```bash
   git clone https://github.com/danielstewart77/hive_mind <INSTALL_PATH>
   ```
   Do NOT copy from any existing local installation. Do NOT cd into any other directory. Do NOT run git commands from any path other than `<INSTALL_PATH>`.
2. Create `<INSTALL_PATH>/config.yaml`. A standalone instance needs its own
   nervous system; if comms on this host already binds 8426, give the standalone
   one a non-conflicting comms port.
3. Copy OAuth credentials to `<INSTALL_PATH>/.claude/` (same as bare-metal above).
4. Create venv and install deps:
   ```bash
   python3 -m venv <INSTALL_PATH>/.venv
   <INSTALL_PATH>/.venv/bin/pip install -r <INSTALL_PATH>/requirements.txt
   ```
5. The mind's own implementation goes under `<INSTALL_PATH>/minds/<name>/` using the
   selected template (same as the Docker scaffold, but targeting INSTALL_PATH).
6. Write the soul seed to `<INSTALL_PATH>/souls/<name>.md`.
7. Show a systemd unit for the standalone system's gateway server:
   ```ini
   [Unit]
   Description=<name> HiveMind — Standalone Gateway
   After=network.target

   [Service]
   Type=simple
   User=<current user>
   WorkingDirectory=<INSTALL_PATH>
   ExecStart=<INSTALL_PATH>/.venv/bin/python3 server.py
   Restart=on-failure
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```
8. Pause for user to place and start the systemd unit.

Skip Steps 4 and 5 (no broker registration — this system is independent).
Go directly to Step 6 — Report.

---

**If Docker (LOCATION=docker, not standalone):**
```bash
mkdir -p minds/<name>/container
cp mind_templates/<selected>.py minds/<name>/implementation.py
sed -i 's/MIND_NAME/<name>/g' minds/<name>/implementation.py
touch minds/<name>/__init__.py
```
Write `minds/<name>/runtime.yaml` (name, mind_id [the generated UUID],
default_model, provider, runtime_config_dir, and a provider-specific `env`
block — e.g. `OLLAMA_BASE_URL` for ollama). The container fragment and broker
registration are handled in Steps 4–5 via `/add-mind`. Write the soul seed to
`souls/<name>.md`.

**If bare-metal — standalone (STANDALONE=true or no existing instance):**

Ask one question only:

```
Where should this Hive Mind be installed?
(e.g. /home/daniel/hive_mind_skippy)
```

Store as `INSTALL_PATH`. The Hive Mind repo will be cloned here — the mind lives inside it at `<INSTALL_PATH>/minds/<name>/`. Do NOT ask for an existing hive_mind path. Do NOT reference or touch any other hive_mind installation on the host.

```bash
git clone https://github.com/danielstewart77/hive_mind <INSTALL_PATH>
```

Then scaffold the mind inside the cloned repo:

```bash
mkdir -p <INSTALL_PATH>/minds/<name>
cp <INSTALL_PATH>/mind_templates/<selected>.py <INSTALL_PATH>/minds/<name>/implementation.py
sed -i 's/MIND_NAME/<name>/g' <INSTALL_PATH>/minds/<name>/implementation.py
touch <INSTALL_PATH>/minds/<name>/__init__.py
```

Write `<INSTALL_PATH>/souls/<name>.md` with the soul seed.

Ask what port to use (default: 8421).

Write `<INSTALL_PATH>/.env`:
```
MIND_ID=<name>
MIND_SERVER_PORT=<port>
PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring
CLAUDE_CONFIG_DIR=<INSTALL_PATH>/.claude
```

Create venv and install deps — do not ask:
```bash
python3 -m venv <INSTALL_PATH>/.venv
<INSTALL_PATH>/.venv/bin/pip install -r <INSTALL_PATH>/requirements.txt
```

Copy OAuth credentials — do not ask:
```bash
mkdir -p <INSTALL_PATH>/.claude
cp ${CLAUDE_CONFIG_DIR:-~/.claude}/.credentials.json <INSTALL_PATH>/.claude/.credentials.json
cp ${CLAUDE_CONFIG_DIR:-~/.claude}/.claude.json <INSTALL_PATH>/.claude/.claude.json 2>/dev/null || true
```

Show the systemd unit and pause — user must place it manually (requires sudo):
```ini
[Unit]
Description=<name> — Hive Mind Standalone
After=network.target

[Service]
Type=simple
User=<current user>
WorkingDirectory=<INSTALL_PATH>
EnvironmentFile=<INSTALL_PATH>/.env
ExecStart=<INSTALL_PATH>/.venv/bin/python3 <INSTALL_PATH>/mind_server.py
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```
Save as /etc/systemd/system/<name>.service, then run:
  sudo systemctl daemon-reload
  sudo systemctl start <name>

Tell me when it's running and I'll verify health and register it.
```

---

**If bare-metal — hub-and-spoke (joining an existing instance):**

Ask two questions — one at a time:

1. "Where should this mind be installed?"
   (e.g. `/home/daniel/my_mind`)
   Store as `INSTALL_PATH`. All code, runtime files, and credentials go here.

2. "Where is the existing Hive Mind project on this host?"
   (e.g. `/home/daniel/Storage/Dev/hive_mind`)
   Store as `HIVE_MIND_PATH`. Used only to copy templates from — nothing is written there.

Scaffold everything into INSTALL_PATH:

```bash
mkdir -p <INSTALL_PATH>/minds/<name>
cp <HIVE_MIND_PATH>/mind_templates/<selected>.py <INSTALL_PATH>/minds/<name>/implementation.py
sed -i 's/MIND_NAME/<name>/g' <INSTALL_PATH>/minds/<name>/implementation.py
touch <INSTALL_PATH>/minds/<name>/__init__.py
mkdir -p <INSTALL_PATH>/souls
cp <HIVE_MIND_PATH>/mind_server.py <INSTALL_PATH>/mind_server.py
```

Write `<INSTALL_PATH>/souls/<name>.md` with the soul seed.

Ask what port to use (default: 8421).

Write `<INSTALL_PATH>/.env`. `HIVE_MIND_SERVER_URL` is the comms gateway: use
`http://localhost:8426` only when comms runs on this same host; on a satellite
host point it at the managing instance's comms (the `COMMS_URL` recorded by
`/setup-nervous-system`'s Existing path), e.g. `http://192.168.4.64:8426`. The
mind also needs the comms bearer token and its lucent coordinates:
```
MIND_ID=<uuid>
MIND_SERVER_PORT=<port>
HIVE_MIND_SERVER_URL=<COMMS_URL>      # http://localhost:8426 local, or remote comms on a satellite
COMMS_BEARER_TOKEN=<comms token>
LUCENT_URL=<lucent URL>              # http://localhost:8425 local, or remote lucent on a satellite
LUCENT_BEARER_TOKEN=<lucent token>
PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring
CLAUDE_CONFIG_DIR=<INSTALL_PATH>/.claude
```

Create venv and install deps — do not ask:
```bash
python3 -m venv <INSTALL_PATH>/.venv
<INSTALL_PATH>/.venv/bin/pip install -r <HIVE_MIND_PATH>/requirements.txt
```

Copy OAuth credentials — do not ask:
```bash
mkdir -p <INSTALL_PATH>/.claude
cp ${CLAUDE_CONFIG_DIR:-~/.claude}/.credentials.json <INSTALL_PATH>/.claude/.credentials.json
cp ${CLAUDE_CONFIG_DIR:-~/.claude}/.claude.json <INSTALL_PATH>/.claude/.claude.json 2>/dev/null || true
```

Show the systemd unit and pause:
```ini
[Unit]
Description=<name> — Hive Mind Bare-Metal Mind
After=network.target

[Service]
Type=simple
User=<current user>
WorkingDirectory=<INSTALL_PATH>
EnvironmentFile=<INSTALL_PATH>/.env
ExecStart=<INSTALL_PATH>/.venv/bin/python3 <INSTALL_PATH>/mind_server.py
Restart=no
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```
Save as /etc/systemd/system/<name>.service, then run:
  sudo systemctl daemon-reload
  sudo systemctl start <name>

Tell me when it's running and I'll verify health and register it.
```

## Step 4 — Container isolation (Docker only — skip entirely for bare-metal)

Each Docker mind runs in its own isolated container. This is not optional — there is no shared/subprocess mode.

Show the proposed mounts and ask to confirm or customize. Never say "defaults only" — always list explicit paths.

**Proposed mounts:**

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
  /home/hivemind/.claude  ←  <install_dir>/minds/<name>/.claude  (rw)  — per-mind config only
```

Note: for Ollama-backed minds, no OAuth mount is needed — auth comes from env vars only.
For Claude OAuth minds, OAuth credentials live in `minds/<name>/.claude/` which is
already covered by the project directory mount above.

If the user wants a different set, let them list paths freely.

Ask: "Does this mind connect to any external APIs or services that need API keys?
(Examples: Asana, Gmail, a custom REST API, Slack.) Claude authentication was
handled in Step 1d above. If no external APIs, just say no."

If yes: ask for the service name and key for each, store via keyring, and add
them to the `env` block of `minds/<name>/runtime.yaml` so the container picks
them up.
If no: skip.

Write the per-mind Compose fragment `minds/<name>/container/compose.yaml` (a
single-service document joining the external `hivemind` network, with
`HIVE_MIND_SERVER_URL=http://hive-comms:8424` and `MIND_SERVER_PORT` set).
Note: `/add-mind` will call `/generate-compose` to wire the fragment into the
top-level `docker-compose.yml` include list and register the mind.

## Step 5 — Register with the network

**If STANDALONE=true:** Skip this step entirely. The standalone system is independent.

Do not ask for hub-and-spoke minds. Proceed directly.

**If Docker (hub-and-spoke):**
Delegate to `/add-mind <name>` (it will detect Scenario C — directory exists — and handle compose generation, registration, and routability check).

**If bare-metal, local_external (hub-and-spoke):**
Wait for the user to confirm the service is running. Once confirmed, run without asking:

```bash
curl -sf http://localhost:<port>/health && echo "up" || echo "not responding"
```

If health passes, immediately delegate to `/add-mind <name>` — do not ask.
If health fails, report the error and stop. Do not register a mind that isn't responding.

## Step 6 — Report

- Deployment type: Docker or bare-metal
- Template used
- Files created (with full paths)
- For bare-metal: systemd unit shown, port, INSTALL_PATH. All code lives there — nothing
  written to hive_mind.
- For Docker: compose and registration status
