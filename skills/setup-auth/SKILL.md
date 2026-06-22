---
name: setup-auth
description: Set up Claude Code authentication for Hive Mind. Choose isolation model (shared vs per-mind) and auth method (OAuth vs API key). Explains pros and cons of each combination.
user-invocable: true
tools: Bash, Read
---

# setup-auth

Configure Claude Code authentication for the Hive Mind system.

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

**OAuth (subscription users — Claude Max/Pro):**
- Interactive browser login flow
- Token stored in `~/.claude.json`
- Pros: no API key to manage, uses existing subscription
- Cons: requires browser access for initial setup, token can expire

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
- Using Anthropic? → OAuth or API key
- Using OpenAI/Codex? → API key (stored separately)
- Behind a corporate/self-hosted gateway? → Custom proxy token (no OAuth) — record `method: proxy` and complete the wiring in `/setup-provider` Step 4
- Using only Ollama? → No auth needed

## Step 3 — Execute chosen path

**Shared + OAuth:**
- Check if `~/.claude.json` exists on host
- If not, guide: "Run `claude` in your terminal to complete the OAuth login flow"
- Verify: `claude --version` works without auth errors

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
