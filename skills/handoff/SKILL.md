---
name: handoff
description: Author an attested handoff artifact in the flat handoff layout (house style — context, change semantics, tests, push-back-on asks, deferred items). Use when the user says "write a handoff", "prep this for review", or before dispatch-review when no handoff exists yet.
---

# handoff — author an attested handoff artifact

Read [protocol](../../reference/protocol.md). Resolve templates and other
plugin resources relative to this skill's plugin root. Project paths resolve
from collab.toml. A missing config is not permission to initialize.

## Procedure

1. Read `collab.toml` (paths, roles, attestation, protocol pin). Use the
   actual writer identity and a fresh invocation ID. In dynamic mode the
   review-handoff initiator owns this cycle; follow
   [review-routing.md](../../reference/review-routing.md), retaining active-cycle
   ownership on resume and recording any handover. A handoff can be written
   before a reviewer is available; it never dispatches by itself. Resolve {role}, {run_id},
   and {host} when present in the configured attestation. Never relabel
   another agent's work or change historical headers after a role swap.
2. Derive the path: `<handoffs>/<UTC-ts>-<your-token>-<topic>[-rN].md`
   — `date -u +%Y-%m-%dT%H%M%SZ`; topic = short kebab slug of the
   change set; `-rN` only when this continues an existing thread (same
   topic slug as the prior rounds).
3. Fill the plugin's `templates/handoff.template.md`:
   - Attestation header first: Author (your exact `collab.toml`
     string), Author-ID (session id), Audience, Date, Protocol pin.
   - **Context** — what prompted this; ticket/incident refs.
   - **Changes** — per file/module, the SEMANTICS of the change (what
     behavior is different and why), not a diff restatement.
   - **Tests** — what ran, counts, what didn't and why.
   - **Push back on** — 3-6 SPECIFIC questions naming the seams you
     are least sure of. Name the failure mode you want attacked; never
     "is this good?".
   - **Deferred / don't re-flag** — known gaps with tracked
     issue/rationale, so the reviewer spends attention on live seams.
4. Verify before finishing: first line matches your declared
   attestation exactly; filename token matches; every file named in
   Changes actually exists in the change set (and nothing touched is
   silently omitted — reviewers treat silent scope as a finding).
5. Report the artifact path. If the user asked for review in the same
   breath, chain straight into the `dispatch-review` skill.
