import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from experiments.sqlite_export import ADAPTER_VERSION, call, setup


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = setup(Path(self.temp.name) / "trial")

    def request(self, **changes):
        req = {"action": "export", "output": "products.csv",
               "expected_application_version": sqlite3.sqlite_version,
               "expected_adapter_version": ADAPTER_VERSION}
        req.update(changes)
        return req

    def test_export_matches_independent_expected_bytes_and_keeps_source(self):
        before = (self.root / "source.sqlite").read_bytes()
        result = call(self.root, self.request())
        self.assertTrue(result["ok"])
        expected = b"id,name,quantity\n1,Bolt,12\n2,Nut,18\n3,Washer,24\n"
        self.assertEqual((self.root / "products.csv").read_bytes(), expected)
        self.assertEqual(result["evidence"]["sha256"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(result["evidence"]["data_rows"], 3)
        self.assertEqual((self.root / "source.sqlite").read_bytes(), before)

    def test_stale_version_recovers_using_current_status(self):
        result = call(self.root, self.request(expected_adapter_version="stale-test-value"))
        self.assertEqual(result["code"], "VERSION_MISMATCH")
        self.assertFalse((self.root / "products.csv").exists())
        status = call(self.root, {"action": "status"})
        self.assertTrue(call(self.root, self.request(
            expected_adapter_version=status["runtime"]["adapter_version"]))["ok"])

    def test_existing_output_is_preserved(self):
        output = self.root / "products.csv"
        output.write_bytes(b"keep me")
        result = call(self.root, self.request())
        self.assertEqual(result["code"], "OUTPUT_EXISTS")
        self.assertEqual(output.read_bytes(), b"keep me")
        self.assertTrue(call(self.root, self.request(output="products-2.csv"))["ok"])

    def test_cannot_write_outside_trial_directory(self):
        self.assertEqual(call(self.root, self.request(output="../escape.csv"))["code"], "INVALID_OUTPUT")
        self.assertFalse((self.root.parent / "escape.csv").exists())

    def test_corrupt_source_never_reports_export_success(self):
        (self.root / "source.sqlite").write_bytes(b"corrupt database")
        self.assertEqual(call(self.root, self.request())["code"], "DATABASE_ERROR")
        self.assertFalse((self.root / "products.csv").exists())

    def test_output_symlink_does_not_overwrite_target(self):
        target = self.root / "important.txt"
        target.write_text("keep me")
        (self.root / "products.csv").symlink_to(target)
        self.assertEqual(call(self.root, self.request())["code"], "OUTPUT_EXISTS")
        self.assertEqual(target.read_text(), "keep me")
