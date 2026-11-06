# Review-cycle roles (plugin 0.3.1 / protocol 2.1.0)

Resolve roles once when a new review cycle starts. The initiating agent is
the writer for that scope, responsible for handoff, fixes, tests and dispositions.
A handoff alone still does not authorize dispatch. Preserve original authorship:
if another agent owns active work, record the handover and stop competing writes
before taking responsibility. Forwarding another author's artifact does not make
you its author. A reviewer never becomes the writer by sending its reply.

## New-project defaults

```toml
protocol = "2.1.0"

[roles]
mode = "dynamic"
preferred_reviewers = ["claude", "codex"]
producers = []
```

Declare each participating agent under `[agents.*]` with its token, attestation
and invocation settings as usual. The list contains stable agent keys, not a
hardcoded ranking of changing model releases. It is ordered and may contain more
than two identities. Do not pin `roles.implementer`, `roles.reviewers` or
`reviewer.identity` in dynamic mode. `[reviewer]` still supplies transport,
sandbox, timeout and escalation settings; the chosen agent supplies its command.

## Selection order

1. An explicitly requested reviewer wins for this cycle. Resolve an agent name,
   configured alias or exact configured model to one agent route. For example,
   “dispatch a review from Claude” selects `agents.claude` even if the preferred
   list has a different order. A request naming only a model must map uniquely
   to a configured route; do not guess the provider or switch to a different model.
2. Otherwise choose the first preferred agent other than the writer. Exclude
   candidates with the same **known** `model_family` as the writer, useful when
   OpenCode runs a Claude or GPT model. Default declarations use `claude` and
   `gpt` respectively. If family is unknown, record that uncertainty and check
   actual model independence before dispatch under any cross-vendor policy.
3. If there is no eligible candidate, report the configuration gap. Missing
   credentials, tools or a failed invocation do not authorize silently changing
   the selected identity/model. A configured transport fallback may run the same
   selected reviewer through another permitted transport; changing the reviewer
   needs an existing explicit fallback policy or a user choice. An explicit
   reviewer request must never be replaced by the default pair.

| Initiator | Request | Selected reviewer |
|---|---|---|
| Codex | “dispatch a review” | Claude |
| Claude | “dispatch a review” | Codex |
| OpenCode, unknown family | “dispatch a review” | Claude (first preferred; independence still checked) |
| OpenCode running Claude | “dispatch a review” | Codex |
| Any writer | “dispatch a review from configured agent X” | X |

A named reviewer from the writer's host/family requires a fresh, independent run
and must meet project policy. Never let the writing session review itself. If
cross-vendor policy conflicts with the request, explain that conflict rather than
claiming independence or silently substituting someone else.

## Deterministic resolution

Use the plugin's helper (Python 3.11+) for new dispatches:

```bash
python3 scripts/resolve_review.py --config /project/collab.toml --initiator codex
python3 scripts/resolve_review.py --config /project/collab.toml --initiator codex --reviewer claude
python3 scripts/resolve_review.py --config /project/collab.toml --initiator codex --reviewer opencode --model provider/requested-model
```

Optional `agents.<key>.aliases` names an agent route; `model` is its configured
default. Matching a configured model selects that route and model. If multiple
routes match, specify the route instead of choosing arbitrarily. `--model` is
only for an explicit model override on an explicit route; map it to that host's
supported invocation mechanism after checking installed help. Do not mutate the
project's default model or replace a user's requested reasoning variant.
Supply actual `--initiator-model` / `--initiator-family` when known, especially
for multi-provider hosts. An override with unknown family does not inherit a
possibly incorrect family from the agent's default model.

The helper reads TOML and emits role-selection JSON. It does not launch agents,
check authentication, enforce tool permissions, prove model independence, or
authorize writes. Retain its output in the dispatch record with the scope,
revision, writer session, reviewer run ID, requested model/variant, and the actual
model/process identity observed at completion. Host defaults are recorded as
unknown until observed, never invented. Use these resolved identities for
attestations, paths, commands and dispositions.

Resume and follow-up rounds use the recorded cycle identities, even if a different
host resumes or preferences change. A requested reassignment needs a recorded
handover and a new dispatch identity; never rewrite the original review record.
Council stages with explicit agents and producer/implementation jobs keep their
own assignments; this routing rule does not reassign a running council or worker.

## Existing projects

An absent `roles.mode` means **fixed**, preserving legacy `roles.implementer`,
`roles.reviewers` and `reviewer.identity`. `mode = "fixed"` is also supported.
The helper refuses an initiating writer that conflicts with the fixed assignment;
resolve a handover/configuration change explicitly. An explicit reviewer request
overrides the fixed default for that dispatch, while required additional reviewers
and escalation gates still apply. Multi-reviewer fixed configurations are
dispatched explicitly per reviewer, not silently reduced to one review.

To adopt dynamic routing, an authorized `collab-init` upgrade sets protocol 2.1.0,
adds `mode = "dynamic"` and the preferred list, and removes the three static role
pins. Preserve agent configurations, review-round limits, overlays, artifacts and
in-flight cycle identities. Update generated instructions and record the change
in the ledger. Do not rewrite conflicting project overlays without resolving the
user's intended rule. Installing a plugin never migrates projects by itself.
