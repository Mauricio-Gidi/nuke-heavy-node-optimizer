"""Dialog helpers for the Optimizer UI.

Defines DialogService, a thin wrapper around common QMessageBox
patterns used by the controller to show user-facing dialogs without
embedding Qt-specific code throughout the rest of the application.

Centralising dialog behavior here also makes tests easier to write and
future changes to messaging or styling easier to apply in one place.

Message style guide:

- Use sentence case for dialog titles with no trailing period
  (for example, "No nodes selected", "Import failed", "Export failed").
- Use short, neutral sentences ending with a period for dialog body text
  and status messages (for example, "Select one or more nodes.",
  "No classes added.", "Preset exported.").
- Use a Unicode ellipsis (…) in labels and progress-like messages to
  indicate ongoing work (for example, "Exporting preset…").
"""

from __future__ import annotations

from typing import Optional

# Qt binding compatibility (PySide2 / PySide6) is provided repo-wide.
# Assumes mvc/qt_compat.py exists after the agreed fixes are applied.
from mvc.qt_compat import QtWidgets

# QMessageBox button enum compatibility (Qt5/PySide2 vs Qt6/PySide6)
try:
    _YES = QtWidgets.QMessageBox.StandardButton.Yes
    _NO = QtWidgets.QMessageBox.StandardButton.No
except Exception:  # pragma: no cover - depends on host Qt binding
    _YES = QtWidgets.QMessageBox.Yes
    _NO = QtWidgets.QMessageBox.No


class DialogService:
    """Simple service object for showing standard message dialogs.

    The methods provided are intentionally minimal and synchronous:
    they block until the user dismisses the dialog, just like the
    underlying QMessageBox helpers.
    """

    def info(
        self,
        parent: Optional[QtWidgets.QWidget],
        title: str,
        text: str,
    ) -> None:
        """Show an informational message box.

        Args:
            parent: Parent widget for the dialog, or ``None``.
            title: Window title for the message box.
            text: Body text displayed to the user.
        """
        QtWidgets.QMessageBox.information(parent, title, text)

    def warn(
        self,
        parent: Optional[QtWidgets.QWidget],
        title: str,
        text: str,
    ) -> None:
        """Show a warning message box.

        Args:
            parent: Parent widget for the dialog, or ``None``.
            title: Window title for the message box.
            text: Body text describing the warning.
        """
        QtWidgets.QMessageBox.warning(parent, title, text)

    def error(
        self,
        parent: Optional[QtWidgets.QWidget],
        title: str,
        text: str,
    ) -> None:
        """Show an error (critical) message box.

        Args:
            parent: Parent widget for the dialog, or ``None``.
            title: Window title for the message box.
            text: Body text describing the error.
        """
        QtWidgets.QMessageBox.critical(parent, title, text)

    def ask_yes_no(
        self,
        parent: Optional[QtWidgets.QWidget],
        title: str,
        text: str,
    ) -> bool:
        """Ask a Yes/No question and return the user's choice.

        The dialog uses ``Yes`` and ``No`` buttons, with ``No`` as the
        default. The return value is ``True`` only when the user explicitly
        clicks ``Yes``.

        Args:
            parent: Parent widget for the dialog, or ``None``.
            title: Window title for the question box.
            text: Question text presented to the user.

        Returns:
            bool: ``True`` if the user clicked ``Yes``; ``False`` if they
            clicked ``No`` or closed the dialog.
        """
        btn = QtWidgets.QMessageBox.question(
            parent,
            title,
            text,
            _YES | _NO,
            _NO,
        )
        return btn == _YES
