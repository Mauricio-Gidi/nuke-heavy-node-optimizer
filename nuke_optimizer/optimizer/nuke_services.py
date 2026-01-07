"""Nuke-facing services for the Optimizer tool.

Provides small, focused helpers that talk directly to the Nuke Python API
to collect class statistics, locate “heavy” nodes with a disable knob,
perform bulk enable/disable/toggle operations, and inspect the user's
current selection.

Repo-wide correctness constraints addressed here:
- Global node discovery: node scanning is performed from the script root
  and includes nodes inside Group nodes (recursively), independent of the
  current UI/context group.
"""

from __future__ import annotations

import logging
from typing import Iterable

try:
    # Python 3.8+
    from typing import Literal
except Exception:  # pragma: no cover - Python 3.7 (Nuke 13.x)
    from typing_extensions import Literal  # type: ignore


logger = logging.getLogger(__name__)


def _iter_all_nodes_global(nuke) -> list:
    """Return all nodes in the script, including nodes inside Groups.

    Uses nuke.allNodes(group=nuke.root(), recurseGroups=True) when
    available. Falls back to a manual group-walk if needed.

    Args:
        nuke: Imported Nuke module.

    Returns:
        list: List of Node objects.
    """
    # Preferred: explicit root + recursive group traversal.
    try:
        return list(nuke.allNodes(group=nuke.root(), recurseGroups=True))
    except TypeError:
        # Older/odd bindings may not accept these keywords.
        pass
    except Exception as e:
        logger.debug("nuke.allNodes(group=root, recurseGroups=True) failed: %s", e)

    # Secondary: attempt recursion with root as the current context.
    try:
        with nuke.root():
            return list(nuke.allNodes(recurseGroups=True))
    except TypeError:
        pass
    except Exception as e:
        logger.debug("nuke.allNodes(recurseGroups=True) in root context failed: %s", e)

    # Final fallback: manual recursive walk of Group-like nodes.
    nodes_out = []
    seen = set()

    def _walk(group_node) -> None:
        try:
            with group_node:
                for node in nuke.allNodes():
                    node_id = id(node)
                    if node_id in seen:
                        continue
                    seen.add(node_id)
                    nodes_out.append(node)

                    try:
                        cls = node.Class()
                    except Exception:
                        cls = ""

                    # Recurse into common container node types.
                    if cls in ("Group", "Gizmo", "LiveGroup"):
                        _walk(node)
        except Exception as e:
            # Never hard-fail traversal; keep best-effort behavior.
            logger.debug("Group traversal failed in %r: %s", group_node, e)

    try:
        _walk(nuke.root())
    except Exception as e:
        logger.debug("Manual traversal from root failed: %s", e)

    return nodes_out


def class_stats(classes: Iterable[str]) -> dict[str, dict[str, int]]:
    """Return per-class node statistics for the current Nuke script (global scope).

    For each class name in ``classes``, this function counts how many nodes
    of that class exist in the script (including inside Groups and nested
    Groups) and how many have their ``disable`` knob set to a truthy value.

    If the Nuke API is not available (for example when running outside
    a Nuke session), the function returns a mapping with all totals and
    disabled counts set to zero.

    Args:
        classes: Iterable of Nuke node class names to inspect.

    Returns:
        dict[str, dict[str, int]]: Mapping of the form::

            {
                "ClassName": {
                    "total": <int>,     # number of nodes of that class
                    "disabled": <int>,  # number whose 'disable' is True
                },
                ...
            }
    """
    nuke = _require_nuke()
    stats: dict[str, dict[str, int]] = {}

    if nuke is None:
        for cls in classes:
            stats[cls] = {"total": 0, "disabled": 0}
        return stats

    # Build once; filter in Python so group recursion remains correct
    # even if nuke.allNodes(filter=..., recurseGroups=True) has quirks
    # in certain Nuke versions.
    all_nodes = _iter_all_nodes_global(nuke)

    for cls in classes:
        total = 0
        disabled = 0

        for node in all_nodes:
            try:
                if node.Class() != cls:
                    continue
            except Exception:
                continue

            total += 1
            try:
                if bool(node["disable"].value()):
                    disabled += 1
            except Exception as e:
                node_name = getattr(node, "name", lambda: "<unnamed>")()
                logger.debug(
                    "Ignoring node %s (class %s) for disabled-count: no usable "
                    "'disable' knob (%s)",
                    node_name,
                    cls,
                    e,
                )

        stats[cls] = {"total": total, "disabled": disabled}

    return stats


def _get_target_nodes():
    """Return nodes that are both configured as heavy and currently toggled.

    A "target" node is defined as:

    - Its Class() is present in the stored configuration's `classes` list.
    - That class name is also present in the `toggled` list.
    - The node exposes a `disable` knob (so it can be safely modified).

    Node discovery is global and recursive: nodes inside Groups (and nested
    Groups) are included regardless of current UI context.

    Returns:
        list: List of Nuke node objects that match the criteria above.
        If the Nuke API is not available or there are no matching
        classes, an empty list is returned.
    """
    nuke = _require_nuke()
    if nuke is None:
        return []

    # Import here to minimize import-time side effects.
    from optimizer import storage, defaults

    data = storage.safe_load_or_default()
    classes = set(data.get("classes", list(defaults.RENDER_INTENSIVE_NODES)))
    toggled = set(data.get("toggled", []))
    targets = classes & toggled
    if not targets:
        logger.info("No configured/toggled classes for heavy-node operations.")
        return []

    nodes_out = []
    for node in _iter_all_nodes_global(nuke):
        try:
            cls = node.Class()
        except Exception:
            continue

        if cls not in targets:
            continue

        try:
            _ = node["disable"]  # must have a disable knob
        except Exception:
            node_name = getattr(node, "name", lambda: "<unnamed>")()
            logger.debug(
                "Skipping node %s (class %s): no 'disable' knob.",
                node_name,
                cls,
            )
            continue

        nodes_out.append(node)

    return nodes_out


