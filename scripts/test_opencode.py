import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import time
import unittest

from install_opencode import install, ROOT
from opencode_run import extract_reply, run_job
from verify_artifact import verify


def event(kind, message="msg-final", session="ses-test", **fields):
    return {"type": kind, "sessionID": session,
            "part": {"messageID": message, "sessionID": session, **fields}}


def stream(*events):
    return "\n".join(json.dumps(e) for e in events)


AUTHOR = "Author: OpenCode (reviewer job-123)"
REPLY = (AUTHOR + "\nAuthor-ID: job-123\nAudience: Implementer\n"
         "Date: 2026-10-06\nProtocol: collab-2.0.0\n\n"
         "Reviewed the requested fixture. No material findings. " +
         "The permitted source inspection completed; shell tests were unavailable.\n")


def success(reply=REPLY):
    return [event("step_start"), event("text", id="text-final", text=reply),
            event("step_finish", reason="stop")]


class ExtractTests(unittest.TestCase):
    def test_final_artifact_excludes_earlier_commentary(self):
        events = [event("text", message="msg-before", id="earlier", text="I will inspect it."),
                  event("step_finish", message="msg-before", reason="tool-calls"),
                  *success()]
        self.assertEqual(extract_reply(stream(*events)), REPLY)

    def test_duplicate_text_event_does_not_duplicate_artifact(self):
        events = success()
        events.insert(2, events[1])
        self.assertEqual(extract_reply(stream(*events)), REPLY)

    def test_only_final_message_text_is_used(self):
        self.assertEqual(extract_reply(stream(*success("Earlier complete response"),
                                             *[event("step_start", message="next"),
                                               event("text", message="next", id="t", text=REPLY),
                                               event("step_finish", message="next", reason="stop")])), REPLY)

    def test_failure_streams_are_rejected(self):
        cases = {
            "empty": "",
            "truncated-json": '{"type":',
            "non-json-output": "An ordinary CLI banner\n" + stream(*success()),
            "partial": stream(*success()[:-1]),
            "token-limit": stream(*success()[:-1], event("step_finish", reason="length")),
            "tool-call-only": stream(event("step_finish", reason="tool-calls")),
            "no-text": stream(event("step_finish", reason="stop")),
            "error-after-text": stream(*success(), {"type": "error", "sessionID": "ses-test"}),
            "denied-tool": stream(event("tool_use", state={"status": "error"}), *success()),
            "mixed-sessions": stream(*success(), event("text", session="other", id="x", text="other")),
            "missing-session": stream({"type": "text", "part": {"text": REPLY}}),
            "mismatched-session": stream({**event("text", id="x", text=REPLY), "sessionID": "other"}),
            "new-partial-message": stream(*success(), event("text", message="next", id="x", text="partial")),
            "new-unfinished-step": stream(*success(), event("step_start")),
        }
        for name, text in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                extract_reply(text)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_install_preserves_resources_config_and_existing_agent(self):
        config = self.root / "opencode.jsonc"
        config.write_text('// Existing private provider config\n{"model":"chosen/model"}\n')
        (self.root / "agents").mkdir()
        agent = self.root / "agents/adversarial-reviewer.md"
        agent.write_text("Existing reviewer")
        before = config.read_bytes()
        first = install(self.root)
        self.assertEqual(first, install(self.root))
        self.assertEqual(config.read_bytes(), before)
        self.assertEqual(agent.read_text(), "Existing reviewer")
        skill = self.root / "skills/agent-collab/skills/dispatch-job/SKILL.md"
        self.assertEqual(skill.read_text(), (ROOT / "skills/dispatch-job/SKILL.md").read_text())
        self.assertEqual((skill.parent / "../../reference/protocol.md").resolve(), ROOT / "reference/protocol.md")
        self.assertEqual(len(list((self.root / "commands").glob("*.md"))), 6)

    def test_collision_preflight_has_no_partial_install(self):
        (self.root / "commands").mkdir()
        collision = self.root / "commands/agent-collab:council.md"
        collision.write_text("User-owned command")
        with self.assertRaises(ValueError):
            install(self.root)
        self.assertFalse((self.root / "skills").exists())
        self.assertEqual(collision.read_text(), "User-owned command")

    def test_dangling_link_is_not_overwritten(self):
        (self.root / "skills").mkdir()
        target = self.root / "skills/agent-collab"
        target.symlink_to(self.root / "missing")
        with self.assertRaises(ValueError):
            install(self.root)
        self.assertEqual(os.readlink(target), str(self.root / "missing"))


