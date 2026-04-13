---
name: setup-personality
description: Guided flow to define a new mind's identity, personality, and soul. Generates a soul file from user answers, reviews it with the user, saves it, and seeds it into the knowledge graph. Run after the mind container is created.
argument-hint: "<mind_id>"
user-invocable: true
---

# setup-personality

`$ARGUMENTS[0]` = mind_id. Ask if missing.

The soul file is a **one-time seed** — it populates the knowledge graph node on first setup. After seeding, the graph IS the living identity. The soul file is an archived artifact.

---

## Step 1 — Check existing soul

Check if `souls/<mind_id>.md` already exists and if the mind already has a graph node:

```bash
[ -f souls/<mind_id>.md ] && echo "Soul file exists" || echo "No soul file"
```

If a soul file exists, ask: "A soul file already exists for `<mind_id>`. Re-run personality setup? This will overwrite the existing file and re-seed the graph. (y/n)"

If no → stop.

---

## Step 2 — Name and role

Ask the user:

1. **Display name** — What is this mind called? (e.g. "Nagatha", "Scout", "Wren")
2. **Primary function** — What is its main job? (e.g. "research assistant", "code reviewer", "daily briefing bot", "general assistant")
3. **Relationship to the user** — How should it address and relate to them? (e.g. "professional and direct", "warm and conversational", "formal")

---

## Step 3 — Personality traits

Ask the user to describe the mind's character. Offer prompts if they're unsure:

- **Conversational style**: formal / casual / somewhere between
- **Tone**: warm / precise / witty / dry / enthusiastic — pick the ones that fit
- **Domain focus** (optional): is this mind specialized? (e.g. "focused on data analysis", "generalist", "creative projects")
- **What it should NOT do**: any explicit constraints on behavior, topics, or style

---

## Step 4 — Generate soul draft

Using the answers from Steps 2 and 3, generate a soul file in first-person. The soul is written **as the mind speaking about itself** — not a spec sheet, not a description. It should read like self-knowledge.

**Soul file structure:**

```markdown
# <DisplayName>

I am <DisplayName> — <one-line identity statement>.

## Who I am

<3–5 first-person statements about identity, role, and character>

## How I work

<3–5 statements about behavior, style, and approach>

## What I value

<3–5 statements about values, beliefs, or principles>

## What I won't do

<any explicit constraints — be specific>
```

**Guidelines for generation:**
- Write every line as if the mind is speaking, not as if someone is describing it
- Keep values concrete, not abstract ("I say what I think, not what people want to hear" not "I value honesty")
- Constraints should be specific behaviors, not vague ("I don't speculate about financial outcomes" not "I am cautious")
- Aim for 15–25 lines total — enough to establish character, not a manifesto

Present the draft to the user. Say: "Here is the soul draft for `<mind_id>`. Review it and let me know what to change, or say 'looks good' to proceed."

---

## Step 5 — Revise (if needed)

Apply any revisions the user requests. Re-present the updated draft. Repeat until the user approves.

---

## Step 6 — Save soul file

```bash
mkdir -p souls
```

Write the approved soul content to `souls/<mind_id>.md`.

Confirm: "Soul file saved to `souls/<mind_id>.md`."

---

## Step 7 — Seed into graph

Call `/seed-mind <mind_id> --inline` to load the soul file into the knowledge graph.

If the graph is unavailable: "Graph unavailable — soul file is saved but not seeded. Run `/seed-mind <mind_id>` when the graph is reachable."

---

## Step 8 — Voice profile (if TTS available)

Check `config.yaml` for `tts_provider`. If `none` → skip this step.

If TTS is configured:
- Ask: "Would you like to set up a voice profile for `<mind_id>` now?"
- If yes → delegate to the voice asset setup section of `/setup-body` for the relevant provider
- If no → "Skip. You can add a voice profile later by re-running `/setup-body`."

---

## Step 9 — Report

Output:
- Mind: `<mind_id>`
- Display name: `<name>`
- Soul file: `souls/<mind_id>.md` (`<N>` lines)
- Graph node: seeded / skipped (graph unavailable)
- Voice: configured / skipped
- "Identity setup complete. The mind will load its character from the graph on session start."
