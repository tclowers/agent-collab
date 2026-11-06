---
name: dispatch-job
description: Dispatch a requested one-off research, production, or implementation job to a configured agent, verify its artifact, and record the outcome. Use dispatch-review for independent review and council for a dependency graph.
---

# Dispatch a one-off job

Read the project's instructions, collab.toml, and the shared
[protocol](../../reference/protocol.md) and [host adapters](../../reference/hosts.md).
Missing agent configuration is a gap to resolve; do not invent a model,
transport, or permission grant. A review request uses the sibling
dispatch-review skill and its review policy. A dependency graph uses council.

1. Establish the requested outcome, target agent, source scope, role,
   permitted writes, completion checks, and run/time budget from the request
   and project configuration. Default a research/production job to an
   artifact-only producer. A request to dispatch work authorizes this job,
   not a recurring schedule or unrelated external action.
2. For implementation, establish an explicit writer handover for the agreed
   scope and pause competing writes until completion or confirmed termination.
   Use an implementation-capable configured command; do not widen the
   restricted reviewer command to make it succeed. An interrupted writer is
   not assumed stopped. Preserve and inspect its changes before taking over.
3. Assign a fresh run ID, resolve the actual agent's attestation with its
   role and run ID, and derive a fresh output path using its author token.
   Give the worker the exact Author and Author-ID lines, output contract,
   task, evidence, allowed writes, and acceptance checks. For OpenCode,
   record provider/model and any configured variant as well as host identity.
4. Record the job's scope, revision, target, model, run ID, expected author,
   output path, and process/session identity. Dispatch using an available
   native agent or configured CLI as described in the host guide. Use a
   fresh context; do not continue an unrelated session. Remain responsible
   for waiting and observing terminal state. Use council or an existing
   durable project runner when the job must survive this session.
5. Require successful completion and run scripts/verify_artifact.py with
   the expected author, token, run ID, and configured minimum size before
   publishing. Apply the same identity and exit guards to producer/worker
   artifacts as reviews. Capture final responses verbatim; never repair
   another worker's attestation. A valid header is not task acceptance:
   inspect the deliverable and requested checks separately.
6. Append the outcome, artifact, checks, incomplete work, and returned
   ownership to the ledger. A partial/failed/denied job is incomplete even
   when it produced a plausible artifact. Diagnose before retrying and stay
   within the requested budget. Do not label production work an independent
   review or automatically commission another agent.
