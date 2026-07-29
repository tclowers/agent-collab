# AGENTS.md — Shared Instructions for All AI Agents

<!-- agent-collab core (collab-protocol {{PROTOCOL_VERSION}}). Generated
     by the collab-init skill; the PROJECT OVERLAY section at the bottom
     is yours — everything above it tracks the plugin's protocol and is
     regenerated on protocol upgrades. -->

This file is the single source of truth for every AI agent working in
this repository. All agents read it at the start of every session.

## Agent roles (strict)

- **{{IMPLEMENTER_NAME}} (implementer)** — the ONLY agent that edits
  code, runs commands, or mutates state. Owns tests, integration,
  commits. Orchestrates dispatches to reviewers and producers.
- **Reviewers** ({{REVIEWER_NAMES}}) — strictly read-only for code and
  state. Allowed writes: attested artifacts in the flat handoff
  directory (own author token only) and ledger appends.
- **Producers** ({{PRODUCER_NAMES}}) — write only their own attested
  artifacts + provenance sidecars in the flat handoff directory.

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
(2) Author == you → your OWN prior output, never disposition as
external; (3) missing → UNATTESTED, do not disposition, request signed
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
3. One review per change-set at completion; confirmation rounds
   (`-rN`) after material fixes — reviewer re-judges before merge.
4. Significant work → structured ledger entry (the entry's `Agent:`
   field is its attestation).

---

## PROJECT OVERLAY (owned by this project — edit freely below)

{{OVERLAY}}
