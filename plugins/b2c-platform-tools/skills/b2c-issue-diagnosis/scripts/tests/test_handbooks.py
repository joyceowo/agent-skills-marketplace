"""Handbook preferences: isolated files, no Notion or real user settings."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "handbooks.py"
SPEC = importlib.util.spec_from_file_location("b2c_handbooks", SCRIPT)
handbooks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handbooks)
PAGE = "11111111-1111-1111-1111-111111111111"
DATABASE = "22222222-2222-2222-2222-222222222222"
SOURCE = "collection://33333333-3333-3333-3333-333333333333"


class HandbookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "個人設定" / "handbooks.json"

    def cli(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = handbooks.main([*arguments, "--config-file", str(self.path)])
        return code, json.loads(output.getvalue() or errors.getvalue())

    def save(self, system="b2c", enabled=True, kinds=None):
        return handbooks.set_target(self.path, system, PAGE, DATABASE, SOURCE,
                                    enabled, kinds if kinds is not None else list(handbooks.KINDS))

    def test_missing_status_disable_and_clear_do_not_create_settings(self):
        for action, expected in (("status", 2), ("disable", 2), ("clear", 0)):
            code, result = self.cli(action, "--system", "b2c")
            self.assertEqual(code, expected)
            self.assertFalse(result["configured"])
            self.assertFalse(result["auto_maintain"])
            self.assertFalse(self.path.parent.exists())

    def test_explicit_cli_setup_survives_a_fresh_process(self):
        code, result = self.cli("set", "--system", "b2c", "--page-id", PAGE.replace("-", ""),
                                "--database-id", DATABASE, "--data-source-url", SOURCE,
                                "--auto-maintain", "on", "--types", "access-request")
        self.assertEqual(code, 0)
        self.assertEqual(result["target"]["page_id"], PAGE)
        actual = subprocess.run([sys.executable, "-I", str(SCRIPT), "status", "--system", "b2c",
                                 "--config-file", str(self.path)], capture_output=True, text=True)
        self.assertEqual(actual.returncode, 0, actual.stderr)
        loaded = json.loads(actual.stdout)
        self.assertEqual(loaded["target"]["types"], ["access-request"])
        self.assertTrue(loaded["auto_maintain"])
        self.assertEqual(loaded["remote_access"], "not_checked")

    def test_disable_and_clear_preserve_destination_and_other_systems(self):
        self.save("other-system", False)
        self.save()
        before = handbooks.read_config(self.path)["systems"]
        code, disabled = self.cli("disable", "--system", "b2c")
        self.assertEqual(code, 0)
        self.assertFalse(disabled["auto_maintain"])
        self.assertEqual(disabled["target"]["page_id"], PAGE)
        self.cli("clear", "--system", "b2c")
        self.assertEqual(handbooks.read_config(self.path)["systems"], {"other-system": before["other-system"]})

    def test_missing_auto_choice_is_rejected_without_a_write(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.cli("set", "--system", "b2c", "--page-id", PAGE,
                     "--database-id", DATABASE, "--data-source-url", SOURCE)
        self.assertFalse(self.path.exists())

    def test_corrupt_unknown_and_secret_containing_configs_are_preserved(self):
        self.path.parent.mkdir()
        for raw in ('{"secret":"private-token"', '{"version":2,"systems":{}}',
                    '{"version":true,"systems":{}}'):
            with self.subTest(raw=raw):
                self.path.write_text(raw, encoding="utf-8")
                code, result = self.cli("set", "--system", "b2c", "--page-id", PAGE,
                                        "--database-id", DATABASE, "--data-source-url", SOURCE,
                                        "--auto-maintain", "on")
                self.assertEqual(code, 1)
                self.assertNotIn("private-token", json.dumps(result))
                self.assertEqual(self.path.read_text(encoding="utf-8"), raw)

    def test_invalid_target_scope_and_boolean_do_not_replace_saved_values(self):
        self.save()
        before = self.path.read_bytes()
        valid = {"page_id": PAGE, "database_id": DATABASE, "data_source_url": SOURCE,
                 "auto_maintain": True, "kinds": list(handbooks.KINDS)}
        for field, value in (("page_id", "https://notion.so/private?token=secret"),
                             ("database_id", "wrong-id"), ("data_source_url", "https://example.com"),
                             ("auto_maintain", "on"), ("kinds", []),
                             ("kinds", ["common-issue", "common-issue"]), ("kinds", ["unknown"])):
            with self.subTest(field=field, value=value):
                with self.assertRaises(handbooks.HandbookError):
                    handbooks.set_target(self.path, "b2c", **{**valid, field: value})
                self.assertEqual(self.path.read_bytes(), before)

    def test_failed_atomic_replace_preserves_existing_file(self):
        self.save()
        before = self.path.read_bytes()
        with patch.object(handbooks.os, "replace", side_effect=OSError("private")):
            code, result = self.cli("disable", "--system", "b2c")
        self.assertEqual(code, 1)
        self.assertEqual(result, {"error": "OSError"})
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob(".handbooks-*.tmp")), [])

    def test_preferences_do_not_touch_source_paths_or_blob_sources(self):
        self.path.parent.mkdir()
        unrelated = [self.path.parent / name for name in ("settings.json", "blob-sources.json")]
        for path in unrelated:
            path.write_text("unchanged", encoding="utf-8")
        self.save()
        self.cli("disable", "--system", "b2c")
        self.cli("clear", "--system", "b2c")
        self.assertTrue(all(path.read_text(encoding="utf-8") == "unchanged" for path in unrelated))


if __name__ == "__main__":
    unittest.main()
