"""Blob onboarding and bounded-read regressions. No real login or Azure requests."""

import argparse
import contextlib
import gzip
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError


SCRIPT = Path(__file__).parents[1] / "blob_logs.py"
SPEC = importlib.util.spec_from_file_location("blob_logs", SCRIPT)
blob = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(blob)
TENANT = "11111111-1111-1111-1111-111111111111"
SOURCE = {"tenant_id": TENANT, "account": "examplestorage", "container": "test-logs", "prefix": "app/"}


def options(**overrides):
    return argparse.Namespace(**{"prefix": "app/261113/", "contains": "abc12", "start": None, "end": None,
                                 "log_offset": None, "max_pages": 2, "max_blobs": 5,
                                 "max_blob_bytes": 1024, "max_matches": 20, **overrides})


class FakeClient:
    def __init__(self, pages=None, payload=None):
        self.pages = pages or [([], "")]
        self.payload = payload or {}
        self.lists = []
        self.reads = []

    def list_page(self, prefix, marker, count):
        self.lists.append((prefix, marker, count))
        return self.pages[len(self.lists) - 1]

    def read(self, item, limit, probe=False):
        self.reads.append((item["name"], limit, probe))
        data = self.payload[item["name"]]
        return data[:1] if probe else data, {}


def item(name="app/261113/api.log", size=100):
    return {"name": name, "size": size, "etag": '"test-etag"'}


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "user data/blob-sources.json"

    def cli(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = blob.main([*args, "--system", "b2c", "--environment", "test", "--sources-file", str(self.config)])
        return code, json.loads(output.getvalue() or errors.getvalue())

    def save(self):
        return blob.save_source(self.config, "b2c", "test", SOURCE.copy())

    def test_source_status_never_creates_settings_or_contacts_azure(self):
        with patch.object(blob, "cli") as azure:
            code, result = self.cli("source-status")
        self.assertEqual(code, 2)
        self.assertFalse(result["source_configured"])
        self.assertIsNone(result["authenticated"])
        self.assertFalse(self.config.parent.exists())
        azure.assert_not_called()

    def test_source_save_is_separate_from_paths_and_does_not_login(self):
        path_settings = self.root / "user data/settings.json"
        path_settings.parent.mkdir()
        path_settings.write_bytes(b'{"version":1,"systems":{}}')
        before = path_settings.read_bytes()
        with patch.object(blob, "cli") as azure:
            code, result = self.cli("set-source", "--tenant-id", TENANT, "--account", SOURCE["account"],
                                    "--container", SOURCE["container"], "--source-prefix", SOURCE["prefix"])
        self.assertEqual(code, 0)
        self.assertTrue(result["source_configured"])
        self.assertIsNone(result["can_read"])
        self.assertEqual(path_settings.read_bytes(), before)
        azure.assert_not_called()

    def test_update_and_clear_preserve_other_environment_and_system(self):
        self.save()
        blob.save_source(self.config, "b2c", "prod", {**SOURCE, "container": "prod-logs"})
        data = blob.read_sources(self.config)
        data["systems"]["another-system"] = {"test": SOURCE.copy()}
        self.config.write_text(json.dumps(data), encoding="utf-8")
        blob.save_source(self.config, "b2c", "test", {**SOURCE, "prefix": "new/"})
        blob.save_source(self.config, "b2c", "test")
        after = blob.read_sources(self.config)
        self.assertEqual(after["systems"]["b2c"]["prod"], data["systems"]["b2c"]["prod"])
        self.assertEqual(after["systems"]["another-system"], data["systems"]["another-system"])

    def test_clear_missing_creates_nothing(self):
        code, result = self.cli("clear-source")
        self.assertEqual(code, 0)
        self.assertFalse(self.config.exists())

    def test_corrupt_unknown_version_or_secret_fields_are_not_overwritten(self):
        self.config.parent.mkdir()
        for value in ("private-broken", '{"version":99,"systems":{}}',
                      json.dumps({"version": 1, "systems": {"b2c": {"test": {**SOURCE, "token": "private-secret"}}}})):
            self.config.write_text(value, encoding="utf-8")
            code, result = self.cli("clear-source")
            self.assertEqual(code, 1)
            self.assertNotIn("private-", str(result))
            self.assertEqual(self.config.read_text(encoding="utf-8"), value)

    def test_invalid_source_values_are_rejected_without_writing(self):
        for change in ({"tenant_id": "not-a-guid"}, {"account": "https://secret/"},
                       {"container": "bad--container"}, {"prefix": "logs/?sig=secret"}, {"prefix": "\n"}):
            with self.subTest(change=change), self.assertRaises(blob.BlobError):
                blob.save_source(self.config, "b2c", "test", {**SOURCE, **change})
        self.assertFalse(self.config.exists())

    def test_failed_atomic_save_preserves_existing_sources(self):
        self.save()
        before = self.config.read_bytes()
        with patch.object(blob.os, "replace", side_effect=PermissionError("private-error")):
            with self.assertRaises(PermissionError):
                blob.save_source(self.config, "b2c", "test", {**SOURCE, "prefix": "other/"})
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(list(self.config.parent.glob(".blob-sources-*.tmp")), [])

    def test_missing_source_never_attempts_login(self):
        with patch.object(blob, "cli") as azure:
            code, result = self.cli("check")
        self.assertEqual(code, 2)
        self.assertEqual(result["state"], "source_missing")
        azure.assert_not_called()

    def test_status_uses_token_without_blob_reads_and_hides_token(self):
        self.save()
        with patch.object(blob, "cli", side_effect=[json.dumps({"tenantId": TENANT}), "private-token"]), \
                patch.object(blob, "BlobClient") as client:
            code, result = self.cli("status")
        self.assertEqual(code, 0)
        self.assertTrue(result["authenticated"])
        self.assertIsNone(result["can_read"])
        self.assertNotIn("private-token", str(result))
        client.assert_not_called()

    def test_expired_login_returns_needs_input_without_opening_login(self):
        self.save()
        with patch.object(blob, "cli", side_effect=blob.BlobError("needs_login")), patch.object(blob, "login") as login:
            code, result = self.cli("check")
        self.assertEqual((code, result["state"]), (2, "needs_login"))
        login.assert_not_called()

    def test_tenant_mismatch_never_gets_token_or_reads_blobs(self):
        self.save()
        with patch.object(blob, "cli", return_value=json.dumps({"tenantId": "other"})) as azure:
            code, result = self.cli("check")
        self.assertEqual((code, result["state"]), (2, "tenant_mismatch"))
        self.assertEqual(azure.call_count, 1)

    def test_cached_account_without_usable_token_is_not_authenticated(self):
        self.save()
        with patch.object(blob, "cli", side_effect=[json.dumps({"tenantId": TENANT}), blob.BlobError("needs_login")]):
            code, result = self.cli("status")
        self.assertEqual((code, result["state"]), (2, "needs_login"))
        self.assertNotIn("authenticated", result)

    def test_cancelled_login_returns_cancelled_and_can_resume_same_source(self):
        self.save()
        with patch.object(blob, "login", side_effect=KeyboardInterrupt):
            code, result = self.cli("login")
        self.assertEqual((code, result["state"]), (130, "cancelled"))
        client = FakeClient([([item()], "")], {item()["name"]: b"x"})
        with patch.object(blob, "access_token", return_value="private-token"), patch.object(blob, "BlobClient", return_value=client):
            code, result = self.cli("check")
        self.assertEqual((code, result["state"]), (0, "read_access_verified"))

    def test_invalid_query_is_rejected_before_token_acquisition(self):
        self.save()
        with patch.object(blob, "access_token") as token:
            code, result = self.cli("query", "--prefix", "other/", "--contains", "abc12")
        self.assertEqual((code, result["state"]), (1, "prefix_outside_source"))
        token.assert_not_called()


class IdentityTests(unittest.TestCase):
    def test_missing_cli_and_expired_session_are_distinct_and_errors_do_not_leak(self):
        with patch.object(blob.shutil, "which", return_value=None), self.assertRaisesRegex(blob.BlobError, "azure_cli_missing"):
            blob.cli(["account", "show"])
        with patch.object(blob.shutil, "which", return_value="az"), \
                patch.object(blob.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "private-token", "Please run az login private-detail")), \
                self.assertRaisesRegex(blob.BlobError, "^needs_login$"):
            blob.cli(["account", "show"])

    def test_token_uses_storage_audience_and_never_keys_or_shared_key(self):
        with patch.object(blob, "cli", side_effect=[json.dumps({"tenantId": TENANT}), "private-token\n"]) as azure:
            self.assertEqual(blob.access_token(SOURCE), "private-token")
        command = azure.call_args.args[0]
        self.assertIn("https://storage.azure.com/", command)
        self.assertIn(TENANT, command)
        self.assertNotIn("keys", command)

    def test_login_verifies_token_but_does_not_claim_blob_access(self):
        with patch.object(blob, "cli") as azure, patch.object(blob, "access_token", return_value="private-token"):
            result = blob.login(SOURCE)
        self.assertTrue(result["authenticated"])
        self.assertIsNone(result["can_read"])
        self.assertIn("--output", azure.call_args.args[0])
        self.assertIn("none", azure.call_args.args[0])
        self.assertTrue(azure.call_args.kwargs["interactive"])

    def test_other_cloud_is_not_silently_used(self):
        with patch.object(blob, "cli", return_value=json.dumps({"tenantId": TENANT, "environmentName": "AzureChinaCloud"})), \
                self.assertRaisesRegex(blob.BlobError, "unsupported_azure_cloud"):
            blob.access_token(SOURCE)


