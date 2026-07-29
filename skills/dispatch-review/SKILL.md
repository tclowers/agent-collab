---
name: dispatch-review
description: Run an adversarial review of a handoff through the configured transport (subagent / subagent-cli / project dispatch), verify the reply's attestation, and drive the disposition loop. Use when the user says "send for review", "dispatch to the reviewer", "/dispatch-review <handoff-path>", or after authoring a handoff.
argument-hint: <handoff-path> [reviewer-identity]
---

# dispatch-review — transport-independent adversarial review

## Setup (all transports)

1. Read `collab.toml`: `[reviewer]` (mode, identity, fallback,
   sandbox, timeout, escalate), `[agents.*]` (attestation strings,
   CLI templates), `[guards]`, `[paths]`.
2. Verify the handoff exists and is attested (reader rule — including
   filename-token match). Unattested → fix it first via the `handoff`
   skill; never dispatch unattested work.
3. **Escalation check**: if the change set touches a class listed in
   `escalate` (governance, schema, risk, ...), require the strongest
   available tier (cross-vendor `subagent-cli`/`dispatch`); if only
   the in-family `subagent` is available, SAY SO to the user before
   proceeding — an escalated class reviewed in-family is a conscious
   operator choice, not a silent fallback.
4. Derive the reply path: `<handoffs>/<fresh-UTC-ts>-<reviewer-token>-
   <topic>[-rN].md` (topic + rN mirror the handoff). Compute the
   expected attestation from the reviewer's `collab.toml` string
   (fill `{run_id}`-style fields with this dispatch's id when the
   template has them).

## Transport: `subagent`

Spawn the plugin's `adversarial-reviewer` agent (background) with: the
handoff path, the change-set scope, the reply path, and the expected
attestation string. Prefer a different model than the session's via the
Agent tool's model override when the project configures one. The
completion notification returns the findings summary.

## Transport: `subagent-cli`

Run the reviewer CLI as a detached background Bash command, built from
the agent's `cli` template + sandbox + the reply path as the output
anchor, with the handoff body as the prompt PLUS an appended output
contract: "FIRST line of your reply must be exactly `<expected
attestation>`; your final message is captured verbatim to `<reply
path>` and IS the deliverable." The harness wakes you when the process
exits — do not poll.

## Transport: `dispatch`

Fill the project's `dispatch_cmd` template and run it; arm the
project's `dispatch_watch` as a background loop that exits on ANY
terminal status (silence is not success). This tier is for
scheduler-fired, >session-lifetime, or spend-capped review runs.

## On completion (all transports — the guards live HERE)

1. **Mechanical verify (MANDATORY before any MAJOR/BLOCKING is
   recorded)** — run an actual command that exits nonzero on failure,
   not an eyeball check:

   ```bash
   reply=<reply-path>; expected='<expected attestation line>'
   [ "$(head -1 "$reply" | tr -d '\r')" = "$expected" ] \
     && [ "$(stat -c%s "$reply")" -ge <min_bytes> ] \
     && case "$(basename "$reply")" in *-<reviewer-token>-*) true;; *) false;; esac \
     && echo VERIFIED || { echo VERIFY-FAILED; exit 1; }
   ```

   A transport whose framework already enforces this mechanically
   (e.g. a dispatch job that rejects unattested replies) satisfies the
   requirement; the portable tiers MUST run it explicitly. On failure:
   the file is NOT a review (unattested / stale / partial / wrong
   dispatch) — do not read findings as verdicts; investigate and
   re-dispatch.
2. **Self-check**: Author == your own identity → your own prior
   output; never disposition it as external review.
3. **Disposition** per the protocol: BLOCKING resolved (fix /
   prove-false / operator override) before merge; MAJOR gets a written
   disposition; MINOR at judgment. After material fixes, author an
   `-rN+1` handoff and re-dispatch — the reviewer re-judges before
   merge; you are the builder, not the judge.
4. **Record**: ledger entry (attested via its `Agent:` field) with
   artifact references and status.
