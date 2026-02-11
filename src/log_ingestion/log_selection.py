"""Log listing + selection helpers for Rapid7 Log Search.
Separated from CLI so selection logic is testable without interactive prompts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogSetDescriptor:
    """Minimal descriptor for a Log Set as returned by the management API."""

    id: str
    name: str
    description: str = ""
    # Optional embedded membership list (from `logs_info` in the logsets response).
    logs: Optional[list["LogDescriptor"]] = None


@dataclass(frozen=True)
class LogDescriptor:
    id: str
    name: str


def _choose_id(items: list[object], user_choice: str, *, get_id) -> str:
    if not items:
        raise ValueError("No items available to select")

    choice = (user_choice or "").strip()
    if not choice:
        raise ValueError("Empty selection")

    if choice.isdigit():
        idx = int(choice)
        if idx < 1 or idx > len(items):
            raise ValueError("Selection out of range")
        return str(get_id(items[idx - 1]))

    for item in items:
        if str(get_id(item)) == choice:
            return choice

    raise ValueError("Selection did not match any id")


def choose_log_set_id(log_sets: list[LogSetDescriptor], user_choice: str) -> str:
    """Resolve user's choice into a log set id.

    Accepts:
    - 1-based index into the displayed list
    - a direct log set id

    Raises:
        ValueError: invalid selection, empty log_sets, or empty choice.
    """

    return _choose_id(log_sets, user_choice, get_id=lambda x: x.id)


def choose_log_id(logs: list[LogDescriptor], user_choice: str) -> str:
    """Resolve user's choice into a log id.
    Accepts:
    - 1-based index into the displayed list
    - a direct log id
    Raises:
        ValueError: invalid selection, empty logs, or empty choice.
    """

    return _choose_id(logs, user_choice, get_id=lambda x: x.id)
