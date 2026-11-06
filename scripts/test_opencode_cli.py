"""Opt-in real CLI/transport test with a local fixture provider, no model spend.

Run: AGENT_COLLAB_TEST_OPENCODE=1 python3 -m unittest discover -s scripts -p 'test_*.py'
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

from install_opencode import install, ROOT
from verify_artifact import verify


@unittest.skipUnless(os.environ.get("AGENT_COLLAB_TEST_OPENCODE") == "1",
                     "Opt in to the installed OpenCode CLI integration test")
class OpenCodeCLITests(unittest.TestCase):
    def test_read_only_review_transport(self):
        executable = shutil.which("opencode")
        self.assertIsNotNone(executable, "OpenCode must be installed")
        with tempfile.TemporaryDirectory(prefix="agent-collab-cli-") as directory:
            project = Path(directory)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            install(project / ".opencode")
            source = project / "fixture.txt"
            source.write_text("A local transport fixture.\n")
            author = "Author: OpenCode (reviewer fixture-run)"
            reply = (author + "\nAuthor-ID: fixture-run\nAudience: Test\n"
                     "Date: 2026-10-06\nProtocol: collab-2.0.0\n\n"
                     "No material findings in the local fixture. This tests CLI transport "
                     "and permission exposure, not model judgment or provider authentication.\n")
            requests = []

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_POST(self):
                    body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    requests.append(body)
                    # First turn inspects the fixture using the actual OpenCode read tool.
                    read_done = any(m.get("role") == "tool" for m in body.get("messages", []))
                    if not body.get("tools"):
                        # OpenCode may make a separate title/summary request.
                        delta = {"content": "Local transport fixture"}
                        finish = "stop"
                    elif read_done:
                        delta = {"content": reply}
                        finish = "stop"
                    else:
                        delta = {"tool_calls": [{"index": 0, "id": "call_fixture", "type": "function",
                                  "function": {"name": "read", "arguments": json.dumps({"filePath": str(source)})}}]}
                        finish = "tool_calls"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    for value, reason in (({"role": "assistant", **delta}, None), ({}, finish)):
                        chunk = {"id": "fixture-response", "object": "chat.completion.chunk",
                                 "created": 1, "model": "fixture",
                                 "choices": [{"index": 0, "delta": value, "finish_reason": reason}]}
                        self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode())
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()

            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            config = {
                "$schema": "https://opencode.ai/config.json",
                "share": "disabled",
                "enabled_providers": ["collab-fixture"],
                "provider": {"collab-fixture": {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "Local transport fixture",
                    "options": {"baseURL": f"http://127.0.0.1:{server.server_port}/v1", "apiKey": "fixture"},
                    "models": {"fixture": {"name": "fixture", "tool_call": True,
                                           "limit": {"context": 64000, "output": 4000}}},
                }},
            }
            env = dict(os.environ, OPENCODE_CONFIG_CONTENT=json.dumps(config),
                       OPENCODE_DISABLE_AUTOUPDATE="true", OPENCODE_DISABLE_MODELS_FETCH="true")
            # --pure applies only to this disposable test, leaving user plugins intact.
            shim = project / "opencode-fixture"
            import shlex
            shim.write_text("#!/bin/sh\nexec " + shlex.quote(executable) + ' --pure "$@"\n')
            shim.chmod(0o700)
            events = project / "events.jsonl"
            prompt = (ROOT / "reference/reviewer.md").read_text() + (
                f"\nReview only {source}. Run ID: fixture-run. Begin: {author}\n"
                "Return only the complete attested review as your final response.\n")
            result = subprocess.run([
                "python3", str(ROOT / "scripts/opencode_run.py"),
                "--project", str(project), "--model", "collab-fixture/fixture",
                "--events", str(events), "--timeout", "40", "--executable", str(shim),
            ], input=prompt, text=True, capture_output=True, env=env, timeout=50)
            self.assertEqual(result.returncode, 0, result.stderr[-4000:])
            self.assertEqual(result.stdout, reply)
            self.assertGreaterEqual(len(requests), 2)
            tool_requests = [body for body in requests if body.get("tools")]
            self.assertGreaterEqual(len(tool_requests), 2)
            for body in tool_requests:
                names = {t["function"]["name"] for t in body.get("tools", [])}
                self.assertIn("read", names)
                self.assertFalse(names - {"read", "glob", "grep", "list"}, names)
            output = project / "2026-10-06T180000Z-opencode-review.md"
            output.write_text(result.stdout)
            self.assertEqual(verify(output, author, "opencode", "fixture-run"), [])
            self.assertEqual(source.read_text(), "A local transport fixture.\n")


if __name__ == "__main__":
    unittest.main()
