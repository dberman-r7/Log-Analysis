"""Utilities for safely reading and updating `.env` files.

This module is intentionally dependency-free. It supports a minimal subset of
`.env` semantics needed by this repo:

- `KEY=value` assignments (unquoted or quoted)
- preserving comments and unknown lines

Governance notes:
- Never log secret values.
- Fail loudly on I/O errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class EnvUpdateResult:
    path: Path
    key: str
    updated: bool
    created: bool


def upsert_env_var(env_path: Path, key: str, value: str) -> EnvUpdateResult:
    """Insert or update `key=value` in the given `.env` file.

    Contract:
    - If the file doesn't exist, it is created containing a single assignment.
    - If `key` exists, the first occurrence is replaced and any subsequent
      duplicates are removed.
    - All other lines are preserved (including comments and blank lines).
    """

    if not key or "=" in key or "\n" in key:
        raise ValueError("Invalid env var key")
    if "\n" in value:
        raise ValueError("Invalid env var value")

    assignment = f"{key}={value}"

    if not env_path.exists():
        env_path.write_text(assignment + "\n", encoding="utf-8")
        return EnvUpdateResult(path=env_path, key=key, updated=True, created=True)

    lines = env_path.read_text(encoding="utf-8").splitlines(keepends=False)
    out: list[str] = []
    replaced = False

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out.append(line)
            continue

        k = _parse_env_key(stripped)
        if k == key:
            if not replaced:
                out.append(assignment)
                replaced = True
            # drop duplicates
            continue

        out.append(line)

    if not replaced:
        # keep original newline style: add blank line separator if file isn't empty
        if out and out[-1].strip() != "":
            out.append("")
        out.append(assignment)

    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return EnvUpdateResult(path=env_path, key=key, updated=True, created=False)


def _parse_env_key(line: str) -> Optional[str]:
    """Extract key from a `KEY=...` line. Returns None if not an assignment."""

    if "=" not in line:
        return None
    key = line.split("=", 1)[0].strip()
    if not key:
        return None
    return key
