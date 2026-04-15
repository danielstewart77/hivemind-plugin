---
name: setup-provider
description: Configure AI providers — Anthropic, OpenAI, Azure OpenAI, Ollama, or OpenAI-compatible endpoints. At least one provider is required. Stores API keys in the keyring and verifies connectivity.
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
1. Anthropic          [not configured]  — Required for Claude CLI/SDK harnesses
2. OpenAI             [not configured]  — Required for Codex CLI harness native models
3. Azure OpenAI       [not configured]  — Enterprise/corporate OpenAI endpoints
4. Ollama             [not configured]  — Local model hosting (no API key needed)
5. OpenAI-compatible  [not configured]  — Generic endpoint (Groq, Together AI, vLLM, etc.)

You need at least one. Which would you like to configure?
(comma-separated numbers, or "all")
```

If `$ARGUMENTS[0]` is provided, skip to that provider directly.

## Step 2 — Anthropic (if selected)

First check the auth method recorded by setup-auth:
```bash
python3 -c "
import yaml
cfg = yaml.safe_load(open('config.yaml'))
print(cfg.get('auth', {}).get('method', ''))
"
```

If auth method is already `oauth` or `api-key` from setup-auth, use that — skip the question below.

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

## Step 3 — OpenAI (if selected)

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

## Step 4 — Azure OpenAI (if selected)

Ask for: endpoint URL, API key, deployment name, API version.
Store API key in keyring. Verify endpoint connectivity.
Add to config.yaml with Azure-specific env overrides.

## Step 5 — Ollama (if selected)

Ask for endpoint URL (default: http://localhost:11434).
Check connectivity:
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

## Step 6 — OpenAI-compatible (if selected)

Ask for: provider name (e.g. "groq"), endpoint URL, API key.
Store API key. Test connectivity using the OpenAI-compatible /v1/models endpoint.
Add to config.yaml as a named provider with env overrides.

## Step 7 — Summary

| Provider | Status | Details |
|----------|--------|---------|
| Anthropic | OK/FAIL | key stored, N models |
| OpenAI | OK/FAIL | key stored, verified |
| Ollama | OK/FAIL | endpoint, N models |
| ... | | |
