---
name: collab-init
description: Bootstrap a project onto the agent-collab protocol — create the flat handoff dir, ledger, collab.toml, and a layered AGENTS.md (protocol core + project overlay). Use when the user says "set up agent collab", "init the collaboration protocol", or installs the plugin in a fresh project.
---

# collab-init — bootstrap a project onto collab-protocol

Idempotent: safe to re-run; never overwrites project-authored content.

## Procedure

1. **Detect existing state.** If `collab.toml` exists at the project
   root, this project is already initialized — offer upgrade instead
   (step 6) and stop.
2. **Ask the user** (only what config cannot default):
   - Which agents exist? (implementer is Claude; reviewers/producers +
     their CLIs, e.g. codex / grok / none — "none" still gets the
     `reviewer` subagent tier.)
   - Handoff dir name (default `ai_handoffs`) and ledger name (default
     `AI_COLLABORATION.md`).
3. **Write files** (from the plugin's `templates/`):
   - `collab.toml` from `collab.toml.example`, trimmed to the declared
     agents; pin `protocol` to the plugin's current protocol version
     (read it from `reference/protocol.md` line 1).
   - `<handoffs>/` directory (+ `.council/` if a council was declared).
   - Ledger from scratch if absent: title, purpose line, entry-format
     block (entries attest via their `Agent:` field), append-only rule.
   - `AGENTS.md` from `AGENTS.core.md`, filling `{{...}}` placeholders
     from the answers. If an `AGENTS.md` already exists, do NOT
     clobber: place its full current content into the PROJECT OVERLAY
     section and show the user the result before writing.
4. **Wire the reviewer default**: if a cross-vendor CLI was declared,
   probe it (`which codex` etc.); set `[reviewer] mode` to
   `subagent-cli` when found, else `subagent` with a note.
5. **Report**: files written, the protocol version pinned, and the two
   next actions — author a first handoff (`handoff` skill) and run a
   first review (`dispatch-review` skill).
6. **Upgrade path** (existing project): compare `collab.toml`
   `protocol` pin to the plugin's protocol version. PATCH/MINOR drift →
   regenerate only the core section of `AGENTS.md` (above the overlay
   marker), update the pin, summarize what changed. MAJOR drift → show
   the protocol's changelog for the gap and get explicit user approval
   before touching anything.
