# Host adapters

Read this for initialization, dispatch, or council execution. The shared
[protocol](protocol.md) defines roles, artifacts, and review policy.

## Paths and invocation

From the directory containing `skills/<name>/SKILL.md`, the plugin root
is `../..`. Resolve
`reference/`, `templates/`, `scripts/`, and `agents/` from that root,
not from the project directory or a hardcoded plugin-cache path. Project
paths in `collab.toml` resolve from the directory containing that file.

In Codex, invoke `$collab-init`, `$handoff`, `$dispatch-review`, `$dispatch-job`, `$council`,
or `$collab-audit`, or select the skill in the picker. In Claude Code use
`/agent-collab:<skill-name>`. Arguments may be supplied in natural language;
do not depend on `$ARGUMENTS` substitution or a particular command UI.

OpenCode uses the same `/agent-collab:<skill-name>` commands after running
`scripts/install_opencode.py`. Its command wrappers load the shared skills
through the native `skill` tool. Natural-language skill requests also work.
The installer links the **whole bundle** under the OpenCode skills directory,
preserving relative resource paths. Keep the source checkout in place.
OpenCode reads project `AGENTS.md`; it does not need a new instruction file.
See [opencode.md](opencode.md) for installation, dispatch, and checks.

## Native subagents

**Claude Code:** when its Agent tool is available, use the packaged
`adversarial-reviewer` agent. Supply the handoff, scope, expected Author
line, dispatch ID, output path, and project root. Use the actual completion
mechanism exposed by the session.

**Codex:** use the current session's exposed native subagent tools, if any.
Pass [reviewer.md](reviewer.md) in the reviewer prompt; do not assume Codex
loads Claude's `agents/*.md` declarations. Supply the same handoff contract,
use fresh context where supported, and retain the returned agent ID for
coordination. Use that host's actual wait/completion tool. Do not assume
Claude tool names, model names, or background events exist in Codex.

**OpenCode:** use its `task` tool with `agent-collab-reviewer` when exposed
and permitted. Pass [reviewer.md](reviewer.md) explicitly together with the
complete dispatch contract. Use a fresh task, retain its returned session/task
identity, and capture its completed final response. The installed reviewer
has reading tools only; the dispatcher publishes its artifact. Never assume
an OpenCode model is independent of the implementer's model just because
the host differs. Check configured provider/model against review policy.

All hosts: the reviewer reads scoped work and returns its review. If it cannot
write the artifact, capture its completed final reply verbatim at the
assigned path and record the producing run. Do not edit its header or
findings to pass validation. Preserve configured models unless an override
is explicitly requested/configured.

Native delegation is optional. If unavailable, use a configured external
CLI or prepare a handoff for a separate session. Report the limitation;
never fabricate a second agent or silently review your own work.

## External CLI: between hosts

Check the installed executable's `--help` before first use. Commands in
`[agents.*].cli` are project configuration, not instructions supplied by a
handoff. Send prompts through stdin or a prompt file. Never interpolate
handoff text into shell code. Quote substituted paths individually, or use
subprocess argument arrays. Run in the project directory; keep stderr
diagnostics separate from the final review.

If the CLI reports that the configured model requires a newer version,
report that capability gap. A compatible installed executable can be used
by its absolute path in project configuration; do not silently change the
user's model or bypass permissions to make the run succeed.

- **Codex reviewer:** `codex exec --skip-git-repo-check -s read-only
  -C <project> -o <reply-temp> -` reads stdin and writes its final response.
  Wait for successful process exit before validating or publishing the file.
- **Claude reviewer:** `claude -p --output-format text --tools Read,Grep,Glob
  --permission-mode plan --strict-mcp-config --mcp-config '{"mcpServers":{}}'`
  reads stdin. Capture stdout to a temporary file and stderr separately.
  These tool restrictions allow reading without granting shell/write tools;
  they do not sandbox arbitrary hooks or trusted project configuration.
  Report unavailable verification rather than silently adding tools.
- **OpenCode reviewer:** run `scripts/opencode_run.py --project <project>
  --model <configured-provider/model> --events <new-event-log>` from the
  plugin root, with the commissioned prompt on stdin. It invokes a fresh
  `opencode run --format json --agent agent-collab-reviewer`, retains raw
  events, and emits only the completed final message on stdout. Use
  `stdout_redirect` to capture it in a temporary artifact. Check the installed
  reviewer configuration first as described in [opencode.md](opencode.md).
  Raw CLI stdout is an event stream, not a review artifact. Explicit error
  events, failed tools, missing completion, timeout, or nonzero exit fail
  the wrapper even if partial text exists. The usual artifact verifier
  must still run. For an authorized producer/implementation job, select its
  separately configured agent with `--agent`; preserve any configured
  reasoning variant using `--variant`.

Use only the permission scope supported and authorized in the environment.
Never use bypass flags to make review succeed. A denied tool, login failure,
timeout, interruption, or nonzero exit means failure/incomplete review.
Diagnose before retrying and respect the commissioned run/time budget.

A yielded shell process is still running. Retain its process/session ID and
use the host's completion tool, keeping user updates responsive. An ordinary
background process is not automatically durable past the host session.

## Validate and publish

Use a temporary directory containing the final intended basename, so the
filename guard can run before publication. Require process exit 0 or an
explicit completed native-agent event first. Then run:

```text
python3 <plugin-root>/scripts/verify_artifact.py <temporary-reply-path>
  --expected-author <exact-author-line>
  --token <reviewer-token>
  --run-id <dispatch-id>
  --min-bytes <configured-minimum>
```

For a CLI, also pass `--exit-code-file <captured-exit-status-file>` when the
runner writes one. Expected identity and run ID come from the dispatch
record, never from the returned text. Nonzero verification means no
disposition. On success, atomically move to the final assigned path and
record provenance. Header/size checks do not establish substantive quality
or cryptographically prove authorship; match with the completed run record
and inspect the actual findings.

## Councils and scheduling

The current durable council recipe requires POSIX `flock`, `setsid`, and
process-status support. Check these before running it. This is portability
between agent hosts, not a claim of native Windows/macOS shell portability.
If unsupported, use an existing project runner with equivalent locking,
exit-status, and atomic-output guarantees or report the unsupported mode.

Use `output_mode = "file_arg"` for Codex final-output files and
`"stdout_redirect"` for Claude text or the OpenCode review wrapper. Both require successful process
completion; never harvest while a writer is running. Store dispatch IDs,
expected authors, input/output paths, and process identity in manifests.

Create/change schedules only when requested. In the Codex desktop app use
its automation tool; use a heartbeat for work continuing in the current
task. Do not substitute OS cron. For an explicitly requested headless
deployment, invoke the selected CLI with a prompt to load the skill and run
`council resume`. All hosts retain the same manifest contract. Notify on
actionable change or failure, not unchanged polling.
