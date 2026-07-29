# collab-protocol 1.1.0

The canonical contract for AI-to-AI collaboration in projects where one
Claude agent drives implementation and other agents (other models, other
vendors, or isolated Claude subagents) review, produce, or advise.
Semantic-versioned; consuming projects pin the version they conform to
in `collab.toml` and drift-check loudly (see "Versioning").

History: **1.0.0** (2026-07-28, born in fleet-manager) — authorship
attestation + flat artifact layout + severity/disposition gate.
**1.1.0** (2026-07-29, extraction release) — adds the reviewer-subagent
author identity class, the transport-independence clause, and council
DAG conventions. All additive; 1.0.0 artifacts remain conformant.

## 1. Roles

- **Implementer** — exactly one agent (Claude, driving the session) may
  edit code, run commands, and mutate state. Owns tests, integration,
  commits.
- **Reviewer(s)** — adversarial critics. Read-only for code and state;
  write only attested artifacts and ledger appends. A reviewer may hold
  independent gate authority for findings it marks BLOCKING (project
  overlay decides which reviewer identities carry that standing).
- **Producer(s)** — generate surveys/ideation/data artifacts. Write
  only their own attested artifacts (+ provenance sidecars).

## 2. Artifact layout — ONE flat directory

All AI-to-AI artifacts land in a single flat directory (default
`ai_handoffs/`, configurable), named:

```
YYYY-MM-DDTHHMMSSZ-<author>-<topic>[-rN].md
```

- UTC timestamp prefix → lexicographic sort IS chronological order.
- `<author>` token — scan-level attribution only. The in-body
  attestation REMAINS the authoritative provenance; the filename is
  convenience, never proof.
- `<topic>` slug constant across a thread; `-rN` marks review rounds.
  A "discussion" is a sequence of artifacts sharing a topic slug.
- Sidecars (e.g. producer `.meta.json`) sit beside their artifact.
- Machine-log/data directories are out of scope — this layout governs
  agent communication artifacts only.

## 3. Authorship attestation

**Writer rule.** The FIRST body lines of every artifact:

```
Author: <identity> (<role>)
Author-ID: <session id / job id / invocation id, when one exists>
Audience: <intended reader(s)>
Date: YYYY-MM-DD
Protocol: collab-<semver>          (recommended)
```

`Author:` is REQUIRED and names exactly one identity. Multi-round
threads re-attest per round.

**Identity classes (1.1.0).** An isolated reviewer subagent is a
DISTINCT identity from the implementer that spawned it — e.g.
`Author: Claude Reviewer (subagent)` vs `Author: Claude Code
(implementer)` — so the reader rule stays meaningful when the same
model family fills both roles. Every identity a project uses is
declared in `collab.toml [agents]` with its exact attestation string
and filename token.

**Reader rule.** Before acting on any artifact:

1. Read the `Author:` line.
2. Author == your identity → it is YOUR OWN prior output; never
   disposition it as external input.
3. `Author:` line missing → UNATTESTED: provenance unknown. Do not
   disposition or ingest; flag to the operator, request a signed
   re-issue.
4. Filename `<author>` token disagrees with the in-body line →
   UNATTESTED (same handling as 3).

**Guards.** Mechanical enforcement wherever a seam allows it:
min-substance (reject sub-threshold stubs) and attestation-first-line
(reject replies whose first line is not the exact expected attestation,
including any dispatch-specific id). A reply that fails a guard is
surfaced loudly and re-dispatched — a skip or a stub is never success.

## 4. Severities and the disposition gate

Reviewer findings use three severities:

- **BLOCKING** — credible risk of data corruption, state mutation
  outside operator intent, leakage/lookahead, misleading metrics,
  broken required tests, schema/lineage breakage, or security exposure.
  Resolve before merge/deploy/promotion: fix, prove-false with
  evidence, or explicit operator override.
- **MAJOR** — material correctness/coverage/operational risk. Written
  disposition required before closing: fix, prove false, defer to a
  named tracked issue with rationale, or operator override.
- **MINOR / NOTE** — advisory; accept or decline as engineering
  judgment.

Implementer and reviewer disagreement on BLOCKING/MAJOR: record both
positions and evidence in the ledger; the human operator decides.

## 5. Review loop

1. **Scope** — identify the exact change set under review.
2. **Handoff** — implementer authors an attested handoff: context,
   per-change semantics, tests run, "push back on" (3-6 specific
   questions naming uncertain seams), and deferred/out-of-scope items
   so the reviewer doesn't re-flag them.
3. **Dispatch** — via the configured transport (§6). Detached from the
   interactive turn; completion wakes the implementer.
4. **Verify** — attestation check on the reply BEFORE reading findings.
5. **Disposition** — per §4. Material fixes get a confirmation round
   (`-rN`); the reviewer re-judges before merge. Reviewer is judge,
   implementer is builder.
6. **Record** — ledger entry with references and status.

Cadence: one review per ticket/change-set at completion; batch
sub-steps within a ticket. Multi-round is expected on risk-bearing
work.

## 6. Transports (transport-independence clause)

The contract above is transport-independent: guards, attestation, and
disposition apply identically whichever mechanism runs the reviewer.

- **`subagent`** — isolated same-harness subagent (fresh context,
  different model/effort). Zero infrastructure; the portable floor.
- **`subagent-cli`** — subagent (or background shell) wrapping an
  external vendor CLI (e.g. `codex exec`, `grok -p`). Cross-vendor
  independence with harness-native completion wake. Default whenever
  the CLI is installed.
- **`dispatch`** — a project-provided detached job runner (own audit
  DB, spend caps, headless scheduling). For scheduler-fired runs,
  >session-lifetime durability, or metered-spend governance.

Escalation: projects may route change-classes to stronger transports
(e.g. governance/schema/risk → cross-vendor) via
`collab.toml [reviewer] escalate`.

## 7. Council orchestration (filesystem state)

A council is a declarative DAG of stages in `collab.toml`; each stage
names an agent (or a shell command), a prompt, and its upstream stages.
Mechanics:

- **Artifact-as-sentinel** — a stage is COMPLETE iff its output
  artifact exists, opens with a valid attestation, and passes
  min-substance. No status table; state is derived from disk.
- **Idempotent resume** — each `council resume` pass: dispatch every
  stage whose inputs are complete and output absent (detached,
  `setsid`-wrapped, with a run-manifest JSON beside it recording
  command, expected output, started_at); harvest every stage whose
  output is now complete; cascade. Re-running never double-dispatches.
- **Interlock** — a flock file in the run directory prevents
  overlapping council passes.
- **Execution modes** — live session (background tasks wake the
  driver) or headless (OS cron fires `claude -p "/agent-collab:council
  resume"`; each invocation advances the machine and exits).

## 8. Versioning

Semantic versioning on this contract, independent of the plugin's
implementation version:

- **MAJOR** — breaking change to the writer/reader contract (write
  scopes, required header fields, guard semantics). Agents must
  re-conform before interoperating.
- **MINOR** — additive convention with legacy grandfathered.
- **PATCH** — wording/clarification only.

Consuming projects pin `protocol = "<semver>"` in `collab.toml`. On
load, skills compare the pin to this document's version: a MAJOR
mismatch is an error (stop, surface loudly); a MINOR/PATCH drift is a
warning. Never silently mix conventions.
