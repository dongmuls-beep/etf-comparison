#!/usr/bin/env python3
"""Sync changelog.json from production server before local commit."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_URLS = [
    "https://etfsave.life/changelog.json",
    "https://www.etfsave.life/changelog.json",
]
TARGET_FILE = Path("changelog.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download latest changelog.json from web server."
    )
    parser.add_argument(
        "--url",
        action="append",
        default=[],
        help="Remote changelog URL. May be provided multiple times.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--stage",
        action="store_true",
        help="Run git add for changelog.json after sync.",
    )
    parser.add_argument(
        "--allow-fail",
        action="store_true",
        help="Do not fail when download/parse fails.",
    )
    return parser.parse_args()


def fetch_remote_changelog(url: str, timeout: float) -> list[dict]:
    request = Request(
        url=url,
        headers={"User-Agent": "etfsave-life-sync-server-changelog/1.0"},
        method="GET",
    )

    with urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise RuntimeError(f"unexpected HTTP status: {status}")

        payload = response.read().decode("utf-8")
        data = json.loads(payload)

    if not isinstance(data, list):
        raise ValueError("remote changelog.json is not a list")

    return data


def resolve_candidate_urls(args: argparse.Namespace) -> list[str]:
    env_url = os.getenv("CHANGELOG_REMOTE_URL", "").strip()

    urls: list[str] = []
    if args.url:
        urls.extend([url.strip() for url in args.url if url and url.strip()])
    if env_url:
        urls.append(env_url)
    urls.extend(DEFAULT_URLS)

    deduped: list[str] = []
    seen = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


def write_if_changed(path: Path, data: list[dict]) -> bool:
    serialized = json.dumps(data, ensure_ascii=False, indent=2) + "\n"

    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current == serialized:
            return False

    path.write_text(serialized, encoding="utf-8")
    return True


def stage_file(path: Path) -> None:
    subprocess.run(["git", "add", str(path)], check=True)


def main() -> int:
    args = parse_args()
    allow_fail = args.allow_fail or os.getenv("ALLOW_STALE_CHANGELOG") == "1"
    urls = resolve_candidate_urls(args)
    if not urls:
        print("[changelog-sync] no candidate URL configured", file=sys.stderr)
        return 1

    try:
        remote_data = None
        active_url = ""
        last_error: Exception | None = None

        for url in urls:
            try:
                remote_data = fetch_remote_changelog(url, args.timeout)
                active_url = url
                break
            except (HTTPError, URLError, ValueError, RuntimeError) as exc:
                last_error = exc

        if remote_data is None:
            if last_error is None:
                raise RuntimeError("unable to download remote changelog")
            raise last_error

        changed = write_if_changed(TARGET_FILE, remote_data)

        if args.stage:
            stage_file(TARGET_FILE)

        if changed:
            print(f"[changelog-sync] updated from {active_url}")
        else:
            print(f"[changelog-sync] already up to date ({active_url})")
        return 0
    except (HTTPError, URLError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        message = f"[changelog-sync] failed: {exc}"
        if allow_fail:
            print(f"{message} (ignored)")
            return 0
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
