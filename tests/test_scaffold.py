import tempfile
import unittest

from ghostide.scaffold import available_templates, build_project


class ScaffoldTests(unittest.TestCase):
    def test_build_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            from pathlib import Path

            tmp_path = Path(tmp)
            for kind in available_templates():
                created = build_project(kind, f"demo-{kind}", tmp_path)
                self.assertTrue(created)
                self.assertTrue((tmp_path / f"demo-{kind}" / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
