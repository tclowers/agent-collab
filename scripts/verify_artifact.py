#!/usr/bin/env python3
"""Check a completed review's declared attribution, not its factual quality."""
import argparse
from pathlib import Path
import re
import sys


def verify(path, expected_author, token, run_id, min_bytes=200, exit_code_file=None):
    errors = []
    if min_bytes < 1:
        errors.append("min-bytes must be positive")
    if not run_id or run_id not in expected_author:
        errors.append("expected author must include the dispatch run ID")
    if not expected_author.startswith("Author: ") or "\n" in expected_author:
        errors.append("expected author must be one complete Author: line")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", token):
        errors.append("invalid author token")
    filename = rf"\d{{4}}-\d{{2}}-\d{{2}}T\d{{6}}Z-{re.escape(token)}-.+\.md"
    if not re.fullmatch(filename, path.name):
        errors.append("filename does not start with timestamp and expected author token")
    if exit_code_file is not None:
        try:
            if exit_code_file.read_text().strip() != "0":
                errors.append("review process did not exit successfully")
        except (OSError, UnicodeError):
            errors.append("review process exit status is missing or unreadable")
    try:
        data = path.read_bytes()
        if len(data) < min_bytes:
            errors.append("artifact is below the configured size floor")
        lines = data.decode("utf-8").splitlines()
    except (OSError, UnicodeError):
        return errors + ["artifact is missing or is not readable UTF-8"]
    if not lines or lines[0] != expected_author:
        errors.append("first line does not match the dispatched author")
    if sum(line.startswith("Author: ") for line in lines) != 1:
        errors.append("artifact must declare exactly one author")
    ids = [line for line in lines if line.startswith("Author-ID:")]
    if ids != [f"Author-ID: {run_id}"] or len(lines) < 2 or lines[1] != f"Author-ID: {run_id}":
        errors.append("Author-ID does not match the dispatch run ID")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--expected-author", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--min-bytes", type=int, default=200)
    parser.add_argument("--exit-code-file", type=Path)
    args = vars(parser.parse_args())
    errors = verify(**args)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: attribution and size checks; human/agent review of substance still required")
    return 0


if __name__ == "__main__":
    sys.exit(main())