class ReadTests(unittest.TestCase):
    def test_empty_container_only_proves_listing(self):
        result = blob.check_access(SOURCE, FakeClient())
        self.assertTrue(result["can_list"])
        self.assertIsNone(result["can_read"])
        self.assertEqual(result["state"], "list_access_verified")

    def test_probe_reads_one_byte_of_one_blob(self):
        client = FakeClient([([item()], "next")], {item()["name"]: b"private log"})
        result = blob.check_access(SOURCE, client)
        self.assertTrue(result["can_read"])
        self.assertEqual(client.reads, [(item()["name"], 1, True)])

    def test_multiline_exception_and_timezone_filter_preserve_stack_and_redact(self):
        payload = ("[TEST] 26-11-13 10:00:00 ERROR - abc12 - API: password=private-password sig=private-sig\n"
                   "  inner exception Bearer private-token\n  at Service.Method() user@example.com\n"
                   "[TEST] 26-11-13 11:00:00 INFO - abc12 - outside\n").encode()
        client = FakeClient([([item(size=len(payload))], "")], {item()["name"]: payload})
        result = blob.query(SOURCE, client, options(start="2026-11-13T01:59:00Z", end="2026-11-13T02:01:00Z", log_offset="+08:00"))
        self.assertEqual(len(result["matches"]), 1)
        text = result["matches"][0]["text"]
        self.assertIn("at Service.Method()", text)
        self.assertNotIn("private-", text)
        self.assertNotIn("user@example.com", text)
        self.assertTrue(result["can_read"])

    def test_paging_stops_at_blob_budget_and_marks_truncation(self):
        client = FakeClient([([item()], "next")], {item()["name"]: b"abc12"})
        result = blob.query(SOURCE, client, options(max_blobs=1))
        self.assertTrue(result["truncated"])
        self.assertEqual(len(client.lists), 1)

    def test_paging_follows_marker_and_finds_later_blob(self):
        second = item("app/261113/second.log")
        client = FakeClient([([item()], "next"), ([second], "")], {item()["name"]: b"no", second["name"]: b"abc12"})
        result = blob.query(SOURCE, client, options())
        self.assertEqual(result["pages"], 2)
        self.assertEqual(client.lists[1][1], "next")
        self.assertEqual(result["matches"][0]["blob"], second["name"])

    def test_page_budget_reports_incomplete_even_if_no_matches(self):
        client = FakeClient([([], "next")])
        result = blob.query(SOURCE, client, options(max_pages=1))
        self.assertEqual(result["state"], "incomplete")
        self.assertTrue(result["truncated"])

    def test_oversized_blob_is_skipped_without_download(self):
        client = FakeClient([([item(size=2048)], "")])
        result = blob.query(SOURCE, client, options())
        self.assertEqual(result["state"], "incomplete")
        self.assertEqual(result["skipped"][0]["reason"], "size_limit")
        self.assertEqual(client.reads, [])

    def test_total_byte_budget_is_enforced_across_files(self):
        second = item("app/261113/second.log", 3)
        client = FakeClient([([item(size=3), second], "")], {item()["name"]: b"abc"})
        with patch.object(blob, "MAX_TOTAL_BYTES", 4):
            result = blob.query(SOURCE, client, options())
        self.assertEqual(result["bytes_read"], 3)
        self.assertEqual(len(client.reads), 1)
        self.assertTrue(result["truncated"])

    def test_json_secrets_sas_and_connection_string_are_redacted(self):
        original = ('{"access_token":"private-token","password":"private password"} '
                    'https://account.blob.core.windows.net/c/log?sv=2024&sig=private-signature '
                    'Server=host;Password=private-password;AccountKey=private-key;')
        self.assertNotIn("private", blob.redact(original))

    def test_gzip_is_bounded_after_decompression(self):
        name = "app/261113/api.log.gz"
        data = gzip.compress(b"abc12" * 1000)
        client = FakeClient([([item(name, len(data))], "")], {name: data})
        result = blob.query(SOURCE, client, options())
        self.assertTrue(result["truncated"])
        self.assertEqual(result["skipped"][0]["reason"], "decoded_size_limit")

    def test_small_gzip_can_be_searched(self):
        name = "app/261113/api.log.gz"
        data = gzip.compress(b"abc12 exception")
        client = FakeClient([([item(name, len(data))], "")], {name: data})
        result = blob.query(SOURCE, client, options())
        self.assertEqual(result["state"], "matches_found")

    def test_match_limit_is_explicit(self):
        data = b"26-11-13 10:00:00 abc12\n26-11-13 10:00:01 abc12"
        client = FakeClient([([item()], "")], {item()["name"]: data})
        result = blob.query(SOURCE, client, options(max_matches=1))
        self.assertEqual(len(result["matches"]), 1)
        self.assertTrue(result["truncated"])

    def test_unknown_timestamp_is_reported_when_time_filter_requested(self):
        client = FakeClient([([item()], "")], {item()["name"]: b"abc12 unknown format"})
        result = blob.query(SOURCE, client, options(start="2026-11-13T00:00:00Z", end="2026-11-13T01:00:00Z", log_offset="+08:00"))
        self.assertEqual(result["unparsed_timestamps"], 1)
        self.assertEqual(result["state"], "incomplete")

    def test_time_window_requires_timezone_and_rejects_reverse_or_large_range(self):
        for args in (options(start="2026-11-13"), options(start="2026-11-13T00:00:00", end="2026-11-14T00:00:00", log_offset="+08:00"),
                     options(start="2026-11-14T00:00:00Z", end="2026-11-13T00:00:00Z", log_offset="+08:00"),
                     options(start="2026-11-01T00:00:00Z", end="2026-11-13T00:00:00Z", log_offset="+08:00")):
            with self.assertRaises(blob.BlobError):
                blob.window(args)


