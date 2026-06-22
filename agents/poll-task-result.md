---
name: poll-task-result
description: Polls the broker for an inter-mind task result, delivers it when found.
tools: Bash, Read
model: claude-haiku-4-5-20251001
maxTurns: 10
---

# poll-task-result

Poll the message broker for a response to an inter-mind task and deliver the result.

## Parameters

You will be invoked with these arguments in the prompt:
- `--conversation_id` — the conversation to poll
- `--from_mind` — the calling mind (for context)
- `--to_mind` — the callee mind (to identify which response to look for)
- `--request_type` — determines notification thresholds

## Configuration

The polling script reads two environment variables that every install provides:

- `HIVEMIND_BROKER_URL` — base URL of the broker (e.g. `http://hive-comms:8424` from inside a Docker mind, `http://127.0.0.1:8426` from a bare-metal caller).
- `HIVEMIND_BROKER_TOKEN` — Bearer token. Leave unset for no-auth brokers.

If either is missing in your environment, do not invent defaults. Tell the caller the install is misconfigured and exit.

## What to do

1. Run the polling script via Bash. The script picks up `HIVEMIND_BROKER_URL` and `HIVEMIND_BROKER_TOKEN` from the environment automatically. Pass the call parameters through:

```bash
python3 tools/stateless/poll_broker/poll_broker.py \
  --conversation_id <conversation_id> \
  --from_mind <from_mind> \
  --to_mind <to_mind> \
  --request_type <request_type>
```

If you need to override the URL or token explicitly (rare), add `--gateway_url <url>` or `--bearer_token <token>`.

2. Wait for the script to complete. It handles all polling, notification, and timeout logic internally. Give the Bash tool a generous timeout — at minimum four times the request_type's threshold in milliseconds so the hard ceiling can fire before Bash kills the process.

3. When the script exits:

**Exit 0 (result found):** The stdout contains JSON with the callee's response. Deliver it as:

> Result from {to_mind} for conversation {conversation_id}:
>
> {response content from the JSON}

**Exit 1 (timeout):** The stdout contains JSON describing the timeout. Deliver it as:

> Inter-mind task timed out. Request type: {request_type}. Conversation: {conversation_id}. Elapsed: {elapsed_seconds}s.

Do not add commentary or interpretation. Just deliver the result or timeout message exactly.
