---
name: dispatch-review
description: Dispatch a commissioned independent review of a handoff, verify its provenance, and record findings and dispositions. Use when the user requests review or an explicit project review policy requires it.
---

# Dispatch review

Read the target project's collab.toml and the plugin's
[protocol](../../reference/protocol.md). Read [host adapters](../../reference/hosts.md)
for the chosen transport. Resolve plugin resources relative to this skill.
Missing configuration is a gap to report, not permission to initialize.
A protocol-major mismatch requires an authorized migration.

## Prepare

1. Establish the exact handoff/revision and review_policy. For a new cycle,
   resolve writer/reviewer using [review-routing.md](../../reference/review-routing.md)
   and `scripts/resolve_review.py`: the initiator writes in dynamic mode, an
   explicit reviewer/model request wins, otherwise select the other preferred
   agent. Retain the resolution in the dispatch record. On resume use recorded
   cycle identities, not the resuming host. Legacy fixed configurations keep
   their assignments. Creating a handoff alone does not request delegation.
   Default: one requested round.
2. Verify the input's attestation and scope. If the current author must fix
   their handoff, use the sibling handoff skill; never sign another agent's
   work. Record any writer handover before claiming ownership of active work.
   The reviewer must be a fresh run independent of the writing session; preserve
   original authorship and check model-family requirements.
3. Read reviewer transport, timeout, sandbox, fallback, and escalation
   settings. A cross-vendor requirement cannot silently fall back to the same
   family. For OpenCode, check the actual provider/model, not just the host
   name. Preserve an explicitly requested model and use its selected agent's
   command, not a stale reviewer.identity. Check supported model override syntax
   in installed help. Never silently substitute a different reviewer/model on
   failure; use an already-authorized compatible route or report the gap.
4. Assign a fresh dispatch ID. Resolve the configured attestation using
   {role} = reviewer, {run_id} = that ID, and {host} = actual host; preserve explicit strings where
   configured. Reviewer attestations must include the dispatch ID. Derive the
   reply filename from the actual author token.
5. Supply the handoff, source scope, exact reply path, expected Author line,
   and [reviewer instructions](../../reference/reviewer.md). Keep a dispatch
   record binding those values to the actual completed agent/process, resolved
   writer and reviewer identities, selection source, and requested/actual models.

## Execute and verify

- subagent: use available native tools and an independent run.
- subagent-cli: use the configured external CLI and output mode. The host
  guide distinguishes Codex output files, Claude stdout, and OpenCode event extraction.
- dispatch: use the existing project runner; watch every terminal state.
  Silence, failed access, and partial output are not success.

Wait using the host's actual tools and keep updates responsive. Validate the
completed reply with scripts/verify_artifact.py as described in the host
guide before accepting it. Nonzero exit, timeout, wrong identity/dispatch,
or undersized output is incomplete/failed review. Diagnose before retrying,
respect the commissioned budget, and preserve a usable handoff if blocked.

## Disposition

Record findings and evidence, then fix, refute, defer, or escalate per the
protocol. Follow confirmation_after_fixes and max_rounds; no automatic
redispatch under the one-round default. Identify the independently reviewed
revision and later implementer checks separately. Append the ledger entry
with real author, artifact links, dispatch ID, and status.
