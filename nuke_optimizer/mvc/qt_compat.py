"""Compatibility layer for PySide2/PySide6 (Qt5/Qt6)."""

from __future__ import annotations


try:
    # Nuke 16+
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore
except Exception:  # pragma: no cover - depends on host DCC
    # Nuke 13-15
    from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore


# ItemDataRole.UserRole (Qt6) vs Qt.UserRole (Qt5)
try:
    USER_ROLE = QtCore.Qt.ItemDataRole.UserRole  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    USER_ROLE = QtCore.Qt.UserRole  # type: ignore[attr-defined]

# CheckState.Checked (Qt6) vs Qt.Checked (Qt5)
try:
    CHECKED = QtCore.Qt.CheckState.Checked  # type: ignore[attr-defined]
    UNCHECKED = QtCore.Qt.CheckState.Unchecked  # type: ignore[attr-defined]
    PARTIALLY_CHECKED = QtCore.Qt.CheckState.PartiallyChecked  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    CHECKED = QtCore.Qt.Checked  # type: ignore[attr-defined]
    UNCHECKED = QtCore.Qt.Unchecked  # type: ignore[attr-defined]
    PARTIALLY_CHECKED = QtCore.Qt.PartiallyChecked  # type: ignore[attr-defined]

# Item flags (Qt6) vs Qt.ItemIs* (Qt5)
try:
    ITEM_IS_ENABLED = QtCore.Qt.ItemFlag.ItemIsEnabled  # type: ignore[attr-defined]
    ITEM_IS_SELECTABLE = QtCore.Qt.ItemFlag.ItemIsSelectable  # type: ignore[attr-defined]
    ITEM_IS_USER_CHECKABLE = QtCore.Qt.ItemFlag.ItemIsUserCheckable  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    ITEM_IS_ENABLED = QtCore.Qt.ItemIsEnabled  # type: ignore[attr-defined]
    ITEM_IS_SELECTABLE = QtCore.Qt.ItemIsSelectable  # type: ignore[attr-defined]
    ITEM_IS_USER_CHECKABLE = QtCore.Qt.ItemIsUserCheckable  # type: ignore[attr-defined]

# Window hint (Qt6) vs Qt.WindowStaysOnTopHint (Qt5)
try:
    WINDOW_STAYS_ON_TOP_HINT = QtCore.Qt.WindowType.WindowStaysOnTopHint  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    WINDOW_STAYS_ON_TOP_HINT = QtCore.Qt.WindowStaysOnTopHint  # type: ignore[attr-defined]

# Drop action (Qt6) vs Qt.MoveAction (Qt5)
try:
    MOVE_ACTION = QtCore.Qt.DropAction.MoveAction  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    MOVE_ACTION = QtCore.Qt.MoveAction  # type: ignore[attr-defined]

# Alignment (Qt6) vs Qt.Align* (Qt5)
try:
    ALIGN_LEFT = QtCore.Qt.AlignmentFlag.AlignLeft  # type: ignore[attr-defined]
    ALIGN_RIGHT = QtCore.Qt.AlignmentFlag.AlignRight  # type: ignore[attr-defined]
    ALIGN_VCENTER = QtCore.Qt.AlignmentFlag.AlignVCenter  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    ALIGN_LEFT = QtCore.Qt.AlignLeft  # type: ignore[attr-defined]
    ALIGN_RIGHT = QtCore.Qt.AlignRight  # type: ignore[attr-defined]
    ALIGN_VCENTER = QtCore.Qt.AlignVCenter  # type: ignore[attr-defined]

# Text elide mode (Qt6) vs Qt.ElideRight (Qt5)
try:
    ELIDE_RIGHT = QtCore.Qt.TextElideMode.ElideRight  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    ELIDE_RIGHT = QtCore.Qt.ElideRight  # type: ignore[attr-defined]


# -----------------------------------------------------------------------------
# -
# -----------------------------------------------------------------------------
# Common moved symbols
# -----------------------------------------------------------------------------
# -
# -----------------------------------------------------------------------------


__all__ = [
    "QtCore",
    "QtGui",
    "QtWidgets",
    "USER_ROLE",
    "CHECKED",
    "UNCHECKED",
    "PARTIALLY_CHECKED",
    "ITEM_IS_ENABLED",
    "ITEM_IS_SELECTABLE",
    "ITEM_IS_USER_CHECKABLE",
    "WINDOW_STAYS_ON_TOP_HINT",
    "MOVE_ACTION",
    "ALIGN_LEFT",
    "ALIGN_RIGHT",
    "ALIGN_VCENTER",
    "ELIDE_RIGHT"
]
