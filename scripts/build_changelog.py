#!/usr/bin/env python3
"""Generate changelog.json by diffing current data.json against HEAD:data.json."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_FILE = Path("data.json")
CHANGELOG_FILE = Path("changelog.json")

FIELDS = [
    "총보수",
    "기타비용",
    "매매중개수수료",
    "실부담비용",
]


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_previous_data_from_git() -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["git", "show", "HEAD:data.json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        payload = json.loads(result.stdout)
        return payload if isinstance(payload, list) else []
    except Exception:
        return []


def to_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        cleaned = str(value).replace(",", "").replace("%", "").strip()
        if cleaned == "":
            return None
        return float(cleaned)
    except Exception:
        return None


def row_key(row: dict[str, Any]) -> tuple[str, str]:
    code = str(row.get("종목코드", "")).strip()
    name = str(row.get("종목명", "")).strip()
    return code, name


def make_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}

    for row in rows:
        key = row_key(row)
        if not key[0] and not key[1]:
            continue
        index[key] = row

    return index


def build_changes(
    prev_rows: list[dict[str, Any]],
    curr_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prev_index = make_index(prev_rows)
    curr_index = make_index(curr_rows)

    changes: list[dict[str, Any]] = []

    for key, curr_row in curr_index.items():
        prev_row = prev_index.get(key)
        if not prev_row:
            continue

        for field in FIELDS:
            before = to_float(prev_row.get(field))
            after = to_float(curr_row.get(field))

            if before is None and after is None:
                continue

            if before != after:
                changes.append(
                    {
                        "code": key[0],
                        "name": key[1],
                        "field": field,
                        "before": before,
                        "after": after,
                    }
                )

    changes.sort(key=lambda item: (item["code"], FIELDS.index(item["field"])))
    return changes


def write_changelog(entries: list[dict[str, Any]]) -> None:
    CHANGELOG_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    current_data = read_json_file(DATA_FILE, [])
    if not isinstance(current_data, list):
        current_data = []

    changelog_entries = read_json_file(CHANGELOG_FILE, [])
    if not isinstance(changelog_entries, list):
        changelog_entries = []

    previous_data = read_previous_data_from_git()
    changes = build_changes(previous_data, current_data)

    if not changes:
        if not CHANGELOG_FILE.exists():
            write_changelog([])
            print("[changelog] created empty changelog.json")
        else:
            print("[changelog] no changes detected; kept existing changelog.json")
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    month = today[:7]

    new_entry = {
        "month": month,
        "updatedAt": today,
        "changes": changes,
    }

    if changelog_entries:
        last_entry = changelog_entries[-1]
        if (
            isinstance(last_entry, dict)
            and last_entry.get("updatedAt") == today
            and last_entry.get("changes") == changes
        ):
            print("[changelog] latest entry already matches today's changes")
            return 0

        if isinstance(last_entry, dict) and last_entry.get("updatedAt") == today:
            changelog_entries[-1] = new_entry
            write_changelog(changelog_entries)
            print("[changelog] updated today's existing entry")
            return 0

    changelog_entries.append(new_entry)
    write_changelog(changelog_entries)
    print(f"[changelog] appended {len(changes)} changes for {today}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
