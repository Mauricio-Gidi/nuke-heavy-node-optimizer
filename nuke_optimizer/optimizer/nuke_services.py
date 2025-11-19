"""Nuke-facing services for the Optimizer tool.

Provides the small, focused helpers that talk directly to the Nuke
Python API to collect class statistics, locate “heavy” nodes with a
disable knob, perform bulk enable/disable/toggle operations, and
inspect the user's current selection.

All interactions with the Nuke API are intentionally defensive: errors
are logged and swallowed where possible so the rest of the tool remains
robust even when scripts contain unusual or broken nodes.
"""

from typing import Literal, Iterable
import logging


logger = logging.getLogger(__name__)


def class_stats(classes: Iterable[str]) -> dict[str, dict[str, int]]:
    """Return per-class node statistics for the current Nuke script.

    For each class name in ``classes``, this function counts how many
    nodes of that class exist in the current script and how many of
    those have their ``disable`` knob set to a truthy value.

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
        # When Nuke is not present, we still return a predictable shape so
        # callers can safely render the UI with zeros.
        for cls in classes:
            stats[cls] = {"total": 0, "disabled": 0}
        return stats

    # Query each class independently, protecting against bad classes or
    # odd nodes that may not expose 'disable' as expected.
    for cls in classes:

        total = 0
        disabled = 0

        try:
            # Use the filter to avoid scanning unrelated nodes.
            for node in nuke.allNodes(filter=cls):
                total += 1
                try:
                    if bool(node["disable"].value()):
                        disabled += 1
                except Exception as e:
                    # No disable knob or not readable → log and ignore for
                    # disabled count so that one broken node does not poison
                    # the entire class statistics.
                    node_name = getattr(node, "name", lambda: "<unnamed>")()
                    logger.debug(
                        "Ignoring node %s (class %s) for disabled-count: no usable "
                        "'disable' knob (%s)",
                        node_name,
                        cls,
                        e,
                    )
        except Exception as e:
            # Bad class or other Nuke error → leave zeros but log it so the
            # caller understands why stats look empty for that class.
            logger.warning(
                "Failed to collect stats for class %s via nuke.allNodes: %s",
                cls,
                e,
            )

        stats[cls] = {"total": total, "disabled": disabled}

    return stats


def _get_target_nodes():
    """Return nodes that are both configured as heavy and currently toggled.

    A "target" node is defined as:

    - Its `Class()` is present in the stored configuration's `classes` list.
    - That class name is also present in the `toggled` list.
    - The node exposes a `disable` knob (so it can be safely modified).

    The function reads configuration via `optimizer.storage` and
    `optimizer.defaults`, then queries Nuke using `nuke.allNodes(filter=cls)`
    for each relevant class.

    Returns:
        list: List of Nuke node objects that match the criteria above.
        If the Nuke API is not available or there are no matching
        classes, an empty list is returned.
    """
    nuke = _require_nuke()
    if nuke is None:
        return []

    # Import here to avoid importing storage/defaults if this module is
    # used in a limited context (and to minimize import-time side effects).
    from optimizer import storage, defaults

    data = storage.safe_load_or_default()
    classes = set(data.get("classes", list(defaults.RENDER_INTENSIVE_NODES)))
    toggled = set(data.get("toggled", []))
    targets = classes & toggled
    if not targets:
        logger.info("No configured/toggled classes for heavy-node operations.")
        return []

    nodes_out = []
    for cls in targets:
        # For each class name, attempt to get all nodes of that class.
        try:
            class_nodes = nuke.allNodes(filter=cls)
        except Exception as e:
            logger.warning(
                "Skipping class %s: nuke.allNodes(filter=%s) failed (%s)",
                cls,
                cls,
                e,
            )
            continue

        # Filter down to nodes that actually have a 'disable' knob.
        for node in class_nodes:
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
        # We toggle based on whether there is at least one enabled node:
        # if any node is currently enabled (disable=False), the operation
        # will disable all; otherwise it will enable all.
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
                continue
        target_disable = any_enabled
    else:
        target_disable = action == "disable"

    changed = 0
    for node in nodes:
        try:
            knob = node["disable"]
            # Only touch nodes whose state actually needs to change.
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
            continue

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
    sorted list of their ``Class()`` values, ignoring empty or whitespace
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
        logger.info(
            "No selected nodes with a non-empty Class() in the current Nuke script."
        )
    return classes


def _require_nuke():
    """Import and return the Nuke Python module if available.

    This helper centralises the ``import nuke`` pattern and ensures that
    failures are logged consistently. It allows this package to be
    imported or tested outside of a Nuke session without raising
    ``ImportError``; callers simply receive ``None`` instead and can
    decide how to handle that case.

    Returns:
        The imported ``nuke`` module, or ``None`` if unavailable.

    Side effects:
        Logs an error when the Nuke API cannot be imported so callers
        can inspect the log file instead of seeing an unhandled error.
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