def apply_heavy_nodes(action: Literal["disable", "enable", "toggle"]) -> dict:
    """Apply a bulk operation to all configured/toggled heavy nodes.

    This function centralises the logic for enabling, disabling or
    toggling the ``disable`` knob on every "heavy" node in the current
    script.

    The action is interpreted as follows:

    - ``"disable"`` - set ``disable=True`` on all target nodes.
    - ``"enable"`` - set ``disable=False`` on all target nodes.
    - ``"toggle"`` - inspect the target nodes; if any are currently
      enabled (``disable=False``) then they will all be disabled,
      otherwise they will all be enabled.

    Args:
        action: One of ``"disable"``, ``"enable"`` or ``"toggle"`` to
            select the desired behaviour.

    Returns:
        dict: Summary of what happened, shaped like::

            {
                "action": "disabled" | "enabled",
                "changed": <int>,  # how many nodes actually changed state
                "total": <int>,    # how many nodes were considered
            }

        When no target nodes are found, ``"changed"`` and ``"total"``
        will both be zero and ``"action"`` will default to ``"disabled"``.
    """
    nodes = _get_target_nodes()
    total = len(nodes)
    if total == 0:
        logger.info(
            "No heavy nodes matched configured/toggled classes; nothing to %s.",
            action,
        )
        return {"action": "disabled", "changed": 0, "total": 0}

    # Determine target disable state.
    if action == "toggle":
        # If any target node is enabled (disable=False), disable all; else enable all.
        any_enabled = False
        for node in nodes:
            try:
                if not bool(node["disable"].value()):
                    any_enabled = True
                    break
            except Exception as e:
                node_name = getattr(node, "name", lambda: "<unnamed>")()
                logger.debug(
                    "Ignoring node %s while determining toggle target: %s",
                    node_name,
                    e,
                )
        target_disable = any_enabled
    else:
        target_disable = action == "disable"

    changed = 0
    for node in nodes:
        try:
            knob = node["disable"]
            if bool(knob.value()) != target_disable:
                knob.setValue(bool(target_disable))
                changed += 1
        except Exception as e:
            node_name = getattr(node, "name", lambda: "<unnamed>")()
            logger.warning(
                "Could not change 'disable' on node %s (action=%s): %s",
                node_name,
                action,
                e,
            )

    return {
        "action": "disabled" if target_disable else "enabled",
        "changed": changed,
        "total": total,
    }


def heavy_nodes(toggle: bool = True) -> dict:
    """Compatibility wrapper for legacy heavy-node behaviour.

    Historically this function accepted a boolean to control the
    operation:

    - `toggle=True`  → enable heavy nodes (set `disable=False`).
    - `toggle=False` → disable heavy nodes (set `disable=True`).

    This wrapper keeps that behaviour intact while delegating the real
    work to `apply_heavy_nodes()`.

    Args:
        toggle: Legacy flag controlling whether to enable or disable.

    Returns:
        dict: The same summary dictionary as returned by `apply_heavy_nodes()`.
    """
    return apply_heavy_nodes("enable" if toggle else "disable")


def toggle_heavy_nodes() -> dict:
    """Toggle heavy nodes based on the current scene state.

    If any configured and toggled heavy node is currently enabled, all heavy
    nodes will be disabled. Otherwise, all heavy nodes will be enabled.

    Returns:
        dict: The same summary dictionary as returned by `apply_heavy_nodes()`.
    """
    return apply_heavy_nodes("toggle")


def selected_class_names() -> list[str]:
    """Collect unique node class names from the current selection.

    Queries Nuke for the user's currently selected nodes and extracts a
    sorted list of their Class() values, ignoring empty or whitespace
    names.

    If the Nuke API is not available, an empty list is returned.

    Returns:
        list[str]: Sorted list of unique class names in the selection.
    """
    nuke = _require_nuke()
    if nuke is None:
        return []

    nodes = nuke.selectedNodes()
    classes = sorted({getattr(n, "Class", lambda: "")().strip() for n in nodes} - {""})
    if not classes:
        logger.info("No selected nodes with a non-empty Class() in the current Nuke script.")
    return classes


def _require_nuke():
    """Import and return the Nuke Python module if available.

    Returns the imported ``nuke`` module, or ``None`` if unavailable.
    """
    try:
        import nuke  # type: ignore
    except Exception as e:  # pragma: no cover - environment dependent
        logger.error(
            "Nuke API is not available; Optimizer heavy-node operations will be skipped. (%s)",
            e,
        )
        return None
    return nuke
