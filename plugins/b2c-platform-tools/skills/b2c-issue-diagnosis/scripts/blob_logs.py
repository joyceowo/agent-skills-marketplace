"""Bounded Azure Blob log reads using the user's Azure CLI identity.

Source settings are non-secret and separate from settings.py v1. Only login
changes Azure CLI's identity cache. No keys, SAS, role assignments or uploads.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import gzip
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, unquote
from urllib.request import HTTPRedirectHandler, Request, build_opener
import uuid
import xml.etree.ElementTree as ET


_spec = importlib.util.spec_from_file_location("source_settings", Path(__file__).with_name("settings.py"))
settings = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(settings)
ENVIRONMENTS = ("test", "prod")
MAX_LIST_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 10 * 1024 * 1024
MAX_TEXT_BYTES = 16 * 1024 * 1024
STAMP = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2}(?:\.\d+)?)(Z|[+-]\d{2}:\d{2})?")


class BlobError(Exception):
    """Only fixed, non-secret codes may leave the process."""


def default_sources_file():
    return Path.home() / ".local/share/b2c-diagnostics/blob-sources.json"


def validate_source(source):
    if not isinstance(source, dict) or set(source) != {"tenant_id", "account", "container", "prefix"}:
        raise BlobError("invalid_source")
    if any(not isinstance(v, str) for v in source.values()):
        raise BlobError("invalid_source")
    try:
        if str(uuid.UUID(source["tenant_id"])) != source["tenant_id"]:
            raise ValueError()
    except ValueError:
        raise BlobError("invalid_tenant_id") from None
    if not re.fullmatch(r"[a-z0-9]{3,24}", source["account"]):
        raise BlobError("invalid_storage_account")
    container = source["container"]
    if (not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", container) or "--" in container):
        raise BlobError("invalid_container")
    validate_text(source["prefix"], 1024, allow_empty=True)
    return source


def validate_text(value, limit, allow_empty=False):
    if (not isinstance(value, str) or (not allow_empty and not value.strip()) or len(value) > limit
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or "://" in value or "?" in value or "#" in value):
        raise BlobError("invalid_text_or_prefix")


def read_sources(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"version": 1, "systems": {}}
    except (OSError, ValueError):
        raise BlobError("sources_unreadable_or_invalid") from None
    if (not isinstance(data, dict) or set(data) != {"version", "systems"}
            or type(data["version"]) is not int or data["version"] != 1
            or not isinstance(data["systems"], dict)):
        raise BlobError("invalid_sources")
    for system, environments in data["systems"].items():
        settings.validate_system_id(system)
        if not isinstance(environments, dict) or set(environments) - set(ENVIRONMENTS):
            raise BlobError("invalid_sources")
        for source in environments.values():
            validate_source(source)
    return data


def source_status(path, system, environment):
    if environment not in ENVIRONMENTS:
        raise BlobError("invalid_environment")
    settings.load_system(system)
    source = read_sources(path)["systems"].get(system, {}).get(environment)
    return {"system": system, "environment": environment, "source_configured": source is not None,
            "source": source, "authenticated": None, "can_list": None, "can_read": None}


def save_source(path, system, environment, source=None):
    if environment not in ENVIRONMENTS:
        raise BlobError("invalid_environment")
    settings.load_system(system)
    if source is not None:
        validate_source(source)
    data = read_sources(path)
    if source is None:
        existing = data["systems"].get(system, {})
        if environment not in existing:
            return source_status(path, system, environment)
        del existing[environment]
    else:
        data["systems"].setdefault(system, {})[environment] = source
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, prefix=".blob-sources-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return source_status(path, system, environment)


def cli(arguments, interactive=False):
    executable = shutil.which("az")
    if not executable:
        raise BlobError("azure_cli_missing")
    try:
        result = subprocess.run([executable, *arguments, "--only-show-errors"],
                                capture_output=not interactive, text=True, encoding="utf-8",
                                errors="replace", timeout=300 if interactive else 30, check=False)
    except subprocess.TimeoutExpired:
        raise BlobError("login_timed_out" if interactive else "azure_cli_timed_out") from None
    except OSError:
        raise BlobError("azure_cli_unavailable") from None
    if result.returncode:
        if result.returncode in (130, -2):
            raise KeyboardInterrupt()
        error = result.stderr or ""
        if interactive:
            raise BlobError("login_not_completed")
        if any(s in error.lower() for s in ("az login", "interaction_required", "aadsts500", "aadsts700", "expired")):
            raise BlobError("needs_login")
        raise BlobError("azure_cli_failed")
    return result.stdout


def identity(source):
    try:
        account = json.loads(cli(["account", "show", "--output", "json"]))
    except (ValueError, TypeError):
        raise BlobError("invalid_identity_response") from None
    tenant = account.get("tenantId", "") if isinstance(account, dict) else ""
    if not isinstance(tenant, str):
        raise BlobError("invalid_identity_response")
    if tenant.lower() != source["tenant_id"]:
        raise BlobError("tenant_mismatch")
    if account.get("environmentName", "AzureCloud") != "AzureCloud":
        raise BlobError("unsupported_azure_cloud")
    return {"identity_selected": True, "tenant_id": tenant.lower()}


def access_token(source):
    identity(source)
    token = cli(["account", "get-access-token", "--tenant", source["tenant_id"],
                 "--resource", "https://storage.azure.com/", "--query", "accessToken", "--output", "tsv"])
    token = token.strip()
    if not token or any(c.isspace() for c in token):
        raise BlobError("invalid_token_response")
    return token


def login(source):
    cli(["login", "--tenant", source["tenant_id"], "--allow-no-subscriptions", "--output", "none"], interactive=True)
    access_token(source)
    return {"state": "authenticated", "authenticated": True, "can_list": None, "can_read": None}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BlobError("unexpected_redirect")


class BlobClient:
    def __init__(self, source, token):
        self.base = f'https://{source["account"]}.blob.core.windows.net/{source["container"]}'
        self.token = token
        self.opener = build_opener(NoRedirect())

    def get(self, suffix, limit, headers=None):
        request = Request(self.base + suffix, headers={"Authorization": "Bearer " + self.token,
                          "x-ms-version": "2021-12-02", **(headers or {})}, method="GET")
        try:
            with self.opener.open(request, timeout=20) as response:
                data = response.read(limit + 1)
                if len(data) > limit:
                    raise BlobError("response_size_limit")
                return data, response.headers
        except HTTPError as error:
            code = error.headers.get("x-ms-error-code", "")
            if error.code == 401 or code in ("AuthenticationFailed", "InvalidAuthenticationInfo", "ExpiredAuthenticationToken"):
                state = "needs_login"
            elif code == "AuthorizationPermissionMismatch":
                state = "permission_denied"
            elif error.code == 403:
                state = "access_denied"  # May also be a firewall/private endpoint restriction.
            else:
                state = {404: "source_or_blob_not_found", 412: "blob_changed", 429: "throttled"}.get(error.code, "storage_http_error")
            error.close()
            raise BlobError(state) from None
        except (URLError, TimeoutError, OSError):
            raise BlobError("network_failed") from None

    def list_page(self, prefix, marker, count):
        data, _ = self.get("?" + urlencode({"restype": "container", "comp": "list", "prefix": prefix,
                                           "marker": marker, "maxresults": count}), MAX_LIST_BYTES)
        try:
            if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
                raise ValueError()
            root = ET.fromstring(data)
            blobs = []
            for element in root.findall("./Blobs/Blob"):
                name_node = element.find("Name")
                name = name_node.text or ""
                if name_node.get("Encoded", "false").lower() == "true":
                    name = unquote(name)
                if (not name.startswith(prefix) or any(part in (".", "..") for part in name.split("/"))
                        or any(ord(c) < 32 for c in name)):
                    raise ValueError()
                size = int(element.findtext("Properties/Content-Length", "-1"))
                if size < 0:
                    raise ValueError()
                blobs.append({"name": name, "size": size, "etag": element.findtext("Properties/Etag", "")})
            if len(blobs) > count:
                raise ValueError()
            return blobs, root.findtext("NextMarker", "") or ""
        except (ET.ParseError, ValueError, AttributeError):
            raise BlobError("invalid_blob_list") from None

    def read(self, blob, limit, probe=False):
        headers = {"If-Match": blob["etag"]} if blob["etag"] else {}
        if probe and blob["size"]:
            headers["Range"] = "bytes=0-0"
        return self.get("/" + quote(blob["name"], safe="/"), limit, headers)


def check_access(source, client):
    blobs, _ = client.list_page(source["prefix"], "", 1)
    result = {"authenticated": True, "can_list": True, "can_read": None,
              "state": "list_access_verified"}
    if blobs:
        client.read(blobs[0], 1, probe=True)
        result.update(can_read=True, state="read_access_verified")
    return result


def redact(value):
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    value = re.sub(r"(?i)Bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [REDACTED]", value)
    value = re.sub(r'''(?i)((?:["']?)(?:password|pwd|secret|client_secret|token|access_token|refresh_token|AccountKey|SharedAccessSignature|sig|Authorization)(?:["']?)\s*[:=]\s*)(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s;&,]+)''', r"\1[REDACTED]", value)
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", value)


def window(args):
    if not args.start and not args.end and not args.log_offset:
        return None
    if not args.start or not args.end or not re.fullmatch(r"[+-](?:0\d|1[0-4]):[0-5]\d", args.log_offset or ""):
        raise BlobError("time_window_requires_start_end_and_log_offset")
    try:
        start = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
        end = datetime.fromisoformat(args.end.replace("Z", "+00:00"))
        if start.tzinfo is None or end.tzinfo is None or end <= start or end - start > timedelta(days=7):
            raise ValueError()
        offset = datetime.fromisoformat("2000-01-01T00:00:00" + args.log_offset).tzinfo
        return start, end, offset
    except ValueError:
        raise BlobError("invalid_time_window") from None


def entries(text):
    current = []
    stamp = None
    for line in text.splitlines():
        found = STAMP.search(line)
        if found and current:
            yield stamp, "\n".join(current)
            current = []
        if found:
            stamp = found
        current.append(line)
    if current:
        yield stamp, "\n".join(current)


def query(source, client, args):
    validate_text(args.prefix, 1024)
    validate_text(args.contains, 256)
    if not args.prefix.startswith(source["prefix"]):
        raise BlobError("prefix_outside_source")
    bounds = window(args)
    result = {"state": "no_matches", "authenticated": True, "can_list": False, "can_read": None,
              "pages": 0, "blobs_read": 0, "bytes_read": 0, "matches": [], "skipped": [],
              "truncated": False, "unparsed_timestamps": 0}
    marker = ""
    examined = decoded = 0
    stop = False
    for _ in range(args.max_pages):
        blobs, marker = client.list_page(args.prefix, marker, min(10, args.max_blobs - examined))
        result["pages"] += 1
        result["can_list"] = True
        for index, blob in enumerate(blobs):
            examined += 1
            name = blob["name"]
            if blob["size"] > args.max_blob_bytes or result["bytes_read"] + blob["size"] > MAX_TOTAL_BYTES:
                result["skipped"].append({"blob": redact(name), "reason": "size_limit"})
                result["truncated"] = True
                continue
            if not name.lower().endswith((".log", ".txt", ".json", ".jsonl", ".gz")):
                result["skipped"].append({"blob": redact(name), "reason": "unsupported_format"})
                result["truncated"] = True
                continue
            data, headers = client.read(blob, min(args.max_blob_bytes, MAX_TOTAL_BYTES - result["bytes_read"]))
            result["bytes_read"] += len(data)
            result["blobs_read"] += 1
            result["can_read"] = True
            if name.lower().endswith(".gz") or headers.get("Content-Encoding", "").lower() == "gzip":
                try:
                    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                        data = stream.read(min(args.max_blob_bytes, MAX_TEXT_BYTES - decoded) + 1)
                except (OSError, EOFError):
                    raise BlobError("invalid_gzip") from None
            if len(data) > args.max_blob_bytes or decoded + len(data) > MAX_TEXT_BYTES:
                result["skipped"].append({"blob": redact(name), "reason": "decoded_size_limit"})
                result["truncated"] = True
                continue
            decoded += len(data)
            try:
                text = data.decode("utf-8-sig")
            except UnicodeDecodeError:
                result["skipped"].append({"blob": redact(name), "reason": "unsupported_encoding"})
                result["truncated"] = True
                continue
            for stamp, entry in entries(text):
                if args.contains.casefold() not in entry.casefold():
                    continue
                if bounds:
                    if stamp is None:
                        result["unparsed_timestamps"] += 1
                        result["truncated"] = True
                        continue
                    try:
                        day = stamp[1] if len(stamp[1]) == 10 else "20" + stamp[1]
                        when = datetime.fromisoformat(day + "T" + stamp[2] + (stamp[3] or "" ).replace("Z", "+00:00"))
                        if when.tzinfo is None:
                            when = when.replace(tzinfo=bounds[2])
                        if not bounds[0] <= when < bounds[1]:
                            continue
                    except ValueError:
                        result["unparsed_timestamps"] += 1
                        result["truncated"] = True
                        continue
                if len(result["matches"]) >= args.max_matches:
                    result["truncated"] = stop = True
                    break
                safe = redact(entry)
                result["matches"].append({"blob": redact(name), "text": safe[:4000], "text_truncated": len(safe) > 4000})
                if len(safe) > 4000:
                    result["truncated"] = True
            if stop:
                result["truncated"] = True
                break
        if stop or not marker:
            break
        if examined >= args.max_blobs:
            result["truncated"] = True
            break
    if marker:
        result["truncated"] = True
    if result["matches"]:
        result["state"] = "matches_found"
    elif result["truncated"]:
        result["state"] = "incomplete"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Azure Blob log source setup, interactive login and bounded reads")
    parser.add_argument("action", choices=("source-status", "set-source", "clear-source", "status", "login", "check", "query"))
    parser.add_argument("--system", required=True)
    parser.add_argument("--environment", required=True, choices=ENVIRONMENTS)
    parser.add_argument("--sources-file", type=Path, default=default_sources_file())
    parser.add_argument("--tenant-id")
    parser.add_argument("--account")
    parser.add_argument("--container")
    parser.add_argument("--source-prefix", default="")
    parser.add_argument("--prefix")
    parser.add_argument("--contains")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--log-offset")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--max-blobs", type=int, default=5)
    parser.add_argument("--max-blob-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--max-matches", type=int, default=20)
    args = parser.parse_args(argv)
    if not args.sources_file.is_absolute():
        parser.error("--sources-file must be absolute")
    if args.action == "set-source" and not all((args.tenant_id, args.account, args.container)):
        parser.error("set-source requires --tenant-id, --account and --container")
    if args.action == "query" and not all((args.prefix, args.contains)):
        parser.error("query requires --prefix and --contains")
    if not (1 <= args.max_pages <= 10 and 1 <= args.max_blobs <= 50 and 1 <= args.max_matches <= 100
            and 1 <= args.max_blob_bytes <= 8 * 1024 * 1024):
        parser.error("query limits exceeded")
    base = {"system": args.system, "environment": args.environment}
    try:
        state = source_status(args.sources_file, args.system, args.environment)
        if args.action == "set-source":
            state = save_source(args.sources_file, args.system, args.environment,
                                {"tenant_id": args.tenant_id, "account": args.account,
                                 "container": args.container, "prefix": args.source_prefix})
        elif args.action == "clear-source":
            state = save_source(args.sources_file, args.system, args.environment)
        elif args.action != "source-status":
            if not state["source_configured"]:
                raise BlobError("source_missing")
            source = state["source"]
            if args.action == "query":  # Reject invalid query before token acquisition or HTTP.
                validate_text(args.prefix, 1024)
                validate_text(args.contains, 256)
                if not args.prefix.startswith(source["prefix"]):
                    raise BlobError("prefix_outside_source")
                window(args)
            if args.action == "status":
                access_token(source)
                state.update(authenticated=True, state="token_available")
            elif args.action == "login":
                state.update(login(source))
            else:
                client = BlobClient(source, access_token(source))
                state.update(check_access(source, client) if args.action == "check" else query(source, client, args))
        print(json.dumps(state, ensure_ascii=False))
        return 0 if state["source_configured"] or args.action == "clear-source" else 2
    except (KeyboardInterrupt, EOFError):
        print(json.dumps({**base, "state": "cancelled", "completed": False}))
        return 130
    except Exception as exc:
        code = str(exc) if isinstance(exc, (BlobError, settings.SettingsError)) else type(exc).__name__
        print(json.dumps({**base, "state": code, "completed": False}), file=sys.stderr)
        return 2 if code in ("source_missing", "needs_login", "tenant_mismatch", "azure_cli_missing") else 1


if __name__ == "__main__":
    raise SystemExit(main())
