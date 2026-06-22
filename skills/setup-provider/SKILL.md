---
name: setup-provider
description: Configure AI providers — Anthropic, OpenAI, a custom proxy/gateway (Azure or any OpenAI/Anthropic-compatible endpoint), or Ollama. At least one provider is required. Stores API keys in the keyring and verifies connectivity.
argument-hint: "[provider-name]"
user-invocable: true
tools: Bash, Read
---

# setup-provider

Configure AI model providers. You need at least one.

## Step 1 — Check current state and present options

```bash
# Check which providers are already configured
grep -A5 "^providers:" config.yaml
```

Present all available providers with current status:

```
Available providers:
1. Anthropic          [not configured]  — Claude harness, direct to api.anthropic.com (OAuth or key)
2. OpenAI             [not configured]  — Codex harness, direct to api.openai.com (OAuth or key)
3. Custom proxy       [not configured]  — One gateway fronting both harnesses (Azure proxy, LiteLLM,
                                          vLLM, Groq, Together, etc.). API-only, no OAuth.
4. Ollama             [not configured]  — Local model hosting (no API key needed)

You need at least one. Which would you like to configure?
(comma-separated numbers, or "all")
```

If `$ARGUMENTS[0]` is provided, skip to that provider directly.

## Step 2 — Anthropic (direct)

First check the auth method recorded by setup-auth:
```bash
python3 -c "
import yaml
cfg = yaml.safe_load(open('config.yaml'))
print(cfg.get('auth', {}).get('method', ''))
"
```

If auth method is already `oauth` or `api-key` from setup-auth, use that — skip the question below. If it is `proxy`, go to Step 4 instead.

Otherwise ask:

> **How do you want to authenticate with Anthropic?**
>
> (A) OAuth — you have a Claude Pro or Max subscription. No API key needed.
>     Claude Code will log in with your Anthropic account. Cost is covered by your plan.
>
> (B) API key — pay-per-token billing. Paste your key from console.anthropic.com.
>
> Choice [A]:

**If OAuth:**
- No key needed. Add to config.yaml.
```yaml
providers:
  anthropic: {}
models:
  sonnet: anthropic
  opus: anthropic
  haiku: anthropic
```
- Tell the user explicitly:
  > "Anthropic OAuth preference recorded — **nothing is authenticated yet.**
  > During /setup-mind, each mind container will need `claude login` run inside it.
  > This opens a browser URL to authorize with your Anthropic account.
  > Have a browser ready when you reach that step."

**If API key:**
- Check for existing: `python3 -m keyring get hive-mind ANTHROPIC_API_KEY 2>/dev/null`
- If missing, ask for it. Store: `python3 -m keyring set hive-mind ANTHROPIC_API_KEY`
- Verify:
```bash
curl -sf https://api.anthropic.com/v1/models \
  -H "x-api-key: <key>" -H "anthropic-version: 2023-06-01" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])),'models')"
```
- Add to config.yaml as above.

## Step 3 — OpenAI (direct)

Ask:

> **How do you want to authenticate with OpenAI?**
>
> (A) OAuth — you have a ChatGPT Plus or Pro subscription. Log in with your
>     OpenAI account. Cost is covered by your subscription.
>
> (B) API key — pay-per-token billing. Get your key at platform.openai.com/api-keys.
>
> Choice [A]:

**If OAuth:**
- No key needed. Add to config.yaml.
```yaml
providers:
  openai:
    env: {}
```
- Tell the user explicitly:
  > "OpenAI OAuth preference recorded — **nothing is authenticated yet.**
  > During /setup-mind, each mind using OpenAI will need its auth flow completed
  > inside the container. Have a browser ready when you reach that step."

**If API key:**
- Check for existing: `python3 -m keyring get hive-mind OPENAI_API_KEY 2>/dev/null`
- If missing, ask for it. Store: `python3 -m keyring set hive-mind OPENAI_API_KEY`
- Verify:
```bash
curl -sf https://api.openai.com/v1/models \
  -H "Authorization: Bearer <key>" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])),'models')"
```
- Add to config.yaml:
```yaml
providers:
  openai:
    env:
      OPENAI_API_KEY: "<from-keyring>"
```

## Step 4 — Custom proxy / gateway (both harnesses, API-only)

