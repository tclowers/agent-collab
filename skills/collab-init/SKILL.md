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
   follow [migration-v2.md](../../reference/migration-v2.md) for 1.x, or
   [review-routing.md](../../reference/review-routing.md) to adopt dynamic roles
   in a 2.x project. The upgrade
   request is authorization; do not require duplicate approval.
2. New projects default to dynamic roles: the review-handoff initiator is the
   writer, and an explicit reviewer request takes precedence over the ordered
   preferred pair `["claude", "codex"]`. Do not ask users to permanently assign
   writer/reviewer roles. Preserve a requested preference list or an explicitly
   requested fixed arrangement. Follow review-routing.md for model aliases and
   known-family exclusions. Declare actual identities and provider/models for
   multi-provider hosts; OpenCode reads AGENTS.md directly.
3. Create collab.toml from templates/collab.toml.example, keeping applicable
   agents and paths. Dynamic mode uses `roles.preferred_reviewers` and no static
   implementer/reviewer pins. Fixed mode retains matching `[roles]` assignments
   and `[reviewer].identity`. Set the protocol pin and requested one-round review
   unless another policy was chosen. Do not enable council stages or
   schedules without a specified task and dependencies.
4. Create the handoff directory and ledger if absent. Ledger entries record
   date, Agent, scope, artifacts, findings/dispositions, and next owner.
5. Generate AGENTS.md from templates/AGENTS.core.md. In dynamic mode set
   IMPLEMENTER_NAME to "Review-handoff initiator for this cycle" and
   REVIEWER_NAMES to "explicitly requested agent or other preferred agent";
   for fixed mode name the configured agents. Preserve an existing
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
   in collab.toml. Use `scripts/resolve_review.py` to check the preferred hosts
   in dynamic mode; selection checks do not dispatch agents. Report routing,
   policy, protocol, and capability gaps.
   Initialization alone does not dispatch review.
