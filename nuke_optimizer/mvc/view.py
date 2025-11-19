"""Qt-based view for the Optimizer configuration window.

Contains the passive PySide2 widgets, layouts, and small helpers used to
display and edit the list of “heavy” node classes and their statistics.

All business logic (persistence, Nuke interaction, and selection rules)
lives in the controller and model; the view exposes a small, focused API
that the controller drives via signals and slots.
"""

from PySide2 import QtWidgets, QtCore, QtGui


class CountSuffixDelegate(QtWidgets.QStyledItemDelegate):
    """List item delegate that draws a right-aligned count suffix.

    The delegate expects each item to carry:

    - Qt.UserRole       → base class name (string)
    - Qt.UserRole + 1   → disabled count (int)
    - Qt.UserRole + 2   → total count (int)

    It renders the base name on the left and a suffix like
    ``"(disabled/total disabled)"`` on the right, using the standard
    palette and selection colors.
    """

    # Space (in pixels) between left base text and right suffix.
    GAP = 8

    def paint(self, painter, option, index):
        """Paint the base text and count suffix for a list item.

        Draws the base class name left-aligned and a
        ``"(disabled/total disabled)"`` suffix right-aligned using the
        standard palette and selection colors. Data is taken from the
        item's user roles.

        Args:
            painter: Active QPainter used for drawing.
            option: Style options for the item.
            index: Model index providing base and count roles.
        """
        opt = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = opt.widget.style() if opt.widget else QtWidgets.QApplication.style()

        # Parts from roles (fallback to DisplayRole for base)
        base = index.data(QtCore.Qt.UserRole) or (opt.text or "")
        d = index.data(QtCore.Qt.UserRole + 1)
        t = index.data(QtCore.Qt.UserRole + 2)
        suffix = (
            f"({d}/{t} disabled)" if isinstance(d, int) and isinstance(t, int) else ""
        )

        # Let the style draw background/selection/focus, but not the text
        text_backup = opt.text
        opt.text = ""
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, opt, painter, opt.widget)
        opt.text = text_backup

        rect = style.subElementRect(
            QtWidgets.QStyle.SE_ItemViewItemText, opt, opt.widget
        )
        fm = opt.fontMetrics

        # Right rect fits the suffix; left takes the remaining space
        if suffix:
            rw = fm.horizontalAdvance(suffix)
            right_rect = QtCore.QRect(
                rect.right() - rw,
                rect.top(),
                rw,
                rect.height(),
            )
            left_rect = QtCore.QRect(
                rect.left(),
                rect.top(),
                max(0, right_rect.left() - rect.left() - self.GAP),
                rect.height(),
            )
        else:
            right_rect = QtCore.QRect(
                rect.right(),
                rect.top(),
                0,
                rect.height(),
            )
            left_rect = rect

        # Elide the base text so it never overlaps the count suffix.
        left_text = fm.elidedText(
            base,
            QtCore.Qt.ElideRight,
            max(0, left_rect.width()),
        )

        enabled = bool(opt.state & QtWidgets.QStyle.State_Enabled)
        role = (
            QtGui.QPalette.HighlightedText
            if (opt.state & QtWidgets.QStyle.State_Selected)
            else QtGui.QPalette.Text
        )

        style.drawItemText(
            painter,
            left_rect,
            QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
            opt.palette,
            enabled,
            left_text,
            role,
        )
        if suffix:
            style.drawItemText(
                painter,
                right_rect,
                QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight,
                opt.palette,
                enabled,
                suffix,
                role,
            )