This is the path for a corporate or self-hosted gateway that fronts the model
backends — an Azure proxy, LiteLLM, vLLM, Groq, Together AI, or any
OpenAI/Anthropic-compatible endpoint. It is **API-only, no OAuth**: each harness
is pointed at the proxy's base URL and carries a custom token as a `Bearer`
header. This is the validated University deployment path.

**Two protocol requirements** (the gateway must expose both if you run both harnesses):
- **Claude** speaks the Anthropic Messages shape — the proxy must serve a
  `/v1/messages` route.
- **Codex** speaks the OpenAI **Responses** API — the proxy must serve a
  `/v1/responses` route. The older chat-completions wire is **not supported** as
  of Codex 0.141 (`wire_api = "chat"` is rejected at config load).

### Collect once

Ask for: the proxy base URL (e.g. `https://proxy.company.com`), the custom token,
and the model name(s) the proxy serves. Store the token in the keyring:
```bash
python3 -m keyring set hive-mind PROXY_API_KEY
```

### Wire Claude (Anthropic harness)

Claude Code reads `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` and posts to
`<base>/v1/messages` with `Authorization: Bearer <token>`. Add to config.yaml —
`mind_server` injects these into the spawned harness subprocess:
```yaml
providers:
  proxy:
    env:
      ANTHROPIC_BASE_URL: "https://proxy.company.com"
      ANTHROPIC_AUTH_TOKEN: "<from-keyring PROXY_API_KEY>"
      ANTHROPIC_API_KEY: ""          # cleared so it can't shadow the token
models:
  sonnet: proxy
  opus: proxy
  haiku: proxy
```
Verify the route is live and the token is accepted (prompt as arg, stdin from
`/dev/null` — both CLIs slurp piped stdin):
```bash
ANTHROPIC_BASE_URL="https://proxy.company.com" ANTHROPIC_AUTH_TOKEN="<token>" ANTHROPIC_API_KEY= \
  claude -p "Reply with exactly: PROXY-OK" </dev/null
```

### Wire Codex (OpenAI harness)

Codex reads its own `~/.codex/config.toml`. Write a custom model provider —
`wire_api = "responses"` is mandatory:
```toml
model = "<model-served-by-proxy>"
model_provider = "proxy"

[model_providers.proxy]
name = "proxy"
base_url = "https://proxy.company.com/v1"
wire_api = "responses"
env_key = "PROXY_API_KEY"
```
Export `PROXY_API_KEY` (from the keyring) into the mind's environment. Codex GETs
`<base>/v1/models`, then POSTs `<base>/v1/responses` with
`Authorization: Bearer $PROXY_API_KEY`. Verify:
```bash
PROXY_API_KEY="<token>" codex exec --skip-git-repo-check \
  -c 'model_provider="proxy"' -c 'model="<model>"' \
  "Reply with exactly: PROXY-OK" </dev/null
```

### Offline routing proof (no working backend needed)

To certify the wiring without a live backend, run a one-shot HTTP capture server
on `127.0.0.1:9099` that logs method, path, and the `Authorization` header and
returns 404, then point both harnesses at it. Confirm Claude hits
`/v1/messages` and Codex hits `/v1/responses`, each forwarding the expected
`Bearer` token. (Used to validate this path on the test box.)

## Step 5 — Ollama (if selected)

Local models, no key. Same `ANTHROPIC_BASE_URL` redirect as a proxy, with a
placeholder token. Note: Ollama serves OpenAI `/v1` but **not** the Anthropic
`/v1/messages` shape, so it backs Codex (OpenAI-compatible) cleanly but cannot
serve Claude turns directly — it is only a routing stand-in for the Claude path.

Ask for endpoint URL (default: http://localhost:11434). Check connectivity:
```bash
curl -sf <endpoint>/api/tags | jq ".models[].name"
```

If reachable, list available models. Add to config.yaml:
```yaml
providers:
  ollama:
    env:
      ANTHROPIC_AUTH_TOKEN: "ollama"
      ANTHROPIC_API_KEY: ""
      ANTHROPIC_BASE_URL: "<endpoint>"
    api_base: "<endpoint>"
```

## Step 6 — Summary

| Provider | Status | Details |
|----------|--------|---------|
| Anthropic | OK/FAIL | OAuth or key, N models |
| OpenAI | OK/FAIL | OAuth or key, verified |
| Custom proxy | OK/FAIL | base URL, /v1/messages + /v1/responses reachable, token accepted |
| Ollama | OK/FAIL | endpoint, N models |
