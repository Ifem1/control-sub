#!/usr/bin/env python3
"""Reproducibly write or verify SHA256 hashes for tracked repository files.

The manifest excludes itself. Only Git-tracked files are included, so ignored
caches, local dependencies, virtual environments and temporary outputs stay out.
Stage intended new source files before running this script.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "SOURCE_MANIFEST.sha256"
EXCLUDED_PARTS = {".git", "node_modules", ".venv", ".pytest_cache", "__pycache__", "artifacts"}
EXCLUDED_SUFFIXES = {".pem", ".key", ".wallet"}


def tracked_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached"], cwd=ROOT,
        check=True, stdout=subprocess.PIPE,
    )
    paths = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8")
        path = Path(relative)
        if relative == "SOURCE_MANIFEST.sha256":
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        name = path.name.lower()
        if name.startswith(".env") or path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        paths.append(path)
    return sorted(paths, key=lambda item: item.as_posix())


def expected_text() -> str:
    rows = []
    for relative in tracked_paths():
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        rows.append(f"{digest}  {relative.as_posix()}")
    return "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true", help="replace SOURCE_MANIFEST.sha256")
    action.add_argument("--check", action="store_true", help="verify every listed path and digest")
    args = parser.parse_args()
    expected = expected_text()
    if args.write:
        MANIFEST.write_text(expected, encoding="utf-8", newline="\n")
        print(f"wrote {len(expected.splitlines())} tracked file hashes")
        return 0
    actual = MANIFEST.read_text(encoding="utf-8")
    if actual != expected:
        print("SOURCE_MANIFEST.sha256 is stale; stage intended source files, then run --write", file=sys.stderr)
        return 1
    print(f"verified {len(expected.splitlines())} tracked file hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
