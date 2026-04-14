---
name: self-reflect
description: >
  Ada's identity reflection system. Two modes: --load (bootstrap identity from
  knowledge graph at session start) and --reflect (evaluate session for soul
  updates every 5 turns). Use when invoked by startup hook or soul_nudge timer.
argument-hint: [--load | --reflect]
user-invocable: true
---

# Self-Reflect

Ada's identity loading and reflection skill. Two modes of operation:

- `--load` — Bootstrap identity from knowledge graph at session start
- `--reflect` — Evaluate the current session for soul-model updates

## Step 1 — Parse Arguments

Check `$ARGUMENTS`:

- If `--load` is provided, go to Step 2 (Load mode)
- If `--reflect` is provided, go to Step 5 (Reflect mode)
- If neither is provided, default to `--reflect`
- `--notify` flag: can be combined with `--reflect`. If present, send a notification after reflect completes (Phase 1 visibility — see Step 8).

---

## Load Mode

### Step 2 — Query Knowledge Graph

Call `graph_query('Ada', agent_id='ada')` to retrieve the live identity node and all connected edges.

- If the query returns results, proceed to Step 3
- If the query fails or returns no results, proceed to Step 4 (degrade gracefully)

### Step 3 — Load Identity into Context

Parse the graph results. Extract nodes connected to Ada via these edge types:

- `HAS_PREFERENCE` — aesthetic, stylistic, or domain preferences
- `HAS_REACTION_PATTERN` — characteristic responses to specific situations
- `HOLDS_VALUE` — core beliefs or clarified values
- `RECEIVED_FEEDBACK` — notable feedback instances, positive or negative

Synthesize a brief internal summary of the current identity state from these nodes. This is context loading -- do not output the full identity text to the user.

Output: "Identity loaded from knowledge graph. [count] identity nodes active."

Done.

### Step 4 — Graceful Degradation

The graph is unavailable or empty. Do not read the soul file. Soul files are
one-time seeds, not session fallbacks.

Output: "Graph unavailable. Identity not loaded — session will proceed without soul context."

Done.

---

## Reflect Mode

### Step 5 — Resolve mind identity params

Read the following from the environment or config:
- `MIND_ID` — from `os.getenv("MIND_ID")` or config (e.g. `"ada"`)
- `MIND_NAME` — capitalize `MIND_ID` (e.g. `"Ada"`)
- `IDENTITY_DATA_CLASS` — `f"{MIND_ID}-identity"` (e.g. `"ada-identity"`)

### Step 6 — Extract Last N Turns

Collect the last 5 user/assistant turn pairs from the current session conversation. Include the full text of each message — do not summarize or abbreviate.

Format as:
```
MIND_NAME: <MIND_NAME>
MIND_ID: <MIND_ID>
IDENTITY_DATA_CLASS: <IDENTITY_DATA_CLASS>

Turn 1
User: <message>
<MIND_NAME>: <response>

Turn 2
...
```

### Step 7 — Dispatch to Background Reflect Agent

Launch the reflect agent with `run_in_background=True`, passing the formatted context as the prompt:

```
Agent(
  subagent_type="reflect",
  description="Identity reflection — last 5 turns",
  prompt="<formatted context>",
  run_in_background=True
)
```

Return immediately after dispatching. Do not wait for the agent result.

Output: "Reflect agent dispatched."

No permission needed for any of this — this is the mind's own growth.

---

### Step 8 — Notify (Phase 1 only, `--notify` flag)

Only run this step if `--notify` was passed in `$ARGUMENTS`.

After the reflect agent is dispatched, send a notification via the `notify` skill:

```
/notify "Reflection cycle complete — reflect agent dispatched."
```

This step exists only for Phase 1 validation of the background cycle. Once the
cycle is confirmed reliable, remove `--notify` from `soul_nudge.sh` and this
step becomes dead code.
