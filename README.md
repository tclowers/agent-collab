# agent-collab

A Claude Code plugin packaging a multi-agent collaboration protocol for
projects where Claude drives implementation and other agents — other
vendors' CLIs (Codex, Grok), or isolated Claude subagents — review,
produce, and advise.

Extracted from the fleet-manager trading project (2026-07), where the
protocol was earned incident-by-incident: authorship attestation exists
because a review once landed at a self-chosen path with nothing proving
who wrote it; the guards exist because a stub reply nearly passed as a
review; the flat layout exists because attestation made per-agent
directories redundant.

## What's inside

- **`reference/protocol.md`** — collab-protocol (semver'd contract):
  attestation writer/reader rules, flat artifact layout, severity +
  disposition gate, transport-independence, council conventions.
- **Skills** — `collab-init` (bootstrap/upgrade a project), `handoff`
  (author attested handoffs), `dispatch-review` (three-transport
  adversarial review loop with attestation + substance guards),
  `council` (filesystem-state DAG orchestration), `collab-audit`
  (hygiene: unattested artifacts, disposition debt, version drift).
- **`agents/adversarial-reviewer.md`** — the in-family reviewer tier:
  fresh context, distinct author identity, refute-don't-affirm.
- **Templates** — `collab.toml.example` (the per-project config seam),
  `AGENTS.core.md` (layered core + project overlay), handoff template.

## Design principles

1. **Attestation over location.** Filenames and directories are
   convenience; the in-body `Author:` line is the proof. Guards reject
   unattested replies mechanically wherever a seam allows.
2. **Transport independence.** The same contract runs over an isolated
   subagent, a cross-vendor CLI in background, or a project's own job
   framework. Portability floor = zero infrastructure.
3. **Filesystem as state.** Council orchestration derives all state
   from attested artifacts + tiny run manifests — idempotent resume,
   no database, works identically live and headless (`claude -p`).
4. **Config owns the specifics.** Everything project-shaped (agent
   roster, CLI commands, escalation classes, council DAG) lives in the
   project's `collab.toml`, never in the plugin.

## Install

```
/plugin marketplace add tclowers/agent-collab
/plugin install agent-collab
```

Then in the target project: run the `collab-init` skill.

## Versioning

Two versions, deliberately distinct: `plugin.json` versions the
implementation; `reference/protocol.md` versions the contract
(collab-protocol, semver — MAJOR = writer/reader contract break).
Projects pin the protocol version in `collab.toml`; skills drift-check
on load.
