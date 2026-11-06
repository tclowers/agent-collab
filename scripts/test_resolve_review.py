import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

from resolve_review import resolve_review


ROOT = Path(__file__).resolve().parents[1]


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.config = tomllib.loads((ROOT / "templates/collab.toml.example").read_text())
        self.config["agents"]["opencode"] = {
            "token": "opencode", "model": "provider/review-model",
            "aliases": ["research-reviewer"],
        }

    def test_default_pair_alternates_without_config_changes(self):
        before = copy.deepcopy(self.config)
        for initiator, target in [("codex", "claude"), ("claude", "codex")]:
            with self.subTest(initiator=initiator):
                result = resolve_review(self.config, initiator)
                self.assertEqual((result["writer"], result["reviewer"]), (initiator, target))
                self.assertEqual(result["selection_source"], "preferred_reviewers")
        self.assertEqual(self.config, before)

    def test_explicit_agent_overrides_pair(self):
        result = resolve_review(self.config, "codex", "OpenCode")
        self.assertEqual(result["reviewer"], "opencode")
        self.assertEqual(result["reviewer_model"], "provider/review-model")
        self.assertEqual(result["selection_source"], "explicit_request")

    def test_explicit_model_or_alias_selects_configured_route(self):
        for request in ["provider/review-model", "RESEARCH-REVIEWER"]:
            result = resolve_review(self.config, "codex", request)
            self.assertEqual(result["reviewer"], "opencode")
            self.assertEqual(result["reviewer_model"], "provider/review-model")

    def test_model_override_is_per_dispatch(self):
        result = resolve_review(self.config, "codex", "opencode", "provider/other-model")
        self.assertEqual(result["reviewer_model"], "provider/other-model")
        self.assertEqual(result["model_source"], "explicit_request")
        self.assertEqual(self.config["agents"]["opencode"]["model"], "provider/review-model")

    def test_unknown_explicit_model_does_not_fall_back(self):
        with self.assertRaisesRegex(ValueError, "not configured"):
            resolve_review(self.config, "codex", "provider/unknown-model")

    def test_ambiguous_model_or_alias_needs_route(self):
        self.config["agents"]["second"] = copy.deepcopy(self.config["agents"]["opencode"])
        for requested in ["provider/review-model", "research-reviewer"]:
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                resolve_review(self.config, "codex", requested)
        self.assertEqual(resolve_review(self.config, "codex", "second")["reviewer"], "second")

    def test_outside_pair_uses_order_and_known_family(self):
        self.assertEqual(resolve_review(self.config, "opencode")["reviewer"], "claude")
        self.assertEqual(resolve_review(self.config, "opencode", initiator_family="Claude")["reviewer"], "codex")
        self.config["roles"]["preferred_reviewers"] = ["codex", "claude"]
        self.assertEqual(resolve_review(self.config, "opencode")["reviewer"], "codex")

    def test_actual_model_does_not_inherit_wrong_family(self):
        self.config["agents"]["opencode"]["model_family"] = "claude"
        result = resolve_review(self.config, "opencode", initiator_model="other/model")
        self.assertIsNone(result["writer_model_family"])
        result = resolve_review(self.config, "codex", "opencode", "other/model")
        self.assertIsNone(result["reviewer_model_family"])

    def test_explicit_same_host_requires_fresh_run(self):
        result = resolve_review(self.config, "codex", "codex")
        self.assertEqual(result["reviewer"], "codex")
        self.assertTrue(result["fresh_reviewer_run_required"])

    def test_single_eligible_candidate_or_no_candidate(self):
        self.config["roles"]["preferred_reviewers"] = ["claude"]
        self.assertEqual(resolve_review(self.config, "codex")["reviewer"], "claude")
        with self.assertRaisesRegex(ValueError, "No other"):
            resolve_review(self.config, "claude")

    def test_preference_validation(self):
        for preferred in [[], "claude", ["claude", "claude"], ["missing"], [1]]:
            with self.subTest(preferred=preferred), self.assertRaises(ValueError):
                self.config["roles"]["preferred_reviewers"] = preferred
                resolve_review(self.config, "codex")

    def test_explicit_request_does_not_require_eligible_pair(self):
        self.config["roles"]["preferred_reviewers"] = ["codex"]
        self.assertEqual(resolve_review(self.config, "codex", "opencode")["reviewer"], "opencode")

    def test_dynamic_rejects_static_pins(self):
        for table, key, value in [("roles", "implementer", "claude"), ("roles", "reviewers", ["codex"]),
                                  ("reviewer", "identity", "codex")]:
            config = copy.deepcopy(self.config)
            config[table][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "cannot also pin"):
                resolve_review(config, "codex")

    def test_no_silent_protocol_migration(self):
        for protocol in ["2.0.0", "1.1.0", "9.0.0"]:
            self.config["protocol"] = protocol
            with self.subTest(protocol=protocol), self.assertRaises(ValueError):
                resolve_review(self.config, "codex")

    def fixed_config(self):
        self.config["protocol"] = "2.0.0"
        self.config["roles"] = {"implementer": "claude", "reviewers": ["codex"]}
        self.config["reviewer"]["identity"] = "codex"
        return self.config

    def test_legacy_missing_mode_preserves_fixed_roles(self):
        result = resolve_review(self.fixed_config(), "claude")
        self.assertEqual((result["writer"], result["reviewer"]), ("claude", "codex"))
        self.assertEqual(result["selection_source"], "fixed_configuration")
        with self.assertRaisesRegex(ValueError, "fixed implementer"):
            resolve_review(self.config, "codex")

    def test_compatible_patch_pin_keeps_role_semantics(self):
        self.config["protocol"] = "2.1.1"
        self.assertEqual(resolve_review(self.config, "codex")["reviewer"], "claude")
        self.fixed_config()["protocol"] = "2.0.1"
        self.assertEqual(resolve_review(self.config, "claude")["reviewer"], "codex")

    def test_explicit_fixed_mode_and_reviewer_override(self):
        self.fixed_config()["roles"]["mode"] = "fixed"
        result = resolve_review(self.config, "claude", "opencode")
        self.assertEqual((result["writer"], result["reviewer"]), ("claude", "opencode"))
        self.assertEqual(self.config["reviewer"]["identity"], "codex")

    def test_fixed_conflicting_or_multiple_reviewers_not_silently_reduced(self):
        self.fixed_config()["roles"]["reviewers"] = ["opencode"]
        with self.assertRaisesRegex(ValueError, "fixed reviewer assignment"):
            resolve_review(self.config, "claude")
        self.config["roles"]["reviewers"] = ["codex", "opencode"]
        with self.assertRaisesRegex(ValueError, "multiple reviewers"):
            resolve_review(self.config, "claude")

    def test_model_override_requires_explicit_route(self):
        with self.assertRaisesRegex(ValueError, "explicit reviewer route"):
            resolve_review(self.config, "codex", model="provider/model")

    def test_unknown_initiator_not_guessed(self):
        with self.assertRaisesRegex(ValueError, "not configured"):
            resolve_review(self.config, "unknown")

    def test_cli_outputs_resolution_and_does_not_mutate_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "collab.toml"
            original = (ROOT / "templates/collab.toml.example").read_bytes()
            path.write_bytes(original)
            cmd = [sys.executable, str(ROOT / "scripts/resolve_review.py"), "--config", str(path), "--initiator", "codex"]
            result = subprocess.run(cmd, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["reviewer"], "claude")
            result = subprocess.run(cmd + ["--reviewer", "missing"], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