class View(QtWidgets.QWidget):
    """
    Define the passive view for the Optimizer configuration window.

    The view defines only the widgets, layout, and small helpers used
    to read and write UI state.

    The controller is responsible for:

    - Wiring signals to actions.
    - Updating the model and storage.
    - Calling the public methods exposed below.
    """

    # Emitted when the window is closed, so the controller can persist state.
    closed = QtCore.Signal()

    def __init__(self):
        """Initialize the view, building widgets, layout, and base styling."""
        super().__init__()
        # Build widgets, layout, and basic styling while keeping __init__ small.
        self.setup_ui()
        self.create_widgets()
        self.create_layout()
        self.set_style()
        self._last_stats: dict[str, dict[str, int]] = {}

    # --------------------------------------------------------------------- #
    # Public API (controller calls)                                         #
    # --------------------------------------------------------------------- #

    def set_items(self, names: list[str], *, checked: bool = True) -> None:
        """Replace the entire list with the given class names.

        Clears existing rows, adds one row per name, and applies the same
        initial checked state to every row. Cached per-class counts are
        reapplied afterwards.

        Args:
            names: Class names to show, in row order.
            checked: Initial checkbox state for every row.
        """
        # Prevent N itemChanged emissions during bulk rebuild.
        blocker = QtCore.QSignalBlocker(self.list_widget)
        try:
            self.list_widget.clear()
            for name in names:
                self._add_list_item(name, checked=checked)
        finally:
            del blocker

        # Re-apply cached counts so the delegate has its roles again.
        if self._last_stats:
            self.set_counts(self._last_stats)

        # Single, cheap recompute of select-all state.
        self.sync_select_all_from_items()

    def add_item(self, name: str, *, checked: bool = True) -> None:
        """Append a single item to the list if it does not already exist.

        Args:
            name: Class name to show.
            checked: Initial checkbox state for the new row.

        Notes:
            This only updates the view; the controller is responsible for
            updating the model and persisting state.
        """
        # Avoid duplicate rows visually; controller/model should
        # also enforce uniqueness.
        if name in self.get_all_names():
            return

        self._add_list_item(name, checked=checked)
        self.sync_select_all_from_items()

    def remove_selected(self) -> None:
        """Remove the currently selected rows from the list widget.

        Notes:
            Selection is controlled by the user (Ctrl/Cmd-click,
            Shift-click). This only updates the view; the controller must
            update the underlying model and storage.
        """
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

        # Keep the Select-all checkbox consistent after removals.
        self.sync_select_all_from_items()


    def set_item_checked(self, name: str, checked: bool) -> None:
        """Set a row's checkbox state by its class name.

        Args:
            name: Class name to match (exact text match on the row).
            checked: True to check the row; False to uncheck it.
        """
        blocker = QtCore.QSignalBlocker(self.list_widget)
        try:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if self._base_name(item) == name:
                    item.setCheckState(
                        QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked
                    )
                    break
        finally:
            del blocker

        # Keep the select-all checkbox consistent with the current item states.
        self.sync_select_all_from_items()

    def get_selected_names(self) -> tuple[str, ...]:
        """Return class names for the currently selected rows."""
        return tuple(self._base_name(it) for it in self.list_widget.selectedItems())

    def get_all_names(self) -> tuple[str, ...]:
        """Return class names for all rows in the list, in row order."""
        return tuple(
            self._base_name(self.list_widget.item(i))
            for i in range(self.list_widget.count())
        )

    def get_enabled_names(self) -> tuple[str, ...]:
        """Return class names for rows whose checkboxes are checked."""
        out: list[str] = []
        for i in range(self.list_widget.count()):
            it = self.list_widget.item(i)
            if it.checkState() == QtCore.Qt.Checked:
                out.append(self._base_name(it))
        return tuple(out)

    def sync_select_all_from_items(self) -> None:
        """Synchronize the 'Select all' checkbox with row check states.

        Sets the tri-state checkbox to:

        - Unchecked: no rows are checked.
        - Checked: all rows are checked.
        - Partially checked: a mix of checked and unchecked rows.
        """
        total = self.list_widget.count()

        blocker = QtCore.QSignalBlocker(self.chk_select_all)
        try:
            # No rows → show unchecked (helps communicate there's
            # nothing to select).
            if total == 0:
                self.chk_select_all.setCheckState(QtCore.Qt.Unchecked)
                return

            checked = sum(
                1
                for i in range(total)
                if self.list_widget.item(i).checkState() == QtCore.Qt.Checked
            )

            if checked == 0:
                self.chk_select_all.setCheckState(QtCore.Qt.Unchecked)
            elif checked == total:
                self.chk_select_all.setCheckState(QtCore.Qt.Checked)
            else:
                self.chk_select_all.setCheckState(QtCore.Qt.PartiallyChecked)
        finally:
            del blocker

    # --------------------------------------------------------------------- #
    # UI construction (widgets + layout + light styling)                    #
    # --------------------------------------------------------------------- #

    def setup_ui(self) -> None:
        """Set basic window metadata such as title, object name, and flags."""
        self.setWindowTitle("Optimizer")
        self.setObjectName("OptimizerView")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def create_widgets(self) -> None:
        """Instantiate child widgets and configure their basic properties."""
        self.title_label = QtWidgets.QLabel(
            "Select node classes to exclude from optimization"
        )
        self.title_label.setToolTip(
            "List of node classes Optimizer will treat as heavy / excluded."
        )

        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setPlaceholderText("Filter classes…")
        self.filter_edit.setToolTip("Type to filter the class list by name.")

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.list_widget.setToolTip(
            "Checked classes will be used by the Optimizer actions " "in the Nuke menu."
        )
        self.list_widget.setItemDelegate(CountSuffixDelegate(self.list_widget))

        self.chk_select_all = QtWidgets.QCheckBox("Select all")
        self.chk_select_all.setTristate(True)
        self.chk_select_all.setToolTip(
            "Check, uncheck, or partially select all classes in the list."
        )

        self.btn_add = QtWidgets.QPushButton("Add")
        self.btn_add.setToolTip("Add one or more node classes to this list.")

        self.btn_remove = QtWidgets.QPushButton("Remove")
        self.btn_remove.setToolTip("Remove the selected classes from this list.")

        self.btn_export = QtWidgets.QPushButton("Export…")
        self.btn_export.setToolTip(
            "Export this class list as a preset file (JSON or CSV)."
        )

        self.btn_import = QtWidgets.QPushButton("Import…")
        self.btn_import.setToolTip("Import a class list preset from disk.")

        self.btn_defaults = QtWidgets.QPushButton("Defaults")
        self.btn_defaults.setToolTip(
            "Restore the factory default list of heavy node classes."
        )

        self.btn_toggle_heavy = QtWidgets.QPushButton("Toggle heavy nodes")
        self.btn_toggle_heavy.setToolTip("Toggle heavy nodes on or off in the current scene.")

        self.preset_button = QtWidgets.QToolButton()
        self.preset_button.setText("Presets")
        self.preset_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.preset_button.setToolTip(
            "Open preset actions: export/import list or reset to defaults."
        )

        menu = QtWidgets.QMenu(self)
        act_export = menu.addAction("Export…", self.btn_export.click)
        act_export.setToolTip(
            "Export the current class list and toggled set as a preset file."
        )
        act_import = menu.addAction("Import…", self.btn_import.click)
        act_import.setToolTip(
            "Import a saved preset file to replace the current class list."
        )

        menu.addSeparator()

        act_defaults = menu.addAction("Reset to defaults", self.btn_defaults.click)
        act_defaults.setToolTip("Restore the factory default list of heavy classes.")

        self.preset_button.setMenu(menu)

        self.help_button = QtWidgets.QToolButton()
        self.help_button.setText("Help")
        self.help_button.setToolTip(
            "Show a brief explanation of what Optimizer does and how to " "use it."
        )
        self.help_button.clicked.connect(self._show_inline_help)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setObjectName("status_label")
        self.status_label.setTextFormat(QtCore.Qt.PlainText)
        self.status_label.setAccessibleName("Status")
        self.status_label.setToolTip("Recent action status")

        self._status_timer = QtCore.QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self.status_label.setText(""))

    def create_layout(self) -> None:
        """Assemble child widgets into the final layout."""
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        header = QtWidgets.QHBoxLayout()
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.preset_button)
        header.addWidget(self.help_button)
        root.addLayout(header)

        root.addWidget(self.filter_edit)
        root.addWidget(self.list_widget)

        row_select_all = QtWidgets.QHBoxLayout()
        row_select_all.addWidget(self.chk_select_all)
        row_select_all.addStretch()
        root.addLayout(row_select_all)

        row_heavy = QtWidgets.QHBoxLayout()
        row_heavy.addStretch()
        row_heavy.addWidget(self.btn_toggle_heavy)
        root.addLayout(row_heavy)

        row_actions = QtWidgets.QHBoxLayout()
        row_actions.addWidget(self.btn_add)
        row_actions.addWidget(self.btn_remove)
        row_actions.addStretch()
        root.addLayout(row_actions)

        root.addWidget(self.status_label)

        self.setLayout(root)

    def set_style(self) -> None:
        """Apply minimal, safe styling such as window size and title emphasis.

        Notes:
            For full theming, prefer a dedicated .qss (stylesheet) in
            resources/.
        """
        # Reasonable default window size for a compact tool palette.
        self.resize(360, 420)

        # Slightly larger/bold title.
        font = self.title_label.font()
        font.setPointSize(8)
        font.setBold(True)
        self.title_label.setFont(font)

    # --------------------------------------------------------------------- #
    # Helpers (internal)                                                    #
    # --------------------------------------------------------------------- #


    def _show_inline_help(self) -> None:
        """Show a brief help dialog describing how to use the Optimizer panel."""
        QtWidgets.QMessageBox.information(
            self,
            "Optimizer Help",
            (
                "This tool lists heavy node classes in your Nuke script.\n\n"
                "- Checked classes are treated as heavy node classes; "
                "nodes of those classes are considered heavy nodes by "
                "the Optimizer.\n"
                "- Use the Optimizer menu actions (Disable heavy / "
                "Enable heavy) or the\n"
                "  'Toggle heavy nodes' button to disable or re-enable "
                "heavy nodes\n"
                "  in the current script.\n\n"
                "You can also export/import the class list as presets "
                "from the Presets menu."
            ),
        )


    def _format_label(
        self,
        base_name: str,
        total: int | None = None,
        disabled: int | None = None,
    ) -> str:
        """Return a label string combining the base name and counts.

        If total is provided, adds a simple ``"(total)"`` suffix. If both
        disabled and total are provided, adds a
        ``"(disabled/total disabled)"`` suffix.

        Args:
            base_name: Base class name to display.
            total: Total number of nodes of that class, if known.
            disabled: Number of disabled nodes of that class, if known.

        Returns:
            A formatted label string suitable for display in the list.
        """
        if total is None:
            return base_name
        if disabled is None:
            return f"{base_name}  ({total})"
        return f"{base_name}  ({disabled}/{total} disabled)"

    def _base_name(self, item: QtWidgets.QListWidgetItem) -> str:
        """Return the class name stored on a list item."""
        return item.data(QtCore.Qt.UserRole)

    def set_counts(self, stats: dict[str, dict[str, int]]) -> None:
        """Update per-class counts used for display on all rows.

        Args:
            stats: Mapping of the form::

                {
                    "ClassName": {
                        "total": <int>,
                        "disabled": <int>,
                    },
                    ...
                }

        Notes:
            These values are used only for display; they do not affect
            the model or Nuke state.
        """
        self._last_stats = dict(stats)  # cache latest

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            name = self._base_name(item)

            # Use defaults when missing.
            s = stats.get(name, {"total": 0, "disabled": 0})
            total = int(s.get("total", 0))
            disabled = int(s.get("disabled", 0))

            # Roles for the delegate.
            item.setData(QtCore.Qt.UserRole + 1, disabled)
            item.setData(QtCore.Qt.UserRole + 2, total)

            # Fallback/diagnostic text (delegate ignores it).
            item.setText(self._format_label(name, total, disabled))
            item.setToolTip(f"{name}: {total} nodes ({disabled} disabled)")

    def show_status(
        self,
        text: str,
        kind: str = "info",
        timeout_ms: int = 2500,
    ) -> None:
        """Show a brief, non-modal status message in the window.

        Args:
            text: Message to display.
            kind: One of ``"info"``, ``"success"``, ``"warn"``, or
                ``"error"``; only affects text color.
            timeout_ms: How long to show the message before clearing it,
                in milliseconds.
        """
        # Minimal styling without depending on an external .qss.
        palette = {
            "info": "color: #6b6b6b;",
            "success": "color: #2e7d32;",
            "warn": "color: #b26a00;",
            "error": "color: #b00020;",
        }.get(kind, "color: #6b6b6b;")

        self.status_label.setStyleSheet(palette)
        self.status_label.setText(text)
        self._status_timer.start(max(0, int(timeout_ms)))

    def apply_filter(self, text: str) -> None:
        """Show only rows whose base name contains the given text.

        Matching is case-insensitive; when the filter text is empty, all
        rows are shown.

        Args:
            text: Substring to match against each row's base name.
        """
        text = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            base = self._base_name(item).lower()
            item.setHidden(bool(text) and text not in base)

    def _add_list_item(self, name: str, *, checked: bool) -> None:
        """Create a single list row with a user-checkable checkbox.

        Args:
            name: Row label (class name).
            checked: Initial checkbox state for the row.
        """
        item = QtWidgets.QListWidgetItem(name)
        item.setData(QtCore.Qt.UserRole, name)

        # Make the item checkable and selectable for bulk remove operations.
        item.setFlags(
            item.flags()
            | QtCore.Qt.ItemIsUserCheckable
            | QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsEnabled
        )

        item.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
        self.list_widget.addItem(item)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle the window close event.

        Emits the ``closed`` signal so the controller can persist state,
        then forwards the event to the base implementation.

        Args:
            event: Close event from Qt.
        """
        super().closeEvent(event)
        self.closed.emit()
