#!/usr/bin/env python3
"""Run a fresh OpenCode job and emit only its completed final response."""

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys


def extract_reply(events):
    """Reject failed/incomplete streams; exclude earlier tool-step commentary."""
    session = None
    messages = {}
    last_finish = None
    last_message = None
    for line in events.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError("Invalid OpenCode event")
        event_session = event.get("sessionID")
        if not event_session or (session and event_session != session):
            raise ValueError("Missing or mixed OpenCode session identity")
        session = event_session
        part = event.get("part", {})
        if not isinstance(part, dict):
            raise ValueError("Invalid OpenCode event part")
        if event.get("type") == "error":
            raise ValueError("OpenCode reported an error; inspect the retained event log")
        if event.get("type") == "tool_use" and part.get("state", {}).get("status") == "error":
            raise ValueError("OpenCode tool failed or was denied; job is incomplete")
        if event.get("type") not in {"text", "step_finish", "step_start", "tool_use"}:
            continue
        message = part.get("messageID")
        if not message or part.get("sessionID") != session:
            raise ValueError("Missing or mismatched message identity")
        last_message = message
        if event["type"] == "text":
            if not part.get("id") or not isinstance(part.get("text"), str):
                raise ValueError("Invalid text event")
            messages.setdefault(message, {})[part["id"]] = part["text"]
        elif event["type"] == "step_finish":
            last_finish = (message, part.get("reason"))
        elif event["type"] == "step_start":
            last_finish = None
    if not last_finish or last_finish != (last_message, "stop"):
        raise ValueError("No normally completed final OpenCode message")
    reply = "\n".join(messages.get(last_finish[0], {}).values())
    if not reply.strip():
        raise ValueError("Completed OpenCode message has no text")
    return reply


def run_job(executable, project, model, events_path, prompt, timeout,
            agent="agent-collab-reviewer", variant=None):
    command = [executable, "run", "--format", "json", "--dir", str(project),
               "--agent", agent, "--model", model]
    if variant:
        command.extend(["--variant", variant])
    # A retained raw log binds the extracted reply to the actual OpenCode session.
    # Exclusive creation prevents accidental reuse of an earlier dispatch log.
    with Path(events_path).open("x", encoding="utf-8") as events:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=events,
                                stderr=None, text=True, start_new_session=True)
        try:
            proc.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise ValueError(f"OpenCode exceeded {timeout} seconds; job is incomplete")
        except BaseException:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            raise
        if proc.returncode:
            raise ValueError(f"OpenCode exited {proc.returncode}; job is incomplete")
    return extract_reply(Path(events_path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--model", required=True, help="Configured provider/model identity")
    parser.add_argument("--events", type=Path, required=True, help="New raw JSON event log")
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--executable", default="opencode")
    parser.add_argument("--agent", default="agent-collab-reviewer",
                        help="Configured agent; default is the restricted reviewer")
    parser.add_argument("--variant", help="Explicitly configured model variant")
    args = parser.parse_args()
    if not args.project.is_dir() or args.timeout <= 0 or "/" not in args.model:
        parser.error("Use an existing project, positive timeout, and provider/model")
    prompt = sys.stdin.read()
    if not prompt.strip():
        parser.error("Supply the commissioned job prompt on stdin")
    def terminate(signum, frame):
        # Council runners often terminate the wrapper with SIGTERM. Ensure
        # the separate OpenCode process group cannot keep writing afterward.
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, terminate)
    try:
        reply = run_job(args.executable, args.project.resolve(), args.model,
                        args.events, prompt, args.timeout, args.agent, args.variant)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")
    except KeyboardInterrupt:
        parser.exit(130, "OpenCode job interrupted; child process terminated\n")
    finally:
        signal.signal(signal.SIGTERM, previous)
    sys.stdout.write(reply)
    if not reply.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
