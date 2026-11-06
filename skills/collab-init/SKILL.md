---
name: collab-init
description: Initialize or explicitly upgrade shared Claude Code, Codex, and OpenCode collaboration instructions, role configuration, handoff storage, and a ledger in a project.
---

# Initialize collaboration

Read applicable project instructions, the plugin's
[protocol](../../reference/protocol.md), and [host guide](../../reference/hosts.md).
Resolve templates from the plugin root, not the target working directory.

1. Inspect collab.toml, AGENTS.md, CLAUDE.md, and the ledger. If initialized,
   report configuration without overwriting it. For a requested upgrade,
   follow [migration-v2.md](../../reference/migration-v2.md). The upgrade
   request is authorization; do not require duplicate approval.
2. Infer roles from the request and existing records. New-project defaults
   are Claude implementation and Codex review when no host is assigned.
   Any supported host can fill either role. If the user asks the current
   session to implement, use its actual host as implementer and preserve a
   requested reviewer; otherwise select an available independent reviewer
   consistent with project policy. If OpenCode is assigned a role, declare its
   identity and actual provider/model separately; the host name is not a model
   vendor. OpenCode reads AGENTS.md directly. Ask only about unresolved material
   choices, not defaults already settled by context.
3. Create collab.toml from templates/collab.toml.example, keeping applicable
   agents and paths. Match `[reviewer].identity` to the selected reviewer
   in `[roles]`; role changes must update both fields. Set the protocol pin and requested one-round review
   unless another policy was chosen. Do not enable council stages or
   schedules without a specified task and dependencies.
4. Create the handoff directory and ledger if absent. Ledger entries record
   date, Agent, scope, artifacts, findings/dispositions, and next owner.
5. Generate AGENTS.md from templates/AGENTS.core.md. Preserve an existing
   non-generated file intact in the project overlay. Preserve overlays on
   upgrade. Create a minimal CLAUDE.md pointer to AGENTS.md if absent; for an
   existing CLAUDE.md add a reference only if missing, retaining all content.
6. Probe configured reviewer CLIs without launching them. A missing binary
   is a capability gap, not permission to bypass controls or invent review.
   Configure an available fallback only if it meets the user's independence
   requirements. Do not claim credentials were tested by executable lookup.
7. Verify TOML parses, paths agree, and generated project files have no
   unresolved generation placeholders such as `{{OVERLAY}}`. Retain intentional
   runtime placeholders such as `{role}`, `{run_id}`, `{repo}`, and `{output}`
   in collab.toml. Report roles, policy, protocol, and capability gaps.
   Initialization alone does not dispatch review.
