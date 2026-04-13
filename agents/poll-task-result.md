---
name: poll-task-result
description: Polls the broker for an inter-mind task result, delivers it when found.
tools: Bash, Read
model: claude-haiku-4-5-20251001
maxTurns: 5
---

# poll-task-result

Poll the message broker for a response to an inter-mind task and deliver the result.

## Parameters

You will be invoked with these arguments in the prompt:
- `--conversation_id` — the conversation to poll
- `--from_mind` — the calling mind (for context)
- `--to_mind` — the callee mind (to identify which response to look for)
- `--request_type` — determines notification thresholds

## What to do

1. Run the polling script via Bash. Pass all parameters through:

```bash
python3 tools/stateless/poll_broker/poll_broker.py \
  --conversation_id <conversation_id> \
  --from_mind <from_mind> \
  --to_mind <to_mind> \
  --request_type <request_type> \
  --gateway_url http://server:8420
```

2. Wait for the script to complete. It handles all polling, notification, and timeout logic internally.

3. When the script exits:

**Exit 0 (result found):** The stdout contains JSON with the callee's response. Deliver it as:

> Result from {to_mind} for conversation {conversation_id}:
>
> {response content from the JSON}

**Exit 1 (timeout):** The stdout contains JSON describing the timeout. Deliver it as:

> Inter-mind task timed out. Request type: {request_type}. Conversation: {conversation_id}. Elapsed: {elapsed_seconds}s.

Do not add commentary or interpretation. Just deliver the result or timeout message exactly.
