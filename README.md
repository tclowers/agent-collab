# agent-collab

Shared collaboration commands for **Codex, Claude Code, and OpenCode**: initialize a
project, write handoffs, dispatch independent reviews, audit collaboration
records, and run a configured council. Any supported host can own implementation;
roles and review policy live in the project, with one writer per scope.

## Commands

| Task | Codex | Claude Code / OpenCode |
| --- | --- | --- |
| Initialize or migrate | `$collab-init` | `/agent-collab:collab-init` |
| Write a handoff | `$handoff` | `/agent-collab:handoff` |
| Commission a review | `$dispatch-review` | `/agent-collab:dispatch-review` |
| Dispatch a one-off job | `$dispatch-job` | `/agent-collab:dispatch-job` |
| Run/resume/status of a council | `$council` | `/agent-collab:council` |
| Audit records | `$collab-audit` | `/agent-collab:collab-audit` |

Natural-language requests also work. New projects default to requested
reviews, one round, and no automatic review after fixes. Creating a handoff
alone does not commission a reviewer. Existing project policies survive
migration unless the user changes them.

## Install

### Codex

Install from this repository's marketplace:

```bash
codex plugin marketplace add tclowers/agent-collab
codex plugin add agent-collab@agent-collab-marketplace
```

For a local checkout already registered in a personal marketplace, use
`codex plugin add agent-collab@personal` instead.

Open a new Codex task to discover the installed skills. Then use
`$collab-init` in the intended project, specifying roles if desired:

```text
$collab-init Set up this project with Codex implementing and Claude reviewing.
```

Install the whole plugin: its skills share `reference/`, `templates/`, and
`scripts/` at the plugin root. Copying an individual skill loses those resources.

### Claude Code

```text
/plugin marketplace add tclowers/agent-collab
/plugin install agent-collab@agent-collab-marketplace
```

For unpublished local changes, start
`claude --plugin-dir /absolute/path/to/agent-collab`.

### OpenCode

From a stable local checkout:

```bash
python3 scripts/install_opencode.py
```

Restart OpenCode, then use the namespaced commands above or ask it to load a
skill by name. The installer links the complete bundle, command wrappers, and
an `agent-collab-reviewer` agent without editing your provider/model settings.
It refuses conflicting files. Keep the checkout in place; updates are visible
through the links. For a project-only install use
`--config-dir /path/to/project/.opencode`.

OpenCode can drive the project and call Claude/Codex for reviews, or serve as
an external reviewer for either host. It also supports one-off jobs and council
stages. [OpenCode setup and dispatch](reference/opencode.md) explains discovery,
model identity, scoped agents, and the JSON-output wrapper. The restricted
reviewer cannot write code; production jobs need an appropriately configured
agent and implementation jobs require an explicit writer handover.

## What is shared

- [Protocol](reference/protocol.md): roles, authorship, severity, review
  policy, and durable records.
- [Host adapters](reference/hosts.md): native subagents when exposed,
  cross-vendor CLI review, process completion, and safe output capture.
- [Reviewer brief](reference/reviewer.md): common instructions used by
  all host adapters.
- [Project configuration](templates/collab.toml.example): roles, agent
  commands, output modes, guards, and optional council stages.
- [Artifact validator](scripts/verify_artifact.py): rejects missing,
  partial, misattributed, or stale-run replies. Header and size checks do
  not establish substantive quality or cryptographically prove authorship.

Codex does not need to load Claude's `agents/*.md` declarations; its
native reviewer receives the shared brief explicitly. External CLI review
works between hosts when the selected CLI is installed, authenticated,
and permitted. Missing tooling produces a handoff or a reported limitation.

Council execution currently requires POSIX `flock`, `setsid`, and process
status support, or an equivalent project runner. It is not a native Windows
runner. Council status is read-only; invoking a council does not create a
schedule. Requested Codex app schedules use the app's automation tools.

## Versions and existing projects

Plugin version **0.3.0** implements **collab-protocol 2.0.0**. Codex local
reinstalls may append build metadata to the plugin version for cache refresh.
Projects pin their protocol in `collab.toml`. Installing the plugin does
not modify or migrate existing projects.

The major protocol change adds explicit role and review-policy semantics.
Use the [migration guide](reference/migration-v2.md) when intentionally
upgrading a 1.x project. Preserve project overlays, historical attestations,
and existing review requirements; never relabel old artifacts.

## Validate local changes

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
```

For the installed OpenCode CLI, run the opt-in integration test with a local
fixture provider (no external model call or model spend):

```bash
AGENT_COLLAB_TEST_OPENCODE=1 python3 -m unittest discover -s scripts -p 'test_*.py'
```

The plugin and skill manifests can also be checked with the Codex
plugin-creator and skill-creator validators.
