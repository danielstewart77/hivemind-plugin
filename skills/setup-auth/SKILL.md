---
name: setup-auth
description: Set up harness authentication (Claude Code and Codex) for Hive Mind. Choose isolation model (shared vs per-mind) and auth method (OAuth, API key, or proxy token). Covers headless OAuth over SSH. Explains pros and cons of each combination.
user-invocable: true
tools: Bash, Read
---

# setup-auth

Configure harness authentication (Claude Code and Codex CLIs) for the Hive Mind
system. The CLIs themselves are installed by `/setup-prerequisites`; this skill
only logs them in. If a CLI is missing when you reach an OAuth step, that is a
`/setup-prerequisites` gap — fix it there, do not hand-install here.

## Step 1 — Explain auth models

Present two independent decisions:

### Decision 1: Isolation Model

**Shared auth (simpler):**
- One Claude OAuth token or API key used by all minds
- Host `~/.claude/` mounted into containers
- Pros: one login, easy to manage, quick to set up
- Cons: all minds share session history, memory, and credentials. A compromised mind sees everything.
- Best for: single-user setups, getting started quickly

**Per-mind auth (recommended for production):**
- Each mind has its own named volume with independent auth
- `CLAUDE_CONFIG_DIR` set per container
- Pros: full isolation — separate memory, sessions, credentials per mind
- Cons: must authenticate each mind individually
- Best for: production deployments, multi-mind systems, security-conscious setups

### Decision 2: Auth Method

**Claude OAuth (subscription users — Claude Max/Pro):**
- Headless-friendly: `claude setup-token` mints a long-lived OAuth token by
  showing a sign-in URL and accepting a pasted authorization code — no browser
  needs to run *on the box*; any browser anywhere completes it.
- Token stored under `~/.claude/` (or exported as `CLAUDE_CODE_OAUTH_TOKEN`).
- Pros: no API key to manage, uses existing subscription.
- Cons: token can expire and must be refreshed.

**Codex OAuth (subscription users — ChatGPT Plus/Pro):**
- Headless-friendly: `codex login --device-auth` prints a device URL and a
  one-time code; sign in at the URL from any browser and enter the code. The
  box itself needs no browser.
- Credentials stored in `~/.codex/auth.json`.
- Pros: no API key to manage, uses existing ChatGPT subscription.
- Cons: the device code expires in ~15 minutes; restart the flow if it lapses.

**API key (pay-per-use):**
- Set `ANTHROPIC_API_KEY` environment variable or write to `~/.claude.json`
- Pros: simple, scriptable, no browser needed
- Cons: pay-per-use costs, key management

**Custom proxy token (corporate/self-hosted gateway):**
- API-only, **no OAuth**. Both harnesses point at a gateway base URL and carry a
  custom token as a `Bearer` header — Claude via `ANTHROPIC_BASE_URL` +
  `ANTHROPIC_AUTH_TOKEN`, Codex via a custom `model_provider` + `env_key`.
- Pros: no browser, scriptable, undetectable to the harness (it just sees an
  API endpoint), works behind enterprise networks.
- Cons: the gateway must expose `/v1/messages` (Claude) and `/v1/responses`
  (Codex). The full wiring lives in `/setup-provider` Step 4 (Custom proxy).
- Best for: University / corporate deployments behind an Azure or LiteLLM proxy.

**None (Ollama-only users):**
- If using only Ollama as a provider, no Claude auth is needed
- The Claude CLI still needs to be installed but auth is handled by the Ollama provider env vars

## Step 2 — Ask user for choices

Ask isolation model preference (recommend per-mind).
Ask auth method based on their provider situation:
- Using Claude (Anthropic)? → Claude OAuth or API key
- Using Codex (OpenAI/ChatGPT)? → Codex OAuth or API key
- Behind a corporate/self-hosted gateway? → Custom proxy token (no OAuth) — record `method: proxy` and complete the wiring in `/setup-provider` Step 4
- Using only Ollama? → No auth needed

## Step 3 — Execute chosen path

**Claude OAuth (headless — works over SSH, no local browser):**
- Confirm the CLI exists first (`command -v claude`); if missing, that is a
  `/setup-prerequisites` gap — install it there, not here.
- Run `claude setup-token`. It prints a sign-in URL and then waits for a pasted
  authorization code. Over SSH this blocks, so run it inside a held-open session
  the operator can return to:
  ```bash
  tmux new-session -d -s claudeauth 'claude setup-token; exec bash'
  tmux capture-pane -t claudeauth -p          # read the URL, hand it to the operator
  # operator authorizes in any browser, returns the code; deliver it:
  tmux send-keys -t claudeauth '<pasted-code>' Enter
  ```
- Verify: `claude --version` runs without an auth error. Store the token where
  the mind reads it — `CLAUDE_CODE_OAUTH_TOKEN` in the mind's `.env`, or the
  per-mind `~/.claude/`. Kill the tmux session when done.

**Codex OAuth (headless — works over SSH, no local browser):**
- Confirm the CLI exists first (`command -v codex`); if missing, fix it in
  `/setup-prerequisites`.
- Run the device flow inside a held-open session:
  ```bash
  tmux new-session -d -s codexauth 'codex login --device-auth; exec bash'
  tmux capture-pane -t codexauth -p           # read the URL + one-time code
  ```
- Hand the operator the URL and the one-time code; they sign in at the URL from
  any browser and enter the code. The flow completes on its own — nothing to
  paste back.
- Verify: `codex login status` reports `Logged in`; credentials land in
  `~/.codex/auth.json`. Kill the tmux session when done.

**Shared + API-key path:** see the API-key blocks below.

**Shared + API key:**
- Ask for the API key
- Store via secrets tool
- Write to `~/.claude.json` or set in container env

**Per-mind + OAuth:**
- Explain that each mind container will need individual auth
- This happens during `/setup-mind` — each new mind gets authenticated after container creation
- Write the choice to `config.yaml`:
```bash
python3 -c "
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
cfg['auth'] = {'isolation': 'per-mind', 'method': 'oauth'}
with open('config.yaml', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False)
print('Auth config written.')
"
```

**Per-mind + API key:**
- Store the API key in the keyring
- Each mind container will reference it from the keyring at startup
- Write the choice to `config.yaml`:
```bash
python3 -c "
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
cfg['auth'] = {'isolation': 'per-mind', 'method': 'api-key'}
with open('config.yaml', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False)
print('Auth config written.')
"
```

**Proxy token (custom gateway):**
- Store the proxy token in the keyring: `python3 -m keyring set hive-mind PROXY_API_KEY`
- Record the choice; the per-harness wiring (base URL, Codex `config.toml`,
  protocol verification) happens in `/setup-provider` Step 4.
```bash
python3 -c "
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
cfg['auth'] = {'isolation': 'shared', 'method': 'proxy'}
with open('config.yaml', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False)
print('Auth config written.')
"
```

## Step 4 — Report

Auth model chosen, method selected, token/key verified (if applicable), next steps.