class HttpTests(unittest.TestCase):
    def client(self, error=None, data=b""):
        client = blob.BlobClient(SOURCE, "private-token")
        response = Mock()
        response.read.return_value = data
        response.headers = {}
        client.opener = Mock()
        if error:
            client.opener.open.side_effect = error
        else:
            client.opener.open.return_value.__enter__ = Mock(return_value=response)
            client.opener.open.return_value.__exit__ = Mock(return_value=False)
        return client

    def test_http_failures_are_distinguished_without_raw_details(self):
        for status, header, expected in ((401, "", "needs_login"), (403, "AuthorizationPermissionMismatch", "permission_denied"),
                                          (403, "AuthorizationFailure", "access_denied"), (404, "", "source_or_blob_not_found"),
                                          (412, "", "blob_changed"), (429, "", "throttled")):
            error = HTTPError("https://private-url", status, "private-message", {"x-ms-error-code": header}, None)
            with self.subTest(status=status, header=header), self.assertRaisesRegex(blob.BlobError, "^" + expected + "$"):
                self.client(error).get("", 1)

    def test_network_failure_does_not_expose_url_or_token(self):
        with self.assertRaisesRegex(blob.BlobError, "^network_failed$"):
            self.client(URLError("private-token private-url")).get("", 1)

    def test_response_read_is_bounded_and_does_not_follow_redirects(self):
        with self.assertRaisesRegex(blob.BlobError, "response_size_limit"):
            self.client(data=b"xx").get("", 1)
        with self.assertRaisesRegex(blob.BlobError, "unexpected_redirect"):
            blob.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example")

    def test_list_url_is_encoded_and_name_encoding_is_decoded_once(self):
        data = b'<EnumerationResults><Blobs><Blob><Name Encoded="true">app/261113/a%20b.log</Name><Properties><Content-Length>3</Content-Length><Etag>etag</Etag></Properties></Blob></Blobs><NextMarker>next</NextMarker></EnumerationResults>'
        client = self.client(data=data)
        records, marker = client.list_page("app/261113/", "", 1)
        self.assertEqual(records[0]["name"], "app/261113/a b.log")
        self.assertEqual(marker, "next")
        request = client.opener.open.call_args.args[0]
        self.assertIn("prefix=app%2F261113%2F", request.full_url)
        self.assertEqual(request.get_method(), "GET")

    def test_unexpected_or_traversal_names_and_xml_entities_are_rejected(self):
        for data in (b'<EnumerationResults><Blobs><Blob><Name>other/a.log</Name><Properties><Content-Length>3</Content-Length></Properties></Blob></Blobs></EnumerationResults>',
                     b'<EnumerationResults><Blobs><Blob><Name>app/../a.log</Name><Properties><Content-Length>3</Content-Length></Properties></Blob></Blobs></EnumerationResults>',
                     b'<!DOCTYPE a [<!ENTITY x "private">]><EnumerationResults/>'):
            with self.assertRaisesRegex(blob.BlobError, "invalid_blob_list"):
                self.client(data=data).list_page("app/", "", 1)


if __name__ == "__main__":
    unittest.main()
