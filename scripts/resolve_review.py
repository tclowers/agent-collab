#!/usr/bin/env python3
"""Resolve one review cycle without editing configuration or launching an agent."""

import argparse
import json
from pathlib import Path
import tomllib


def match_agent(agents, requested):
    """Names/aliases are case-insensitive; provider/model identifiers are exact."""
    keys = [key for key in agents if key.casefold() == requested.casefold()]
    if len(keys) == 1:
        return keys[0]
    if len(keys) > 1:
        raise ValueError("Agent keys must be distinct ignoring case")
    matches = []
    for key, agent in agents.items():
        aliases = agent.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) for a in aliases):
            raise ValueError(f"agents.{key}.aliases must be a list of names")
        if (requested.casefold() in [name.casefold() for name in [key, *aliases]]
                or requested == agent.get("model")):
            matches.append(key)
    if len(matches) != 1:
        detail = "ambiguous" if matches else "not configured"
        raise ValueError(f"Reviewer/initiator {requested!r} is {detail}; specify a unique configured agent")
    return matches[0]


def family(value):
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("model_family must be a nonempty string when supplied")
    return value.strip().casefold()


def resolve_review(config, initiator, requested=None, model=None,
                   initiator_model=None, initiator_family=None):
    agents = config.get("agents", {})
    if not isinstance(agents, dict) or not agents or any(not isinstance(a, dict) for a in agents.values()):
        raise ValueError("Declare the participating identities in [agents.*]")
    if not initiator:
        raise ValueError("Supply the actual initiating agent")
    writer = match_agent(agents, initiator)
    pin = config.get("protocol", "")
    parts = pin.split(".") if isinstance(pin, str) else []
    if len(parts) != 3 or any(not p.isascii() or not p.isdecimal() for p in parts):
        raise ValueError("Supply a numeric major.minor.patch protocol pin")
    version = tuple(map(int, parts))
    if version[0] != 2:
        raise ValueError("Resolve the protocol-major mismatch before routing; this resolver implements protocol 2.x")
    roles = config.get("roles", {})
    reviewer = config.get("reviewer", {})
    if not isinstance(roles, dict) or not isinstance(reviewer, dict):
        raise ValueError("roles and reviewer must be tables")
    mode = roles.get("mode", "fixed")
    if mode not in {"dynamic", "fixed"}:
        raise ValueError("roles.mode must be dynamic or fixed")
    if mode == "dynamic":
        if version < (2, 1, 0):
            raise ValueError("Dynamic roles require protocol 2.1.0 or later in 2.x; migrate explicitly")
        if any(k in roles for k in ("implementer", "reviewers")) or "identity" in reviewer:
            raise ValueError("Dynamic roles cannot also pin implementer, reviewers or reviewer.identity")
    elif roles.get("implementer") != writer:
        raise ValueError("Initiator differs from the fixed implementer; record a handover or migrate to dynamic roles")
    if model is not None and (not requested or not model.strip()):
        raise ValueError("A nonempty model override requires an explicit reviewer route")

    # Actual run metadata takes precedence over defaults for multi-provider hosts.
    writer_model = initiator_model or agents[writer].get("model")
    writer_family = family(initiator_family or (
        agents[writer].get("model_family")
        if initiator_model is None or initiator_model == agents[writer].get("model") else None
    ))
    if requested:
        target = match_agent(agents, requested)
        source = "explicit_request"
    elif mode == "dynamic":
        preferred = roles.get("preferred_reviewers", ["claude", "codex"])
        if (not isinstance(preferred, list) or not preferred
                or any(not isinstance(k, str) for k in preferred)
                or len(set(preferred)) != len(preferred)):
            raise ValueError("preferred_reviewers must be a nonempty ordered list of distinct agent keys")
        if any(k not in agents for k in preferred):
            raise ValueError("Every preferred reviewer must be declared in [agents.*]")
        eligible = [k for k in preferred if k != writer and not (
            writer_family and family(agents[k].get("model_family")) == writer_family)]
        if not eligible:
            raise ValueError("No other preferred reviewer is eligible; specify a reviewer explicitly")
        target = eligible[0]
        source = "preferred_reviewers"
    else:
        targets = roles.get("reviewers", [])
        if not isinstance(targets, list) or any(not isinstance(k, str) for k in targets):
            raise ValueError("Fixed roles.reviewers must be a list of agent keys")
        target = reviewer.get("identity")
        if not target and len(targets) == 1:
            target = targets[0]
        if not target or target not in agents or (targets and target not in targets):
            raise ValueError("Resolve the fixed reviewer assignment or specify the requested reviewer")
        if len(targets) > 1:
            raise ValueError("Fixed policy lists multiple reviewers; dispatch each explicitly, preserving required coverage")
        source = "fixed_configuration"

    selected = agents[target]
    selected_model = model if model is not None else selected.get("model")
    selected_family = family(selected.get("model_family")) if model is None or model == selected.get("model") else None
    return {
        "protocol": pin,
        "roles_mode": mode,
        "writer": writer,
        "writer_model": writer_model,
        "writer_model_family": writer_family,
        "reviewer": target,
        "reviewer_model": selected_model,
        "reviewer_model_family": selected_family,
        "selection_source": source,
        "requested_reviewer": requested,
        "model_source": "explicit_request" if model is not None else "agent_configuration" if selected_model else "host_default",
        "fresh_reviewer_run_required": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--initiator", required=True, help="Actual initiating agent key or alias")
    parser.add_argument("--reviewer", help="Explicitly requested agent, alias or configured model")
    parser.add_argument("--model", help="Explicit model override for the selected reviewer route")
    parser.add_argument("--initiator-model", help="Actual initiating model when different from configuration")
    parser.add_argument("--initiator-family", help="Known actual initiating model family")
    args = parser.parse_args()
    try:
        with args.config.open("rb") as f:
            config = tomllib.load(f)
        result = resolve_review(config, args.initiator, args.reviewer, args.model,
                                args.initiator_model, args.initiator_family)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
