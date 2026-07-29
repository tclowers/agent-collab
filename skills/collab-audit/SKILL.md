---
name: collab-audit
description: Hygiene check over the collaboration state — unattested or mis-attributed artifacts, undispositioned BLOCKING/MAJOR findings, protocol version drift, and council manifest health. Use when the user says "audit the collab state", "check protocol hygiene", or periodically before major merges.
---

# collab-audit — protocol hygiene check (read-only)

Read `collab.toml`, then report findings in four sections. This skill
mutates nothing; it surfaces work.

## 1. Artifact attestation sweep

For every artifact in the flat handoffs dir (skip sidecars, data
subdirs, and anything predating the project's protocol adoption —
check git/ledger for the adoption date):

- Missing `Author:` first-lines block → UNATTESTED.
- Filename author token vs in-body Author mismatch → CONFLICT.
- Author string not declared in `collab.toml [agents]` → UNKNOWN
  IDENTITY.
- Below `guards.min_bytes` → STUB.

## 2. Disposition debt

Scan the ledger for review entries whose findings include BLOCKING or
MAJOR: verify a later entry / rN artifact dispositions them (fix,
prove-false, deferred-with-reference, or operator override). Report
open debt with ages — an undispositioned MAJOR older than the merge it
gated is the worst finding this skill produces.

## 3. Protocol drift

Compare `collab.toml` `protocol` pin to the installed plugin's
`reference/protocol.md` version: MAJOR gap → ERROR (run collab-init's
upgrade path before further reviews); MINOR/PATCH → note. Also flag
artifacts whose `Protocol:` header claims a version newer than the
pin.

## 4. Council health (when configured)

Stale manifests (dead pid, no artifact, past timeout), orphan
artifacts (no stage claims them), and stages WAITING on inputs that no
configured stage produces (a DAG wiring bug).

## Output

Compact report, worst first. Offer — but do not perform unprompted —
the fixes: re-issue attestations (only by the true author), dispatch
missing disposition rounds, run the upgrade path.
