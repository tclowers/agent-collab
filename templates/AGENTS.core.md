# AGENTS.md — Shared Instructions for All AI Agents

<!-- agent-collab core (collab-protocol {{PROTOCOL_VERSION}}). Generated
     by the collab-init skill; the PROJECT OVERLAY section at the bottom
     is yours — everything above it tracks the plugin's protocol and is
     regenerated on protocol upgrades. -->

Read these shared instructions with the project overlay and the current
user request. User instructions take precedence over protocol defaults.

## Agent roles (strict)

- **{{IMPLEMENTER_NAME}} (implementer)** — the ONLY agent that edits
  code or mutates project state for the agreed scope. Read-only commands
  are available to reviewers. Owns tests, integration,
  authorized commits. Orchestrates commissioned dispatches to reviewers and producers.
- **Reviewers** ({{REVIEWER_NAMES}}) — strictly read-only for code and
  state. Allowed writes: attested artifacts in the flat handoff
  directory (own author token only) and ledger appends.
- **Producers** ({{PRODUCER_NAMES}}) — write only their own attested
  artifacts + provenance sidecars in the flat handoff directory.

Resolve roles per `collab.toml [roles]`. In dynamic mode the review-handoff
initiator is writer; an explicit reviewer request wins, otherwise choose the first
other eligible `preferred_reviewers` agent. Use the plugin's review-routing guide
and resolver, record the choice, and preserve it on resume. Absent mode or fixed
mode retains configured assignments. No permanent pairing is needed in dynamic
mode. Record writer handovers and unfinished work explicitly.
Historical authorship does not change with roles. A role swap does not turn
an author's own previous work into independent review.

## Handoff layout — ONE flat directory

All AI-to-AI artifacts land in `{{HANDOFFS_DIR}}/`, named
`YYYY-MM-DDTHHMMSSZ-<author>-<topic>[-rN].md`. UTC timestamp prefix →
lexicographic = chronological. `<author>` token gives scan-level
attribution; the in-body attestation is the authoritative provenance.
Threads share a topic slug; `-rN` marks review rounds.

## Authorship attestation (required on every artifact)

FIRST body lines of every artifact:

```
Author: <identity> (<role>)          # REQUIRED, exactly one declared identity
Author-ID: <session/job/invocation id, when one exists>
Audience: <intended reader(s)>
Date: YYYY-MM-DD
Protocol: collab-{{PROTOCOL_VERSION}}
```

Reader rule — before acting on any artifact: (1) read `Author:`;
(2) compare the actual dispatch/session identity and authorship — your
own work is never independent evidence merely because the role changed; (3) missing → UNATTESTED, do not disposition, request signed
re-issue; (4) filename token vs in-body mismatch → UNATTESTED.

Declared identities and their exact attestation strings live in
`collab.toml [agents]`.

## Review severities and disposition gate

- **BLOCKING** — fix, prove-false with evidence, or operator override
  before merge/deploy/promotion.
- **MAJOR** — written disposition before closing: fix / prove false /
  defer to a named tracked issue / operator override.
- **MINOR / NOTE** — advisory.

Disagreement on BLOCKING/MAJOR: both positions + evidence to the
ledger (`{{LEDGER}}`); the human operator decides.

## Collaboration workflow

1. Read the latest `{{LEDGER}}` entries at session start.
2. Implementer works; reviewers critique via attested artifacts.
3. Follow `collab.toml [review_policy]`. Default: requested review, one
   round, no automatic confirmation after fixes. Do not launch agents just
   because a handoff exists. Record independently reviewed revisions and
   later implementer checks separately.
4. Significant work → structured ledger entry (the entry's `Agent:`
   field is its attestation).

---

## PROJECT OVERLAY (owned by this project — edit freely below)

{{OVERLAY}}
