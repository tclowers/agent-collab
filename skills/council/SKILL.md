---
name: council
description: Run, resume, or report the multi-agent council DAG declared in collab.toml — filesystem-state orchestration where attested artifacts are the completion sentinels. Use when the user says "run the council", "resume the council", "council status", or a scheduled invocation fires "/agent-collab:council resume".
argument-hint: run | resume | status
---

# council — filesystem-state DAG orchestration

State model: NO database. A stage is COMPLETE iff its output artifact
exists in the handoffs dir, opens with the stage agent's exact
attestation, passes `guards.min_bytes`, AND its run is exit-verified:
the manifest's sibling exit-code file records 0 (the dispatch wrapper
captures it — see Dispatch), or the stage's `output_mode` guarantees
atomic write (temp-file + rename). Existence + attestation + size
alone is race-prone against streaming writers. A stage is IN-FLIGHT
iff a run-manifest exists in `council.run_dir` without exit-verified
completion. Everything is re-derived from disk on every invocation —
idempotent by construction; a crashed session loses nothing.

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
   output against the completion rule. Complete → record harvested
   (delete/mark the manifest). Manifest older than the stage timeout
   with a dead pid and no artifact → report FAILED loudly with the
   manifest contents; do not silently re-dispatch a failed stage
   without telling the user.
3. **Dispatch**: for each stage whose `after` inputs are all complete
   and whose output is absent and un-dispatched:
   - Resolve the prompt file; inject upstream artifact paths and the
     output contract (exact attestation line + output path — same
     contract as dispatch-review).
   - `agent` stages: run the agent's `cli` template `setsid`-wrapped as
     a detached background Bash command (survives this session; next
     resume harvests it), capturing the exit code:
     `setsid sh -c '<cmd>; echo $? > <manifest>.exit' &`. For
     `output_mode = "stdout_redirect"` runners, redirect to a temp file
     and `mv` into place on success (atomic) rather than streaming to
     the final path. Write the run-manifest JSON first: {stage, cycle,
     cmd, expected_output, output_mode, started_at, pid,
     timeout_sec}.
   - `shell` stages: run the `command` template (foreground if quick,
     background if long) — these are the project's own ingest/gate
     steps living in the same DAG.
4. **Cascade**: after dispatching, re-check — anything that completed
   synchronously unlocks its dependents within the same pass.
5. **Report**: stages harvested / dispatched / waiting / failed, and
   whether another resume is expected (any IN-FLIGHT remaining). In a
   live session, arm background wake on dispatched processes; headless
   (`claude -p`), just exit — the next scheduled resume advances.

## Scheduling

Live: the session's background-task wake drives the cascade.
Headless: OS cron fires `claude -p "/agent-collab:council resume"` on
the project's cadence. Both modes share identical on-disk state, so
they can be mixed freely.
