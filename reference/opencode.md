# OpenCode adapter

OpenCode is a host for different model providers. Record its actual
`provider/model` and configured variant in each dispatch. Different CLI
names alone do not satisfy a cross-vendor review requirement. Preserve
the project's selected model; ask only if the choice is unresolved.

## Installation and discovery

From a stable checkout of this repository:

```bash
python3 scripts/install_opencode.py
```

The installer uses `OPENCODE_CONFIG_DIR`, otherwise
`${XDG_CONFIG_HOME:-~/.config}/opencode`. It creates a whole-bundle symlink
under `skills/agent-collab`, six namespaced command links under `commands/`,
and a distinct `agents/agent-collab-reviewer.md` link. It refuses collisions
before installing anything and leaves opencode.json/jsonc and existing
agents untouched. Re-running is idempotent; source edits are visible through
the links. Restart OpenCode after changing skills/agents/commands.

For a project-only installation, use `--config-dir /path/to/project/.opencode`.
Symlinks require filesystem support. Do not copy individual skill folders:
their shared references, templates, and scripts would be lost.

Check from the intended project directory:

```bash
opencode debug skill
opencode debug agent agent-collab-reviewer
opencode debug config
```

Confirm all six skills, `/agent-collab:<skill-name>` command entries, and
the reviewer are present. Resolved config can include private provider
settings; inspect locally without pasting the full output into artifacts.
Project configuration may override global definitions. The packaged reviewer
uses `mode: all` for native tasks and CLI runs, denies tools by default,
and permits only read/glob/grep/list. Confirm effective permissions before
dispatch; a missing or overridden reviewer is a capability gap. Tool
permissions do not sandbox installed plugins or trusted project startup code.

## Reviewer dispatch

Declare a project-specific OpenCode identity in collab.toml. Example shape:

```toml
[agents.opencode]
token = "opencode"
attestation = "Author: OpenCode ({role} {run_id})"
model = "provider/model-chosen-for-this-project"
cli = "python3 /absolute/path/to/agent-collab/scripts/opencode_run.py --project {repo} --model {model} --events {output}.events.jsonl"
output_mode = "stdout_redirect"
blocking_authority = true
```

Replace the example path/model during initialization. `{model}` comes from
the selected agent configuration; `{output}` is the per-dispatch temporary
artifact path. Resolve all runtime placeholders before execution and pass
arguments as an array, or quote each substituted value individually.
Set `[roles].reviewers` and `[reviewer].identity` together when selecting it.
Keep other configured reviewers and existing policy as requested.

Send the complete reviewer contract and reference/reviewer.md on stdin.
Use the project timeout for the wrapper's `--timeout`; use `--variant` only
when a specific variant is configured. Do not use `--continue`, `--session`,
`--attach`, `--auto`, or share flags. Each dispatch starts a separate session.

The wrapper retains JSON events containing the OpenCode session ID, selects
only the final normally completed message, and excludes earlier tool-step
commentary. Capture stderr separately. After successful wrapper exit,
validate the temporary reply using verify_artifact.py and atomically publish
it. Retain the event log with the dispatch record. No text or identity is
rewritten to make validation pass. The protocol remains 2.0.0.

## Driver, one-off jobs, and councils

OpenCode can run collab-init, handoff, dispatch-review, dispatch-job, council,
and collab-audit with the same role, attestation, and review policy as other
hosts. It may call configured Claude/Codex CLIs through the host guide.
Initialization and writing a handoff do not themselves authorize dispatch.

Use dispatch-job for a commissioned standalone production/research task or
an implementation task with an explicit writer handover. The wrapper also
supports `--agent <configured-agent>` for these jobs; the default reviewer
cannot execute commands or edit implementation. Use a separate agent entry
and appropriate capabilities for a worker. Do not broaden the reviewer.

For a council OpenCode stage, use the same wrapper and `stdout_redirect`.
Its event log and outer exit-code file belong to that run; a successful
wrapper exit is necessary but the artifact guard and manifest checks are
still required. Producer and implementation stages require their own scoped
configuration. OpenCode may drive run/resume/status against the same manifests.
The existing POSIX runtime requirements and one-writer rule still apply.
No schedule is created implicitly, and no JavaScript hook plugin is required.

## Upstream references

- [Skills and discovery](https://opencode.ai/docs/skills/)
- [Command templates](https://opencode.ai/docs/commands/)
- [Agent modes and permissions](https://opencode.ai/docs/agents/)
- [CLI run and JSON output](https://opencode.ai/docs/cli/)
