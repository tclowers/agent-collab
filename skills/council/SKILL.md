---
name: council
description: Run, resume, or report the multi-agent council DAG declared in collab.toml — filesystem-state orchestration where attested artifacts are the completion sentinels. Use when the user says "run the council", "resume the council", "council status", or a scheduled invocation fires "/agent-collab:council resume".
---

# council — filesystem-state DAG orchestration

State model: NO database. A stage is COMPLETE iff its output artifact
exists in the handoffs dir, opens with the stage agent's exact
attestation, passes `guards.min_bytes`, AND its run is exit-verified:
the manifest's sibling exit-code file records 0 (the dispatch wrapper
captures it — see Dispatch). Atomic rename alone is not proof of success. Existence + attestation + size
alone is race-prone against streaming writers. A stage is IN-FLIGHT
iff a run-manifest exists in `council.run_dir` without exit-verified
completion. Everything is re-derived from disk on every invocation —
resume uses the retained manifests. A crash during dispatch may leave an
ambiguous starting state; investigate it before retrying.

Read [protocol](../../reference/protocol.md) and [host adapters](../../reference/hosts.md).
Resolve plugin resources relative to this skill and project paths from
collab.toml. Accept run/resume/status as natural-language arguments.
If collab.toml or council stages are absent, report not configured without
creating anything. Check the protocol pin before execution.
Before run/resume, validate an acyclic dependency graph, existing prompt
files, declared agents, unique output paths, and the required POSIX runtime.
For a new cycle require fresh output paths; never reuse existing artifacts
as new results or overwrite them. Do not dispatch when those checks fail. Preserve the actual host's permissions.

## `status`

Read `collab.toml [council]`, list every stage as
COMPLETE / IN-FLIGHT (manifest age, pid liveness via `kill -0`) /
READY (inputs complete, not dispatched) / WAITING (inputs incomplete),
with artifact paths. Read-only.

## `run` / `resume` (same verb; `run` starts a new cycle id)

1. **Interlock**: take a flock on `<run_dir>/lock` (non-blocking). If
   held, report "council pass already running" and stop — never
   overlap passes.
2. **Harvest**: for each stage with a manifest, check its expected
   output against the completion rule and run scripts/verify_artifact.py
   with expected identity, dispatch ID, and captured exit status. Never
   accept a stale/partial artifact. Complete → mark the manifest harvested and retain it with exit status
   and dispatch identity for future validation. Manifest older than the stage timeout
   with no running process and no valid completed output → report FAILED loudly with the
   manifest contents; do not silently re-dispatch a failed stage
   without telling the user.
3. **Dispatch**: for each stage whose `after` inputs are all complete
   and whose output is absent and un-dispatched:
   - Resolve the prompt file, stage role, fresh run ID, and attestation
     placeholders; inject upstream artifact paths and the output contract (exact attestation line + output path — same
     contract as dispatch-review).
   - `agent` stages: run the agent's `cli` template `setsid`-wrapped as
     a detached background Bash command (survives this session; next
     resume harvests it), capturing the exit code:
     using a wrapper script and safely quoted arguments, never raw prompt
     interpolation. For
     `output_mode = "stdout_redirect"` runners, redirect to a temp file
     and validate then `mv` into place on success (atomic). For file-argument
     runners also assign a temporary output path, then validate and publish.
     Write a starting manifest before launch, then atomically update the PID
     and process-start identity returned by launch: {stage, cycle,
     cmd, expected_output, output_mode, expected_author, run_id, started_at, pid,
     timeout_sec}.
   - `shell` stages: require exit 0 and their configured output validation
     rather than an AI author header. Run the `command` template (foreground if quick,
     background if long) — these are the project's own ingest/gate
     steps living in the same DAG.
4. **Cascade**: after dispatching, re-check — anything that completed
   synchronously unlocks its dependents within the same pass.
5. **Report**: stages harvested / dispatched / waiting / failed, and
   whether another resume is expected (any IN-FLIGHT remaining). In a
   live session, use the actual host's wait/completion tools. Do not assume
   automatic background wake. Headless drivers exit after durable dispatch;
   a separately configured resume advances the run.

## Scheduling

Running a council does not create a schedule. For a requested schedule,
follow the host guide: Codex app automation for ongoing app tasks, or a
separately authorized headless deployment. Claude Code, Codex, and OpenCode may
invoke resume against the same manifests. Keep unchanged monitoring quiet.
