"""User-entered B2C credentials in Windows Credential Manager or macOS Keychain.

The CLI never returns credentials. Import load_credential inside the connection
process after confirming the target environment; do not print its return value.
"""

from __future__ import annotations

import argparse
import getpass
import json
import shlex
import subprocess
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path


ACCOUNT = "connection"
ENVIRONMENTS = ("test", "prod")
RESOURCES = ("db", "storage")
SERVICES = tuple(f"b2c/{env}/{resource}" for env in ENVIRONMENTS for resource in RESOURCES)


class CredentialError(Exception):
    """A safe error code; backend exceptions must not reach CLI output."""


@dataclass(frozen=True)
class Credential:
    auth_type: str
    username: str = field(repr=False)
    secret: str = field(repr=False)


def service_name(environment: str, resource: str) -> str:
    if environment not in ENVIRONMENTS or resource not in RESOURCES:
        raise CredentialError("invalid_target")
    return f"b2c/{environment}/{resource}"


def native_backend():
    """Use the OS backend directly, ignoring automatic/plugin backend selection."""
    if sys.platform == "win32":
        from keyring.backends.Windows import WinVaultKeyring

        backend = WinVaultKeyring()
        # This is credential persistence for the current user on this PC,
        # not DPAPI's machine-wide encryption scope.
        backend.persist = "local machine"
    elif sys.platform == "darwin":
        from keyring.backends.macOS import Keyring

        backend = Keyring()
    else:
        raise CredentialError("unsupported_platform")
    if backend.priority <= 0:
        raise CredentialError("native_backend_unavailable")
    return backend


def _decode(raw: str) -> Credential:
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError
        auth_type, username, secret = data["auth_type"], data["username"], data["secret"]
        if auth_type not in ("password", "token"):
            raise ValueError
        if not isinstance(username, str) or not isinstance(secret, str) or not secret:
            raise ValueError
        if auth_type == "password" and not username.strip():
            raise ValueError
        return Credential(auth_type, username, secret)
    except (ValueError, KeyError, TypeError):
        raise CredentialError("invalid_record") from None


def load_credential(environment: str, resource: str) -> Credential:
    """Return a credential only to the caller in this process, never stdout."""
    service = service_name(environment, resource)
    try:
        raw = native_backend().get_password(service, ACCOUNT)
        if raw is None:
            raise CredentialError("not_configured")
        result = _decode(raw)
        if resource == "db" and result.auth_type != "password":
            raise CredentialError("invalid_record")
        return result
    except CredentialError:
        raise
    except Exception:
        raise CredentialError("credential_access_failed") from None


def status(backend, services=SERVICES) -> list[dict]:
    """Only return service identifiers and validity, never stored field values."""
    records = []
    for service in services:
        raw = backend.get_password(service, ACCOUNT)
        valid = False
        if raw is not None:
            try:
                record = _decode(raw)
                valid = not (service.endswith("/db") and record.auth_type != "password")
            except CredentialError:
                pass
        records.append({"service": service, "present": raw is not None, "valid": valid})
    return records


def store_new(backend, environment: str, resource: str, credential: Credential) -> None:
    service = service_name(environment, resource)
    if backend.get_password(service, ACCOUNT) is not None:
        raise CredentialError("already_configured")
    raw = json.dumps(
        {"version": 1, "auth_type": credential.auth_type,
         "username": credential.username, "secret": credential.secret},
        ensure_ascii=False, separators=(",", ":"),
    )
    _decode(raw)
    if resource == "db" and credential.auth_type != "password":
        raise CredentialError("invalid_record")
    backend.set_password(service, ACCOUNT, raw)
    if backend.get_password(service, ACCOUNT) != raw:
        raise CredentialError("verification_failed")


def _read_secret() -> str:
    # Never allow getpass to fall back to echoed terminal input.
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        while True:
            secret = getpass.getpass("密碼 / token（不顯示）：")
            repeated = getpass.getpass("再次輸入確認（不顯示）：")
            if secret and secret == repeated:
                return secret
            print("兩次輸入不一致或內容空白，請重新輸入。")


def _progress(path: Path | None, state: str, services: list[str], current: str = "") -> None:
    if path is not None:
        # Fixed non-secret fields only. This file is safe for the assistant to read.
        path.write_text(json.dumps({"state": state, "services": services,
                                    "current_service": current}), encoding="utf-8")


