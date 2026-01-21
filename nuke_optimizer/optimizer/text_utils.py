"""Small helpers for working with user-entered text."""

from __future__ import annotations

from typing import Iterable, Any


def unique_stripped_strings(values: Any, require_list: bool = False) -> list[str]:
    """Return unique, non-empty strings in first-seen order.

    Args:
        values: Iterable of values (typically a list of strings).
        require_list: If True, only accept a real list; otherwise return []

    Returns:
        List of unique, stripped strings. Non-strings are ignored.
    """
    if require_list and not isinstance(values, list):
        return []

    if not values:
        return []

    out: list[str] = []
    seen: set[str] = set()

    for item in values:
        if not isinstance(item, str):
            continue
        s = item.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)

    return out
