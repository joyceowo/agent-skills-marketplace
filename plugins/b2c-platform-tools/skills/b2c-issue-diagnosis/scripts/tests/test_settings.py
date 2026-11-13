"""Path onboarding regressions using temporary directories; no real user settings."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "settings.py"
SPEC = importlib.util.spec_from_file_location("b2c_settings", SCRIPT)
settings = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(settings)


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "user data" / "settings.json"
        self.frontend = self.root / "前端 Portal"
        self.backend = self.root / "後端 PortalAPI"
        self.frontend.mkdir()
        self.backend.mkdir()

    def cli(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = settings.main([*arguments, "--settings-file", str(self.config)])
        return code, json.loads(output.getvalue() or errors.getvalue())

    def test_fresh_status_returns_sources_without_creating_any_settings(self):
        code, result = self.cli("status", "--system", "b2c")
        self.assertEqual(code, 2)
        self.assertFalse(self.config.parent.exists())
        for role, repository in (("frontend", "Portal"), ("backend", "PortalAPI")):
            self.assertEqual(result["paths"][role]["state"], "missing")
            self.assertEqual(result["paths"][role]["source_url"],
                             f"https://ChannelSolution@dev.azure.com/ChannelSolution/Portal/_git/{repository}")

    def test_partial_setup_can_be_used_without_configuring_the_other_role(self):
        code, result = self.cli("set-path", "--system", "b2c", "--role", "frontend",
                                "--path", str(self.frontend))
        self.assertEqual(code, 0)
        self.assertEqual(set(result["paths"]), {"frontend"})
        code, result = self.cli("resolve", "--system", "b2c", "--role", "frontend")
        self.assertEqual(code, 0)
        self.assertEqual(result["path"], str(self.frontend.resolve()))
        self.assertEqual(result["origin"], "settings")
        self.assertFalse(result["needs_input"])
        code, _ = self.cli("status", "--system", "b2c")
        self.assertEqual(code, 2)
        code, _ = self.cli("status", "--system", "b2c", "--role", "frontend")
        self.assertEqual(code, 0)

    def test_set_and_update_preserve_other_roles_and_systems(self):
        self.config.parent.mkdir()
        initial = {"version": 1, "systems": {
            "another-system": {"backend_path": str(self.backend)},
            "b2c": {"backend_path": str(self.backend)}}}
        self.config.write_text(json.dumps(initial), encoding="utf-8")
        settings.set_path(self.config, "b2c", "frontend", str(self.frontend))
        replacement = self.root / "replacement"
        replacement.mkdir()
        settings.set_path(self.config, "b2c", "frontend", str(replacement))
        data = settings.read_settings(self.config)
        self.assertEqual(data["systems"]["another-system"], initial["systems"]["another-system"])
        self.assertEqual(data["systems"]["b2c"]["backend_path"], str(self.backend))
        self.assertEqual(data["systems"]["b2c"]["frontend_path"], str(replacement.resolve()))

    def test_temporary_explicit_path_takes_priority_without_persisting(self):
        settings.set_path(self.config, "b2c", "backend", str(self.backend))
        before = self.config.read_bytes()
        result = settings.resolve_path(self.config, "b2c", "backend", str(self.frontend))
        self.assertTrue(result["ready"])
        self.assertEqual(result["origin"], "request")
        self.assertEqual(result["path"], str(self.frontend.resolve()))
        self.assertEqual(self.config.read_bytes(), before)

    def test_explicit_path_works_without_initialization_and_creates_nothing(self):
        code, result = self.cli("resolve", "--system", "b2c", "--role", "backend",
                                "--path", str(self.backend))
        self.assertEqual(code, 0)
        self.assertEqual(result["origin"], "request")
        self.assertFalse(self.config.parent.exists())

    def test_workspace_is_only_used_when_explicitly_supplied_and_no_saved_path(self):
        result = settings.resolve_path(self.config, "b2c", "backend")
        self.assertTrue(result["needs_input"])
        result = settings.resolve_path(self.config, "b2c", "backend", workspace=str(self.backend))
        self.assertEqual(result["origin"], "workspace")
        self.assertTrue(result["ready"])
        self.assertFalse(self.config.exists())
        settings.set_path(self.config, "b2c", "backend", str(self.backend))
        result = settings.resolve_path(self.config, "b2c", "backend", workspace=str(self.frontend))
        self.assertEqual(result["origin"], "settings")
        self.assertEqual(result["path"], str(self.backend.resolve()))

    def test_stale_path_requires_input_instead_of_silently_falling_back(self):
        settings.set_path(self.config, "b2c", "backend", str(self.backend))
        self.backend.rmdir()
        before = self.config.read_bytes()
        result = settings.resolve_path(self.config, "b2c", "backend", workspace=str(self.frontend))
        self.assertEqual(result["state"], "invalid")
        self.assertEqual(result["origin"], "settings")
        self.assertTrue(result["needs_input"])
        self.assertEqual(self.config.read_bytes(), before)

    def test_invalid_explicit_path_does_not_fall_back_to_a_saved_directory(self):
        settings.set_path(self.config, "b2c", "backend", str(self.backend))
        result = settings.resolve_path(self.config, "b2c", "backend", "https://example.test/project")
        self.assertFalse(result["ready"])
        self.assertEqual(result["origin"], "request")

    def test_urls_relative_missing_or_file_paths_are_not_saved(self):
        file_path = self.root / "source.txt"
        file_path.touch()
        values = ("https://dev.azure.com/org/project/_git/repo", "relative/path", "",
                  str(self.root / "missing"), str(file_path))
        for value in values:
            with self.subTest(value=value):
                code, _ = self.cli("set-path", "--system", "b2c", "--role", "backend", "--path", value)
                self.assertEqual(code, 1)
                self.assertFalse(self.config.parent.exists())

    def test_unreadable_directory_is_not_saved(self):
        with patch.object(settings.os, "scandir", side_effect=PermissionError("private details")):
            code, result = self.cli("set-path", "--system", "b2c", "--role", "backend",
                                    "--path", str(self.backend))
        self.assertEqual(code, 1)
        self.assertEqual(result, {"error": "directory_missing_or_unreadable"})
        self.assertFalse(self.config.exists())

    def test_invalid_settings_are_never_overwritten_or_echoed(self):
        self.config.parent.mkdir()
        for content in ("private-malformed-value", '{"version":99,"systems":{}}',
                        '{"version":true,"systems":{}}',
                        '{"version":1,"systems":{"b2c":{"password":"private-secret"}}}',
                        '{"version":1,"systems":{"b2c":{"backend_path":"relative/path"}}}'):
            with self.subTest(content=content):
                self.config.write_text(content, encoding="utf-8")
                code, result = self.cli("set-path", "--system", "b2c", "--role", "backend",
                                        "--path", str(self.backend))
                self.assertEqual(code, 1)
                self.assertNotIn("private-", json.dumps(result))
                self.assertEqual(self.config.read_text(encoding="utf-8"), content)

    def test_clear_only_removes_the_requested_role_and_does_not_create_empty_files(self):
        code, _ = self.cli("clear-path", "--system", "b2c", "--role", "frontend")
        self.assertEqual(code, 0)
        self.assertFalse(self.config.parent.exists())
        settings.set_path(self.config, "b2c", "frontend", str(self.frontend))
        settings.set_path(self.config, "b2c", "backend", str(self.backend))
        code, result = self.cli("clear-path", "--system", "b2c", "--role", "frontend")
        self.assertEqual(code, 0)
        self.assertFalse(result["ready"])
        self.assertEqual(settings.read_settings(self.config)["systems"]["b2c"],
                         {"backend_path": str(self.backend.resolve())})

    def test_source_definition_is_not_inferred_from_the_working_directory(self):
        for identifier in ("../b2c", "another-system"):
            with self.subTest(identifier=identifier):
                code, _ = self.cli("status", "--system", identifier)
                self.assertEqual(code, 1)
                self.assertFalse(self.config.exists())

    def test_a_new_system_definition_uses_separate_paths_and_sources(self):
        systems_root = self.root / "definitions"
        other = systems_root / "other"
        other.mkdir(parents=True)
        (other / "system.json").write_text(json.dumps({"id": "other", "repositories": {
            role: {"url": f"https://example.test/{role}"} for role in settings.ROLES}}), encoding="utf-8")
        settings.set_path(self.config, "b2c", "backend", str(self.backend))
        before = settings.read_settings(self.config)["systems"]["b2c"]
        with patch.object(settings, "SYSTEMS_ROOT", systems_root):
            settings.set_path(self.config, "other", "frontend", str(self.frontend))
            result = settings.resolve_path(self.config, "other", "backend")
        self.assertTrue(result["needs_input"])
        self.assertEqual(result["source_url"], "https://example.test/backend")
        self.assertEqual(settings.read_settings(self.config)["systems"]["b2c"], before)

    def test_failed_atomic_save_preserves_the_previous_settings(self):
        settings.set_path(self.config, "b2c", "backend", str(self.backend))
        before = self.config.read_bytes()
        with patch.object(settings.os, "replace", side_effect=PermissionError("private-error")):
            code, result = self.cli("set-path", "--system", "b2c", "--role", "frontend",
                                    "--path", str(self.frontend))
        self.assertEqual(code, 1)
        self.assertEqual(result, {"error": "PermissionError"})
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(list(self.config.parent.glob(".settings-*.tmp")), [])

    def test_status_only_checks_the_requested_role(self):
        settings.set_path(self.config, "b2c", "frontend", str(self.frontend))
        settings.set_path(self.config, "b2c", "backend", str(self.backend))
        with patch.object(settings, "directory_path", wraps=settings.directory_path) as reader:
            code, _ = self.cli("status", "--system", "b2c", "--role", "frontend")
        self.assertEqual(code, 0)
        reader.assert_called_once_with(str(self.frontend.resolve()))

    def test_default_settings_location_is_outside_the_plugin(self):
        with patch.object(settings.Path, "home", return_value=self.root):
            self.assertEqual(settings.default_settings_file(),
                             self.root / ".local/share/b2c-diagnostics/settings.json")

    def test_relocated_installed_tool_works_from_an_unrelated_directory(self):
        installed = self.root / "installed skill"
        installed.mkdir()
        (installed / "scripts").mkdir()
        shutil.copy2(SCRIPT, installed / "scripts/settings.py")
        target = installed / "references/systems/b2c"
        target.mkdir(parents=True)
        shutil.copy2(settings.SYSTEMS_ROOT / "b2c/system.json", target / "system.json")
        command = [sys.executable, "-X", "utf8", "-I", str(installed / "scripts/settings.py")]
        result = subprocess.run([*command, "set-path", "--system", "b2c", "--role", "backend",
                                 "--path", str(self.backend), "--settings-file", str(self.config)],
                                cwd=self.frontend, capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ready"])
        result = subprocess.run([*command, "resolve", "--system", "b2c", "--role", "backend",
                                 "--settings-file", str(self.config)], cwd=self.frontend,
                                capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["path"], str(self.backend.resolve()))


if __name__ == "__main__":
    unittest.main()