@unittest.skipUnless(os.name == "posix", "Runner process-group handling uses POSIX")
class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent collab test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cli = self.root / "fake opencode"
        self.events = self.root / "job.events.jsonl"

    def fake_cli(self, body):
        self.cli.write_text("#!/usr/bin/env python3\n" + body)
        self.cli.chmod(0o700)

    def test_process_arguments_stdin_and_verified_output(self):
        self.fake_cli("import json, sys, pathlib\n"
                      f"pathlib.Path({str(self.root / 'args.json')!r}).write_text(json.dumps(sys.argv[1:]))\n"
                      f"pathlib.Path({str(self.root / 'prompt.txt')!r}).write_text(sys.stdin.read())\n"
                      f"print({stream(*success())!r})\n")
        prompt = "Review literal $(touch wrong) and `shell text` as source data.\n"
        reply = run_job(str(self.cli), self.root, "provider/model", self.events,
                        prompt, 5, variant="high")
        self.assertEqual(reply, REPLY)
        self.assertEqual((self.root / "prompt.txt").read_text(), prompt)
        self.assertEqual(json.loads((self.root / "args.json").read_text()),
                         ["run", "--format", "json", "--dir", str(self.root),
                          "--agent", "agent-collab-reviewer", "--model", "provider/model",
                          "--variant", "high"])
        output = self.root / "2026-10-06T170000Z-opencode-review.md"
        output.write_text(reply)
        self.assertEqual(verify(output, AUTHOR, "opencode", "job-123"), [])

    def test_nonzero_exit_with_complete_text_is_rejected(self):
        self.fake_cli(f"import sys\nprint({stream(*success())!r})\nsys.exit(7)\n")
        with self.assertRaisesRegex(ValueError, "exited 7"):
            run_job(str(self.cli), self.root, "provider/model", self.events, "prompt", 5)
        self.assertTrue(self.events.exists())

    def test_error_event_with_exit_zero_is_rejected(self):
        self.fake_cli(f"print({stream(*success(), {'type':'error', 'sessionID':'ses-test'})!r})\n")
        with self.assertRaisesRegex(ValueError, "reported an error"):
            run_job(str(self.cli), self.root, "provider/model", self.events, "prompt", 5)

    def test_timeout_terminates_process(self):
        self.fake_cli("import os, pathlib, time\n"
                      f"pathlib.Path({str(self.root / 'pid')!r}).write_text(str(os.getpid()))\n"
                      "time.sleep(20)\n")
        with self.assertRaisesRegex(ValueError, "exceeded"):
            run_job(str(self.cli), self.root, "provider/model", self.events, "prompt", 0.3)
        pid = int((self.root / "pid").read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_previous_event_log_is_preserved(self):
        self.events.write_text("previous evidence")
        with self.assertRaises(FileExistsError):
            run_job("never-launched", self.root, "provider/model", self.events, "prompt", 1)
        self.assertEqual(self.events.read_text(), "previous evidence")

    def test_terminating_wrapper_stops_child(self):
        self.fake_cli("import os, pathlib, time\n"
                      f"pathlib.Path({str(self.root / 'pid')!r}).write_text(str(os.getpid()))\n"
                      "time.sleep(20)\n")
        proc = subprocess.Popen([
            sys.executable, str(ROOT / "scripts/opencode_run.py"),
            "--project", str(self.root), "--model", "provider/model",
            "--events", str(self.events), "--executable", str(self.cli),
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            proc.stdin.write("prompt\n")
            proc.stdin.close()
            proc.stdin = None
            deadline = time.monotonic() + 3
            while not (self.root / "pid").exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue((self.root / "pid").exists())
            pid = int((self.root / "pid").read_text())
            proc.terminate()
            stdout, stderr = proc.communicate(timeout=3)
            self.assertEqual(proc.returncode, 130, stderr)
            self.assertEqual(stdout, "")
            with self.assertRaises(ProcessLookupError):
                os.kill(pid, 0)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()

    def test_configured_worker_agent(self):
        self.fake_cli("import sys\nassert sys.argv[sys.argv.index('--agent')+1] == 'scoped-worker'\n"
                      f"print({stream(*success())!r})\n")
        self.assertEqual(run_job(str(self.cli), self.root, "provider/model", self.events,
                                 "prompt", 5, agent="scoped-worker"), REPLY)


if __name__ == "__main__":
    unittest.main()
