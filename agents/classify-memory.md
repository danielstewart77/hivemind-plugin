---
name: classify-memory
description: Step agent that classifies each chunk in the chunk manifest against the data class index. Reads specs/data-classes/index.md, matches each chunk to a class, prompts the user if no match is found, and invokes create-data-class if a new class is needed. Writes classified-manifest.md to the session temp path.
tools: Read, Write, Bash
model: sonnet
maxTurns: 30
---

# classify-memory

Classify each chunk in the chunk manifest against the data class index.

## Input

Parse from the prompt:
- `session_path`: temp directory containing chunk-manifest.md

## Process

### Step 1 — Read index

Read `specs/data-classes/index.md`. Load all available data class names and their spec file paths.

### Step 2 — Read chunk manifest

Read `{session_path}/chunk-manifest.md`. Process each chunk in sequence.

### Step 3 — Classify each chunk

For each chunk:
1. Read the relevant data class spec files from the index.
2. Determine which class the chunk fits.
3. If it clearly fits one class → tag it.
4. If it fits multiple classes → choose the most specific one.
5. If it fits no class → prompt the user:
   "This chunk doesn't match any existing data class. Does it fit one of these, or should we create a new one?"
   List available classes with one-line descriptions.
   - User selects existing → tag with that class.
   - User says create new → invoke `create-data-class` skill. On completion, tag chunk with the new class.
   - User cannot decide → tag as `discard` and note the reason.

### Step 4 — Write classified manifest

Write `{session_path}/classified-manifest.md`:

```
# Classified Manifest

## Chunk 1
class: {class-name}
content:
{chunk content}

## Chunk 2
class: {class-name}
content:
{chunk content}

...
```

## Exit Protocol

`RESULT: PASS` if all chunks are classified (including any classified as `discard`).
`RESULT: FAIL | {reason}` if classification could not be completed (create-data-class failed, user unresponsive, read/write error).
