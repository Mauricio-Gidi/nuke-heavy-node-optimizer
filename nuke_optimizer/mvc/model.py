"""In-memory model for the Optimizer class list."""

from __future__ import annotations

from typing import Iterable, Optional


class Model:
    """Authoritative, ordered set of class names.

    The model stores class names in two parallel structures:

    * ``_items`` - a list preserving insertion / UI order.
    * ``_set`` - a set mirroring the same contents for O(1) membership
      checks.

    The controller should treat this as the single source of truth for
    the class list while the UI is open.
    """

    def __init__(self) -> None:
        """Initialize an empty model with no class names."""
        self._items: list[str] = []
        self._set: set[str] = set()

    def as_list(self) -> tuple[str, ...]:
        """Return class names as an immutable tuple in UI order.

        Returns:
            tuple[str, ...]: Current class names in insertion/UI order.
        """
        return tuple(self._items)

    def replace_all(self, list_of_classes: Iterable[str]) -> None:
        """Replace all class names with a new ordered collection.

        Incoming values are normalized defensively:

        * Non-strings are ignored.
        * Strings are stripped of surrounding whitespace.
        * Empty results are discarded.
        * Duplicates are removed while preserving the first occurrence.

        If the new normalized sequence is identical to the current one,
        this is a no-op to avoid unnecessary churn for callers.

        Args:
            list_of_classes: Iterable of class names to store.
        """
        incoming: list[str] = []
        seen: set[str] = set()
        for x in list_of_classes:
            if not isinstance(x, str):
                continue
            name = x.strip()
            if not name or name in seen:
                continue
            seen.add(name)
            incoming.append(name)

        if incoming == self._items:
            return

        self._items = incoming
        self._set = set(incoming)

    def add_class(self, name: str) -> tuple[bool, Optional[str]]:
        """Add one class name if valid and not already present.

        Args:
            name: Candidate class name.

        Returns:
            tuple[bool, Optional[str]]: A ``(ok, err_code)`` pair where:

                * ``None`` - success.
                * ``'type'`` - ``name`` is not a string.
                * ``'empty'`` - the trimmed name is empty.
                * ``'exists'`` - the class name already exists.
        """
        if not isinstance(name, str):
            return False, "type"
        n = name.strip()
        if not n:
            return False, "empty"
        if n in self._set:
            return False, "exists"
        self._items.append(n)
        self._set.add(n)
        return True, None

    def remove_classes(self, list_of_names: Iterable[str]) -> dict[str, object]:
        """Remove any classes whose names appear in ``list_of_names``.

        Non-string values are ignored. String values are stripped of
        whitespace and empty results are discarded before comparison.

        Args:
            list_of_names: Iterable of class names to remove.

        Returns:
            dict[str, object]: Summary mapping with:

                * ``'removed'``: number of classes actually removed.
                * ``'changed'``: ``True`` if the model was modified,
                  ``False`` otherwise.
        """
        targets = {name.strip() for name in list_of_names if isinstance(name, str) and name.strip()}
        if not targets:
            return {"removed": 0, "changed": False}
        remaining_items = [class_name for class_name in self._items if class_name not in targets]
        removed = len(self._items) - len(remaining_items)
        if removed == 0:
            return {"removed": 0, "changed": False}
        self._items = remaining_items
        self._set = set(remaining_items)
        return {"removed": removed, "changed": True}