def setup(backend, environment: str, resource: str, progress_file: Path | None = None) -> int:
    service = service_name(environment, resource)
    existing = status(backend, (service,))[0]
    if existing["present"]:
        if not existing["valid"]:
            raise CredentialError("invalid_record")
        _progress(progress_file, "complete", [service])
        print(f"{service}：已有紀錄，保留，不需要再次輸入。")
        return 0
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise CredentialError("interactive_terminal_required")
    saved = []
    _progress(progress_file, "waiting_for_input", saved, service)
    print("B2C 本機憑證設定 — 帳密只送入作業系統保管庫，不會回傳聊天。")
    print(f"本次只設定 {service}，不會要求輸入其他環境或用途的帳密。")
    print("可按 Ctrl+C 中止。\n")
    try:
        label = "測試機" if environment == "test" else "正式機"
        print(f"--- {label} {resource.upper()} ---")
        auth_type = "password"
        if resource == "storage":
            choice = input("登入類型：1=帳號密碼，2=token / SAS / key [1]：").strip()
            while choice not in ("", "1", "2"):
                choice = input("請輸入 1 或 2：").strip()
            if choice == "2":
                auth_type = "token"
        username = input("帳號（token 可留空）：").strip()
        while auth_type == "password" and not username:
            username = input("帳號不可空白，請輸入帳號：").strip()
        credential = Credential(auth_type, username, _read_secret())
        store_new(backend, environment, resource, credential)
        del credential
        saved.append(service)
        if not status(backend, (service,))[0]["valid"]:
            raise CredentialError("verification_failed")
        _progress(progress_file, "complete", saved)
        print(f"{service}：已儲存並核對。未連線至任何 DB 或 Storage。")
        return 0
    except (KeyboardInterrupt, EOFError):
        _progress(progress_file, "cancelled", saved)
        print("\n設定已中止；先前已儲存的項目仍保留。")
        return 130
    except Exception:
        _progress(progress_file, "failed", saved)
        raise


def prompt(environment: str, resource: str, progress_file: Path) -> None:
    """Open a separate local terminal; neither input nor secret output is captured."""
    service_name(environment, resource)
    arguments = [sys.executable, "-I", str(Path(__file__).resolve()), "setup",
                 "--environment", environment, "--resource", resource,
                 "--progress-file", str(progress_file.resolve())]
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    _progress(progress_file, "starting", [])
    if sys.platform == "win32":
        subprocess.Popen(arguments, creationflags=subprocess.CREATE_NEW_CONSOLE, close_fds=True)
    elif sys.platform == "darwin":
        command = shlex.join(arguments)
        apple_string = command.replace("\\", "\\\\").replace('"', '\\"')
        subprocess.run(["osascript", "-e", f'tell application "Terminal" to do script "{apple_string}"',
                        "-e", 'tell application "Terminal" to activate'],
                       check=True, capture_output=True)
    else:
        raise CredentialError("unsupported_platform")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="B2C OS credential storage; no secret output")
    parser.add_argument("action", choices=("doctor", "status", "setup", "prompt"))
    parser.add_argument("--environment", choices=ENVIRONMENTS)
    parser.add_argument("--resource", choices=RESOURCES)
    parser.add_argument("--progress-file", type=Path, help="Non-secret setup progress JSON")
    args = parser.parse_args(argv)
    if args.action != "doctor" and (args.environment is None or args.resource is None):
        parser.error("--environment and --resource are required; no default environment")
    if args.progress_file is not None and args.action not in ("setup", "prompt"):
        parser.error("--progress-file is only supported for setup or prompt")
    try:
        backend = native_backend()
        if args.action == "doctor":
            from importlib.metadata import version

            print(json.dumps({"platform": sys.platform, "backend": type(backend).__name__,
                              "keyring_version": version("keyring")}, ensure_ascii=False))
        elif args.action == "status":
            service = service_name(args.environment, args.resource)
            print(json.dumps({"credentials": status(backend, (service,))}, ensure_ascii=False))
        elif args.action == "prompt":
            service = service_name(args.environment, args.resource)
            existing = status(backend, (service,))[0]
            if existing["present"]:
                if not existing["valid"]:
                    raise CredentialError("invalid_record")
                print(json.dumps({"service": service, "already_configured": True}))
                return 0
            progress_file = args.progress_file or (Path.home() / ".local/share/b2c-diagnostics" /
                                                   f"setup-{args.environment}-{args.resource}.json")
            prompt(args.environment, args.resource, progress_file)
            print(json.dumps({"service": service, "state": "starting", "progress_file": str(progress_file)}))
        else:
            return setup(backend, args.environment, args.resource, args.progress_file)
        return 0
    except (KeyboardInterrupt, EOFError):
        return 130
    except Exception as exc:
        if args.progress_file is not None:
            try:
                _progress(args.progress_file, "failed", [])
            except OSError:
                pass
        # Do not expose backend error messages, tracebacks, or entered values.
        code = str(exc) if isinstance(exc, CredentialError) else type(exc).__name__
        print(json.dumps({"error": code}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
