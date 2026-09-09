import tempfile
import unittest
from pathlib import Path

from verify_artifact import verify


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "2026-09-09T120000Z-codex-review.md"
        self.author = "Author: Codex (reviewer run-123)"
        self.body = self.author + "\nAuthor-ID: run-123\n" + "Reviewed the requested revision. " * 10
        self.path.write_text(self.body)

    def check(self, **kwargs):
        return verify(self.path, self.author, "codex", "run-123", **kwargs)

    def test_valid(self):
        self.assertEqual(self.check(), [])

    def test_crlf(self):
        self.path.write_bytes(self.body.replace("\n", "\r\n").encode())
        self.assertEqual(self.check(), [])

    def test_wrong_author(self):
        self.path.write_text(self.body.replace("Author: Codex", "Author: Claude"))
        self.assertTrue(self.check())

    def test_token_in_topic_is_not_authorship(self):
        other = self.path.with_name("2026-09-09T120000Z-claude-codex-review.md")
        self.path.rename(other)
        self.path = other
        self.assertTrue(self.check())

    def test_old_run_id(self):
        self.path.write_text(self.body.replace("Author-ID: run-123", "Author-ID: old-run"))
        self.assertTrue(self.check())

    def test_stub(self):
        self.path.write_text(self.author + "\nAuthor-ID: run-123\nDone.")
        self.assertTrue(self.check())

    def test_duplicate_author(self):
        self.path.write_text(self.body + "\n" + self.author)
        self.assertTrue(self.check())

    def test_misplaced_run_id(self):
        self.path.write_text(self.body.replace("\nAuthor-ID:", "\n\nAuthor-ID:"))
        self.assertTrue(self.check())

    def test_exit_status(self):
        status = Path(self.temp.name) / "exit"
        self.assertTrue(self.check(exit_code_file=status))
        status.write_text("1\n")
        self.assertTrue(self.check(exit_code_file=status))
        status.write_text("0\n")
        self.assertEqual(self.check(exit_code_file=status), [])

    def test_missing_or_non_utf8(self):
        self.path.unlink()
        self.assertTrue(self.check())
        self.path.write_bytes(b"\xff" * 250)
        self.assertTrue(self.check())


if __name__ == "__main__":
    unittest.main()
