"""Local source paths only; repository defaults belong to references/systems/.

No network, credential access, cloning, or business-source changes. Exit 2 means
the selected path needs user input; status/resolve never create settings.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile


ROLES = ("frontend", "backend")
SYSTEM_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SYSTEMS_ROOT = Path(__file__).resolve().parents[1] / "references" / "systems"


class SettingsError(Exception):
    """Stable error codes without arbitrary file contents or exception details."""


def default_settings_file() -> Path:
    # Keep the existing diagnostics data directory across plugin updates.
    return Path.home() / ".local" / "share" / "b2c-diagnostics" / "settings.json"


def validate_system_id(system: str) -> None:
    if not SYSTEM_ID.fullmatch(system):
        raise SettingsError("invalid_system")


def load_system(system: str) -> dict:
    validate_system_id(system)
    try:
        data = json.loads((SYSTEMS_ROOT / system / "system.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SettingsError("unknown_system") from None
    except (OSError, ValueError):
        raise SettingsError("invalid_system_definition") from None
    if (not isinstance(data, dict) or data.get("id") != system
            or not isinstance(data.get("repositories"), dict)):
        raise SettingsError("invalid_system_definition")
    for role in ROLES:
        repo = data["repositories"].get(role)
        if (not isinstance(repo, dict) or not isinstance(repo.get("url"), str)
                or not repo["url"].startswith("https://")):
            raise SettingsError("invalid_system_definition")
    return data


def validate_settings(data: object) -> dict:
    if (not isinstance(data, dict) or set(data) != {"version", "systems"}
            or type(data["version"]) is not int or data["version"] != 1
            or not isinstance(data["systems"], dict)):
        raise SettingsError("invalid_settings")
    for system, paths in data["systems"].items():
        validate_system_id(system)
        if not isinstance(paths, dict) or set(paths) - {f"{role}_path" for role in ROLES}:
            raise SettingsError("invalid_settings")
        for value in paths.values():
            if not isinstance(value, str) or not value.strip() or "://" in value:
                raise SettingsError("invalid_settings")
            if not Path(value).is_absolute():
                raise SettingsError("invalid_settings")
    return data


def read_settings(settings_file: Path) -> dict:
    try:
        data = json.loads(settings_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"version": 1, "systems": {}}
    except (OSError, ValueError):
        raise SettingsError("settings_unreadable_or_invalid") from None
    return validate_settings(data)


def directory_path(value: str) -> Path:
    if not value.strip() or "://" in value:
        raise SettingsError("local_directory_required")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise SettingsError("absolute_path_required")
    try:
        path = path.resolve(strict=True)
        # Opening a directory checks access without scanning the project.
        with os.scandir(path):
            pass
    except (OSError, ValueError, RuntimeError):
        raise SettingsError("directory_missing_or_unreadable") from None
    return path


def path_record(value: str | None) -> dict:
    if value is None:
        return {"state": "missing", "path": None, "ready": False}
    try:
        path = directory_path(value)
    except SettingsError as exc:
        return {"state": "invalid", "path": value, "ready": False, "reason": str(exc)}
    return {"state": "ready", "path": str(path), "ready": True}


def status(settings_file: Path, system: str, roles=ROLES) -> dict:
    definition = load_system(system)
    paths = read_settings(settings_file)["systems"].get(system, {})
    selected = {role: {**path_record(paths.get(f"{role}_path")),
                       "source_url": definition["repositories"][role]["url"]}
                for role in roles}
    return {"system": system, "settings_file": str(settings_file), "paths": selected,
            "ready": all(record["ready"] for record in selected.values())}


def write_settings(settings_file: Path, data: dict) -> None:
    validate_settings(data)
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=settings_file.parent, prefix=".settings-",
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, settings_file)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def set_path(settings_file: Path, system: str, role: str, value: str) -> dict:
    load_system(system)
    path = directory_path(value)
    data = read_settings(settings_file)
    data["systems"].setdefault(system, {})[f"{role}_path"] = str(path)
    write_settings(settings_file, data)
    return status(settings_file, system, (role,))


def clear_path(settings_file: Path, system: str, role: str) -> dict:
    load_system(system)
    data = read_settings(settings_file)
    paths = data["systems"].get(system, {})
    if f"{role}_path" in paths:
        del paths[f"{role}_path"]
        write_settings(settings_file, data)
    return status(settings_file, system, (role,))


def resolve_path(settings_file: Path, system: str, role: str,
                 explicit_path: str | None = None, workspace: str | None = None) -> dict:
    definition = load_system(system)
    if explicit_path is not None:
        value, origin = explicit_path, "request"
    else:
        saved = read_settings(settings_file)["systems"].get(system, {}).get(f"{role}_path")
        value, origin = (saved, "settings") if saved is not None else (workspace, "workspace")
    record = path_record(value)
    return {"system": system, "role": role, **record,
            "origin": origin if value is not None else None,
            "source_url": definition["repositories"][role]["url"],
            "needs_input": not record["ready"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Non-secret local project path settings")
    parser.add_argument("action", choices=("status", "set-path", "clear-path", "resolve"))
    parser.add_argument("--system", required=True, help="System definition folder identifier")
    parser.add_argument("--role", choices=ROLES)
    parser.add_argument("--path", help="Local directory; never a repository URL or password")
    parser.add_argument("--workspace", help="Already confirmed role-specific workspace fallback")
    parser.add_argument("--settings-file", type=Path, help="Explicit local settings file override")
    args = parser.parse_args(argv)
    if args.action != "status" and args.role is None:
        parser.error("--role is required for this action")
    if args.action == "set-path" and args.path is None:
        parser.error("set-path requires --path")
    if args.path is not None and args.action not in ("set-path", "resolve"):
        parser.error("--path is only supported for set-path or resolve")
    if args.workspace is not None and args.action != "resolve":
        parser.error("--workspace is only supported for resolve")
    settings_file = args.settings_file or default_settings_file()
    if not settings_file.is_absolute():
        parser.error("--settings-file must be absolute")
    try:
        if args.action == "status":
            result = status(settings_file, args.system, (args.role,) if args.role else ROLES)
        elif args.action == "set-path":
            result = set_path(settings_file, args.system, args.role, args.path)
        elif args.action == "clear-path":
            result = clear_path(settings_file, args.system, args.role)
        else:
            result = resolve_path(settings_file, args.system, args.role, args.path, args.workspace)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ready"] or args.action == "clear-path" else 2
    except (KeyboardInterrupt, EOFError):
        return 130
    except Exception as exc:
        code = str(exc) if isinstance(exc, SettingsError) else type(exc).__name__
        print(json.dumps({"error": code}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
