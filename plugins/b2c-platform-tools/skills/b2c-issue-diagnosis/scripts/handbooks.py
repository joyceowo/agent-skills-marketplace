"""Persist non-secret handbook targets and explicit auto-maintenance preferences.

No Notion calls or permission grants. Status never creates a file; missing targets
return exit 2. Keep this independent of the v1 source-path settings format.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from uuid import UUID


KINDS = ("common-issue", "access-request")
SYSTEM_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
UUID_TEXT = re.compile(r"(?:[0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})\Z")
TARGET_KEYS = {"page_id", "database_id", "data_source_url", "auto_maintain", "types"}


class HandbookError(Exception):
    """Only stable codes are exposed; never echo arbitrary config contents."""


def default_config_file() -> Path:
    return Path.home() / ".local" / "share" / "b2c-diagnostics" / "handbooks.json"


def validate_system(system: str) -> None:
    if not isinstance(system, str) or not SYSTEM_ID.fullmatch(system):
        raise HandbookError("invalid_system")


def notion_id(value: str) -> str:
    if not isinstance(value, str) or not UUID_TEXT.fullmatch(value):
        raise HandbookError("invalid_notion_id")
    return str(UUID(value))


def validate_target(target: object) -> dict:
    if not isinstance(target, dict) or set(target) != TARGET_KEYS:
        raise HandbookError("invalid_handbook_target")
    notion_id(target["page_id"])
    notion_id(target["database_id"])
    source = target["data_source_url"]
    if not isinstance(source, str) or not source.startswith("collection://"):
        raise HandbookError("invalid_data_source_url")
    notion_id(source.removeprefix("collection://"))
    kinds = target["types"]
    if (type(target["auto_maintain"]) is not bool or not isinstance(kinds, list)
            or not kinds or any(not isinstance(kind, str) or kind not in KINDS for kind in kinds)
            or len(set(kinds)) != len(kinds)):
        raise HandbookError("invalid_handbook_preferences")
    return target


def read_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"version": 1, "systems": {}}
    except (OSError, ValueError):
        raise HandbookError("handbooks_unreadable_or_invalid") from None
    if (not isinstance(data, dict) or set(data) != {"version", "systems"}
            or type(data["version"]) is not int or data["version"] != 1
            or not isinstance(data["systems"], dict)):
        raise HandbookError("invalid_handbooks_config")
    for system, target in data["systems"].items():
        validate_system(system)
        validate_target(target)
    return data


def write_config(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, prefix=".handbooks-",
                                         suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def status(path: Path, system: str) -> dict:
    validate_system(system)
    target = read_config(path)["systems"].get(system)
    return {"system": system, "config_file": str(path), "configured": target is not None,
            "auto_maintain": target["auto_maintain"] if target else False,
            "target": target, "remote_access": "not_checked"}


def set_target(path: Path, system: str, page_id: str, database_id: str,
               data_source_url: str, auto_maintain: bool, kinds: list[str]) -> dict:
    validate_system(system)
    target = {"page_id": notion_id(page_id), "database_id": notion_id(database_id),
              "data_source_url": data_source_url, "auto_maintain": auto_maintain,
              "types": kinds}
    validate_target(target)
    target["data_source_url"] = "collection://" + notion_id(data_source_url.removeprefix("collection://"))
    data = read_config(path)
    data["systems"][system] = target
    write_config(path, data)
    return status(path, system)


def disable(path: Path, system: str) -> dict:
    validate_system(system)
    data = read_config(path)
    target = data["systems"].get(system)
    if target and target["auto_maintain"]:
        target["auto_maintain"] = False
        write_config(path, data)
    return status(path, system)


def clear(path: Path, system: str) -> dict:
    validate_system(system)
    data = read_config(path)
    removed = data["systems"].pop(system, None) is not None
    if removed:
        write_config(path, data)
    return {**status(path, system), "removed": removed}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "set", "disable", "clear"))
    parser.add_argument("--system", required=True)
    parser.add_argument("--config-file", type=Path, default=None)
    parser.add_argument("--page-id")
    parser.add_argument("--database-id")
    parser.add_argument("--data-source-url")
    parser.add_argument("--auto-maintain", choices=("on", "off"))
    parser.add_argument("--types", nargs="+", choices=KINDS)
    args = parser.parse_args(argv)
    path = args.config_file if args.config_file is not None else default_config_file()
    if not path.is_absolute():
        parser.error("--config-file must be absolute")
    supplied = (args.page_id, args.database_id, args.data_source_url, args.auto_maintain)
    if args.action == "set" and not all(supplied):
        parser.error("set requires page, database, data source, and explicit --auto-maintain on|off")
    if args.action != "set" and (any(value is not None for value in supplied) or args.types is not None):
        parser.error("target options are only valid for set")
    try:
        if args.action == "set":
            result = set_target(path, args.system, args.page_id, args.database_id,
                                args.data_source_url, args.auto_maintain == "on",
                                args.types if args.types is not None else list(KINDS))
        elif args.action == "disable":
            result = disable(path, args.system)
        elif args.action == "clear":
            result = clear(path, args.system)
        else:
            result = status(path, args.system)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["configured"] or args.action == "clear" else 2
    except (KeyboardInterrupt, EOFError):
        return 130
    except Exception as exc:
        code = str(exc) if isinstance(exc, HandbookError) else type(exc).__name__
        print(json.dumps({"error": code}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
