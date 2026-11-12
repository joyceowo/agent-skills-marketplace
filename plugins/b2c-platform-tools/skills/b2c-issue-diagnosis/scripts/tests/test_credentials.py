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

    def test_wait_continues_until_input_is_saved_and_only_checks_the_target(self):
        backend = MemoryBackend()
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            credentials._progress(progress, "waiting_for_input", [], "b2c/prod/db")

            def finish_input(_seconds):
                credentials.store_new(backend, "prod", "db", credentials.Credential("password", "private-user", "private-value"))
                credentials._progress(progress, "complete", ["b2c/prod/db"])

            with patch.object(credentials.time, "sleep", side_effect=finish_input) as pause:
                result = credentials.wait_for_setup(backend, "prod", "db", progress)
            pause.assert_called_once()
        self.assertEqual(result, {"service": "b2c/prod/db", "state": "complete", "ready": True})
        self.assertNotIn("private-", json.dumps(result))
        self.assertEqual(set(backend.records), {("b2c/prod/db", credentials.ACCOUNT)})

    def test_wait_does_not_treat_startup_pending_cancel_or_failure_as_ready(self):
        backend = MemoryBackend()
        credentials.store_new(backend, "test", "db", credentials.Credential("password", "private-user", "private-value"))
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            for state in ("starting", "waiting_for_input", "cancelled", "failed"):
                with self.subTest(state=state):
                    credentials._progress(progress, state, [], "b2c/test/db")
                    with patch.object(backend, "get_password", wraps=backend.get_password) as reader:
                        result = credentials.wait_for_setup(backend, "test", "db", progress, seconds=0)
                    self.assertFalse(result["ready"])
                    self.assertEqual(result["state"], state)
                    reader.assert_not_called()

    def test_wait_requires_saved_valid_credential_even_when_progress_is_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            credentials._progress(progress, "complete", ["b2c/test/db"])
            with self.assertRaisesRegex(credentials.CredentialError, "^verification_failed$"):
                credentials.wait_for_setup(MemoryBackend(), "test", "db", progress)

    def test_wait_rejects_wrong_target_without_reading_any_credential(self):
        backend = MemoryBackend()
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            for state, services, current in (("complete", ["b2c/prod/db"], ""),
                                              ("waiting_for_input", [], "b2c/test/storage"),
                                              ("complete", [], "")):
                credentials._progress(progress, state, services, current)
                with patch.object(backend, "get_password") as reader:
                    with self.assertRaisesRegex(credentials.CredentialError, "^progress_target_mismatch$"):
                        credentials.wait_for_setup(backend, "test", "db", progress)
                    reader.assert_not_called()

    def test_wait_missing_or_partially_written_progress_is_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            result = credentials.wait_for_setup(MemoryBackend(), "test", "db", progress, seconds=0)
            self.assertFalse(result["ready"])
            progress.write_text('{"state":', encoding="utf-8")
            result = credentials.wait_for_setup(MemoryBackend(), "test", "db", progress, seconds=0)
            self.assertFalse(result["ready"])

    def test_wait_cli_reports_distinct_outcomes_and_preserves_progress(self):
        backend = MemoryBackend()
        credentials.store_new(backend, "test", "db", credentials.Credential("password", "private-user", "private-value"))
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            for state, exit_code in (("starting", 2), ("cancelled", 130), ("failed", 1), ("complete", 0)):
                with self.subTest(state=state):
                    credentials._progress(progress, state, ["b2c/test/db"] if state == "complete" else [])
                    before = progress.read_bytes()
                    output = io.StringIO()
                    with patch.object(credentials, "native_backend", return_value=backend), \
                            patch.object(credentials.time, "monotonic", side_effect=[0, 6]), \
                            contextlib.redirect_stdout(output):
                        self.assertEqual(credentials.main(["wait", "--environment", "test", "--resource", "db",
                                                           "--progress-file", str(progress)]), exit_code)
                    self.assertEqual(progress.read_bytes(), before)
                    self.assertEqual(json.loads(output.getvalue())["ready"], state == "complete")
                    self.assertNotIn("private-", output.getvalue())

    def test_wait_error_does_not_modify_progress_or_expose_file_content(self):
        with tempfile.TemporaryDirectory() as directory:
            progress = Path(directory) / "progress.json"
            progress.write_text('{"state":"private-value"}', encoding="utf-8")
            before = progress.read_bytes()
            output = io.StringIO()
            with patch.object(credentials, "native_backend", return_value=MemoryBackend()), contextlib.redirect_stderr(output):
                self.assertEqual(credentials.main(["wait", "--environment", "test", "--resource", "db",
                                                   "--progress-file", str(progress)]), 1)
            self.assertEqual(progress.read_bytes(), before)
            self.assertEqual(json.loads(output.getvalue()), {"error": "invalid_progress"})

    def test_each_prompt_returns_a_distinct_progress_file(self):
        output = io.StringIO()
        with patch.object(credentials, "native_backend", return_value=MemoryBackend()), \
                patch.object(credentials, "prompt") as launcher, contextlib.redirect_stdout(output):
            for _ in range(2):
                self.assertEqual(credentials.main(["prompt", "--environment", "test", "--resource", "db"]), 0)
        paths = [call.args[2] for call in launcher.call_args_list]
        self.assertNotEqual(paths[0], paths[1])
        self.assertTrue(all(json.loads(line)["state"] == "starting" for line in output.getvalue().splitlines()))

    def test_wait_cli_requires_a_progress_file_and_bounded_duration(self):
        with patch.object(credentials, "native_backend") as factory, contextlib.redirect_stderr(io.StringIO()):
            for extra in ([], ["--progress-file", "progress.json", "--seconds", "0"],
                          ["--progress-file", "progress.json", "--seconds", "31"]):
                with self.assertRaises(SystemExit) as result:
                    credentials.main(["wait", "--environment", "test", "--resource", "db", *extra])
                self.assertEqual(result.exception.code, 2)
            factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
