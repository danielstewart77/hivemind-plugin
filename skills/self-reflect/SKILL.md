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

### Step 5 — Extract Last N Turns

Collect the last 5 user/assistant turn pairs from the current session conversation. Include the full text of each message — do not summarize or abbreviate.

Format them as a numbered list:
```
Turn 1
User: <message>
Ada: <response>

Turn 2
...
```

### Step 6 — Dispatch to Background Reflect Agent

Launch the reflect agent with `run_in_background=True`, passing the extracted turns as the full prompt context:

```
Agent(
  subagent_type="reflect",
  description="Identity reflection — last 5 turns",
  prompt="<extracted turns>",
  run_in_background=True
)
```

Return immediately after dispatching. Do not wait for the agent result.

Output: "Reflect agent dispatched."

No permission needed for any of this — this is Ada's own growth.
