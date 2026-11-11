"""Security and environment isolation checks. Uses synthetic credentials only."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import warnings
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("b2c_credentials", Path(__file__).parents[1] / "credentials.py")
credentials = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = credentials
SPEC.loader.exec_module(credentials)


class MemoryBackend:
    def __init__(self):
        self.records = {}

    def get_password(self, service, account):
        return self.records.get((service, account))

    def set_password(self, service, account, value):
        self.records[(service, account)] = value


class Terminal(io.StringIO):
    def isatty(self):
        return True


class CredentialTests(unittest.TestCase):
    def test_four_records_are_independent_and_secret_fields_are_not_exposed(self):
        backend = MemoryBackend()
        for index, (env, resource) in enumerate((e, r) for e in credentials.ENVIRONMENTS for r in credentials.RESOURCES):
            credentials.store_new(backend, env, resource, credentials.Credential("password", f"user-{index}", f"secret-{index}"))
        self.assertEqual(len(backend.records), 4)
        with patch.object(credentials, "native_backend", return_value=backend):
            for index, (env, resource) in enumerate((e, r) for e in credentials.ENVIRONMENTS for r in credentials.RESOURCES):
                result = credentials.load_credential(env, resource)
                self.assertEqual(result.secret, f"secret-{index}")
                self.assertEqual(result.username, f"user-{index}")
                self.assertNotIn(result.secret, repr(result))
                self.assertNotIn(result.username, repr(result))
        report = json.dumps(credentials.status(backend))
        self.assertNotIn("secret-", report)
        self.assertNotIn("user-", report)
        self.assertTrue(all(row["valid"] for row in credentials.status(backend)))

    def test_invalid_target_does_not_access_a_backend(self):
        with patch.object(credentials, "native_backend") as factory:
            with self.assertRaises(credentials.CredentialError):
                credentials.load_credential("production", "db")
            factory.assert_not_called()

    def test_existing_record_is_not_overwritten(self):
        backend = MemoryBackend()
        credentials.store_new(backend, "test", "db", credentials.Credential("password", "first", "original"))
        with self.assertRaises(credentials.CredentialError):
            credentials.store_new(backend, "test", "db", credentials.Credential("password", "second", "replacement"))
        self.assertEqual(json.loads(backend.get_password("b2c/test/db", credentials.ACCOUNT))["secret"], "original")

    def test_db_rejects_token_before_writing(self):
        backend = MemoryBackend()
        with self.assertRaises(credentials.CredentialError):
            credentials.store_new(backend, "prod", "db", credentials.Credential("token", "", "token"))
        self.assertEqual(backend.records, {})

    def test_storage_accepts_token_without_username(self):
        backend = MemoryBackend()
        credentials.store_new(backend, "prod", "storage", credentials.Credential("token", "", "synthetic-token"))
        self.assertTrue(next(row for row in credentials.status(backend) if row["service"] == "b2c/prod/storage")["valid"])

    def test_malformed_record_does_not_reveal_its_contents(self):
        backend = MemoryBackend()
        backend.records[("b2c/test/db", credentials.ACCOUNT)] = "private-malformed-value"
        with patch.object(credentials, "native_backend", return_value=backend):
            with self.assertRaisesRegex(credentials.CredentialError, "^invalid_record$"):
                credentials.load_credential("test", "db")
        self.assertFalse(credentials.status(backend)[0]["valid"])

    def test_backend_failure_output_excludes_exception_details(self):
        output = io.StringIO()
        with patch.object(credentials, "native_backend", side_effect=RuntimeError("private-password")), contextlib.redirect_stderr(output):
            self.assertEqual(credentials.main(["status", "--environment", "test", "--resource", "db"]), 1)
        self.assertNotIn("private-password", output.getvalue())
        self.assertEqual(json.loads(output.getvalue()), {"error": "RuntimeError"})

    def test_setup_rejects_noninteractive_input(self):
        with patch.object(sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(credentials.CredentialError, "interactive_terminal_required"):
                credentials.setup(MemoryBackend(), "test", "db")

    def test_progress_contains_only_safe_status_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            credentials._progress(path, "waiting_for_input", ["b2c/test/db"], "b2c/test/storage")
            report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(set(report), {"state", "services", "current_service"})

    def test_unknown_platform_has_no_fallback(self):
        with patch.object(sys, "platform", "linux"):
            with self.assertRaisesRegex(credentials.CredentialError, "unsupported_platform"):
                credentials.native_backend()

    def test_interactive_setup_saves_only_the_requested_record_without_echoing_fields(self):
        backend = MemoryBackend()
        output = Terminal()
        answers = ["private-user-a"]
        with patch.object(sys.stdin, "isatty", return_value=True), patch.object(sys, "stdout", output), \
                patch("builtins.input", side_effect=answers), \
                patch.object(credentials.getpass, "getpass", return_value="private-value"):
            self.assertEqual(credentials.setup(backend, "test", "db"), 0)
        self.assertEqual(set(backend.records), {("b2c/test/db", credentials.ACCOUNT)})
        self.assertNotIn("private-user", output.getvalue())
        self.assertNotIn("private-value", output.getvalue())

    def test_cancelled_setup_has_safe_progress_and_no_placeholder(self):
        backend = MemoryBackend()
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            with patch.object(sys.stdin, "isatty", return_value=True), patch.object(sys, "stdout", Terminal()), \
                    patch("builtins.input", side_effect=KeyboardInterrupt), \
                    patch.object(credentials.getpass, "getpass", return_value="private-value"):
                self.assertEqual(credentials.setup(backend, "test", "db", progress), 130)
            report = json.loads(progress.read_text(encoding="utf-8"))
        self.assertEqual(report["state"], "cancelled")
        self.assertEqual(report["services"], [])
        self.assertEqual(len(backend.records), 0)
        self.assertNotIn("private-", json.dumps(report))

    def test_getpass_refuses_echo_fallback(self):
        def insecure_prompt(*args):
            warnings.warn("no secure terminal", credentials.getpass.GetPassWarning)
        with patch.object(credentials.getpass, "getpass", side_effect=insecure_prompt):
            with self.assertRaises(credentials.getpass.GetPassWarning):
                credentials._read_secret()

    def test_existing_credential_needs_no_new_input_or_window(self):
        backend = MemoryBackend()
        credentials.store_new(backend, "prod", "db", credentials.Credential("password", "private-user", "private-value"))
        with patch.object(credentials, "native_backend", return_value=backend), \
                patch.object(credentials, "prompt") as launcher, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(credentials.main(["prompt", "--environment", "prod", "--resource", "db"]), 0)
            launcher.assert_not_called()

    def test_cli_has_no_default_environment_or_bulk_setup(self):
        with patch.object(credentials, "native_backend") as factory, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                credentials.main(["setup"])
            self.assertEqual(result.exception.code, 2)
            factory.assert_not_called()

    def test_targeted_status_does_not_read_other_credentials(self):
        backend = MemoryBackend()
        with patch.object(backend, "get_password", wraps=backend.get_password) as reader, \
                patch.object(credentials, "native_backend", return_value=backend), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(credentials.main(["status", "--environment", "prod", "--resource", "storage"]), 0)
        reader.assert_called_once_with("b2c/prod/storage", credentials.ACCOUNT)

    def test_windows_prompt_uses_a_separate_console_and_explicit_target(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys, "platform", "win32"), \
                    patch.object(credentials.subprocess, "CREATE_NEW_CONSOLE", 0x10, create=True), \
                    patch.object(credentials.subprocess, "Popen") as launch:
                credentials.prompt("test", "db", Path(directory) / "progress.json")
        arguments = launch.call_args.args[0]
        self.assertEqual(arguments[arguments.index("--environment") + 1], "test")
        self.assertEqual(arguments[arguments.index("--resource") + 1], "db")
        self.assertEqual(launch.call_args.kwargs["creationflags"], 0x10)
        self.assertTrue(launch.call_args.kwargs["close_fds"])

    def test_macos_prompt_uses_terminal_without_capturing_credential_input(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys, "platform", "darwin"), patch.object(credentials.subprocess, "run") as launch:
                credentials.prompt("prod", "storage", Path(directory) / "progress space.json")
        arguments = launch.call_args.args[0]
        self.assertEqual(arguments[0], "osascript")
        self.assertIn('tell application "Terminal" to do script', arguments[2])
        self.assertIn("--environment prod --resource storage", arguments[2])
        self.assertNotIn("input", launch.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
