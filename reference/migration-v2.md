# Migration from protocol 1.x to 2.0

Installing the plugin does not migrate existing projects. A 1.x project
retains its instructions, artifacts, and policy. For an authorized migration:

1. Read AGENTS.md, CLAUDE.md, collab.toml, and the recent ledger. Establish
   the actual role assignment and project overrides.
2. Add [roles] with current implementer, reviewers, and producers. Preserve
   tokens and historical attestations. Future attestation templates may use
   {role} and {run_id}; assign fresh IDs, never relabel an old artifact.
3. Add [review_policy] reflecting the existing policy. Do not silently
   replace confirmation requirements. For requested one-round review use
   trigger = "requested", max_rounds = 1, confirmation_after_fixes = false.
4. Check CLI and output_mode for each external agent. Preserve custom
   dispatch commands, permissions, escalation, and agent configurations.
   Executable availability does not establish authentication.
5. Update only the generated AGENTS.md core; retain the project overlay.
   Ensure CLAUDE.md points to shared instructions without replacing it.
6. Set protocol = "2.0.0" and record the migration, preserved overrides,
   role mapping, and validation limits in the ledger.

A version mismatch alone does not authorize migration. A user request to
upgrade supplies authorization; do not ask again. Resolve only material
choices not inferable from the request or project records.

Audit historical artifacts using the protocol/configuration applicable when
authored, not by treating every old role string as invalid today.

