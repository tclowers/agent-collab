# collab-protocol 2.0.0

The shared contract for AI-to-AI collaboration in Claude Code and Codex.
One configured agent owns implementation for a work cycle; independent
agents review, produce, or advise. Host mechanics live in [hosts.md](hosts.md).
User instructions and authorization take precedence over protocol defaults.
Semantic-versioned; consuming projects pin the version they conform to
in `collab.toml` and drift-check loudly (see "Versioning").

History: **1.0.0** (2026-07-28, born in fleet-manager) — authorship
attestation + flat artifact layout + severity/disposition gate.
**1.1.0** (2026-07-29, extraction release) — adds the reviewer-subagent
author identity class, the transport-independence clause, and council
DAG conventions. All additive; 1.0.0 artifacts remain conformant.
Hardened pre-publication per the Codex extraction review (2026-07-29):
mandatory mechanical verify before material dispositions, exit-verified
council harvest, required per-run subagent markers — folded into 1.1.0,
which was never published without them.

**2.0.0** (2026-09-09) — selectable roles, host adapters, explicit review
policy, and portable reply verification. This changes write-role and review
semantics: migrate 1.x projects deliberately using [migration-v2.md](migration-v2.md).
Existing artifacts retain their original author and protocol; never relabel them.

## 1. Roles

- **Implementer** — exactly one configured agent owns edits and state
  changes for the agreed scope. Either Claude or Codex may fill this role.
  Owns implementation, validation, and authorized integration. Read-only
  commands are available to reviewers; role assignment does not expand
  execution permissions or authorize publishing/commits by itself.
- **Reviewer(s)** — adversarial critics. Read-only for code and state;
  write only attested artifacts and ledger appends. A reviewer may hold
  independent gate authority for findings it marks BLOCKING (project
  overlay decides which reviewer identities carry that standing).
- **Producer(s)** — generate surveys/ideation/data artifacts. Write
  only their own attested artifacts (+ provenance sidecars).

Role assignment lives in `collab.toml [roles]`; `[agents.*]` describes
identity and invocation, not permanent rank. Default: Claude implements and
Codex reviews, unless the current request assigns otherwise. A handover
records the old/new writer, scope, revision, unfinished work, and open
findings before ownership changes. Do not run two writers over the same
scope. An agent's own previous work is not independent review after a role swap.

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
`Author: Claude Reviewer (subagent <run-id>)` vs `Author: Claude Code
(implementer)` — so the reader rule stays meaningful when the same
model family fills both roles. All newly dispatched reviewer attestations MUST
carry a per-run marker (a run/dispatch id): a role label alone is
identity theater, while the marker binds the artifact to exactly one
dispatch — the same dispatch-id echo CLI reviewers carry. Every
newly dispatched review also requires `Author-ID: <dispatch-id>` as its
second line. Every identity a project uses is declared in `collab.toml [agents]` with its
exact attestation string and filename token.

**Reader rule.** Before acting on any artifact:

1. Read the `Author:` line.
2. Compare dispatch/session identity and the current work's authorship.
   Your own output is not independent evidence merely because its role label
   changed. A fresh isolated run may share the model family; it must be
   separately invoked and receive the actual source evidence.
3. `Author:` line missing → UNATTESTED: provenance unknown. Do not
   disposition or ingest; flag to the operator, request a signed
   re-issue.
4. Filename `<author>` token disagrees with the in-body line →
   UNATTESTED (same handling as 3).

**Guards.** Mechanical enforcement wherever a seam allows it:
min-substance (reject sub-threshold stubs) and attestation-first-line
(reject replies whose first line is not the exact expected attestation,
including any dispatch-specific id). A reply that fails a guard is
reported as failed — a skip or a stub is never success. Diagnose before
retrying; respect the requested run/time budget rather than looping blindly.

**Mandatory mechanical verify (1.1.0).** Before a MAJOR or BLOCKING
finding may be recorded or dispositioned, the reply MUST pass a
mechanical verify — a command that exits nonzero on failure — checking
at minimum: first line equals the expected attestation (including any
run/dispatch id), the filename's AUTHOR SEGMENT (the token immediately
after the timestamp prefix — parsed positionally, never a substring
match) equals the reviewer's token, and min-substance.
Use `scripts/verify_artifact.py` from the plugin root; see hosts.md for
arguments and process completion requirements. An attestation is a declared
provenance check, not cryptographic proof of independent execution. Match it
with the dispatch record and completed process/subagent identity.
This applies on EVERY transport: procedural eyeballing is an acceptable
floor only for MINOR/NOTE handling. A transport with a built-in guard
(e.g. a dispatch framework that rejects unattested replies) satisfies
this; the portable tiers run the check explicitly post-reply.

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
3. **Dispatch** — via the configured transport (§6), only for a commissioned
   review or an explicitly configured automatic review policy. Use the host's
   actual completion/wait mechanism; do not assume a background wake exists.
4. **Verify** — attestation check on the reply BEFORE reading findings.
5. **Disposition** — per §4. Use `[review_policy]` for follow-up rounds.
   Default: one requested round, no automatic redispatch after fixes. Record
   what the implementer checked and which revision was independently reviewed.
   Further review occurs when commissioned or explicitly required by the
   project. Never call an unreviewed revision independently approved.
6. **Record** — ledger entry with references and status.

New-project defaults: `trigger = "requested"`, `max_rounds = 1`,
`confirmation_after_fixes = false`. `trigger = "completion"` is opt-in.
The maximum includes confirmation rounds; when the limit is reached, report
unresolved findings and stop dispatching. BLOCKING/MAJOR dispositions still
apply. Existing project policy is preserved during a migration unless the
user changes it; do not silently weaken or expand review requirements.

## 6. Transports (transport-independence clause)

The contract above is transport-independent: guards, attestation, and
disposition apply identically whichever mechanism runs the reviewer.

- **`subagent`** — isolated native subagent, if exposed by the current
  host. Use a distinct run ID. Preserve configured model settings; a model
  override is optional and must be explicitly configured or requested.
- **`subagent-cli`** — subagent (or background shell) wrapping an
  external vendor CLI (e.g. `codex exec`, `grok -p`). Cross-vendor
  independence with process exit and output capture. Installation alone
  does not establish authentication or permissions. Configure both directions
  and report a missing capability; never bypass permission controls to retry.
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
  artifact exists, opens with a valid attestation, passes
  min-substance, AND the runner's completion is exit-verified: the
  run-manifest records a successful runner exit (captured exit code
  0). Publish with atomic temp-file rename only after successful exit
  and verification; atomic rename alone does not prove success.
  Existence + attestation + size alone is race-prone against a runner
  that streams to the output path — a partial file could open validly
  and unlock downstream stages. No status table; state is derived
  from disk.
- **Idempotent resume** — each `council resume` pass: dispatch every
  stage whose inputs are complete and output absent (detached,
  `setsid`-wrapped, with a run-manifest JSON beside it recording
  command, expected output, started_at); harvest every stage whose
  output is now complete; cascade. Re-running never double-dispatches.
- **Interlock** — a flock file in the run directory prevents
  overlapping council passes.
- **Execution modes** — live via the host's supported process/wait tools,
  or a separately configured scheduler invoking the chosen driver. See
  hosts.md. Running a council does not itself create a recurring job.
  `status` is read-only; a missing configuration is not permission to initialize.

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
