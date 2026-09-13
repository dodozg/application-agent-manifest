import json
import shutil
import tempfile
import unittest
from pathlib import Path

from validate import ManifestError, validate


EXAMPLE = Path(__file__).parents[1] / "examples/examplecad/.agent"


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / ".agent"
        shutil.copytree(EXAMPLE, self.root)
        self.manifest = self.root / "application-agent.json"

    def mutate(self, change):
        data = json.loads(self.manifest.read_text())
        change(data)
        self.manifest.write_text(json.dumps(data))

    def test_example_valid(self):
        self.assertEqual(validate(self.manifest)["format"], "aam-draft-0.1")

    def test_rejects_missing_evidence_definition(self):
        self.mutate(lambda d: d["operations"][0]["evidence"].append("made_up"))
        with self.assertRaises(ManifestError):
            validate(self.manifest)

    def test_rejects_parent_traversal(self):
        self.mutate(lambda d: d["operations"][0].update(workflow="../operator.md"))
        with self.assertRaises(ManifestError):
            validate(self.manifest)

    def test_rejects_symlink(self):
        (self.root / "link.md").symlink_to(self.root / "operator.md")
        self.mutate(lambda d: d.update(operator_guide="link.md"))
        with self.assertRaises(ManifestError):
            validate(self.manifest)


if __name__ == "__main__":
    unittest.main()
