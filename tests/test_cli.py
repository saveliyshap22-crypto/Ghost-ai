import tempfile
import unittest

from ghostide.cli import GhostIDE


class CliTests(unittest.TestCase):
    def test_help_and_files_commands(self):
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
            app = GhostIDE(project_root=tmp_path)
            self.assertEqual(app.execute("/help"), 0)
            self.assertEqual(app.execute("/files 1"), 0)


if __name__ == "__main__":
    unittest.main()
