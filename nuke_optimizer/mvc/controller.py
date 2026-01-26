"""Controller layer for the Optimizer UI.

The controller coordinates three pieces:

* **View** (:mod:`mvc.view`) - the Qt widgets and small helpers for reading/writing UI state.
* **Model** (:mod:`mvc.model`) - the authoritative ordered set of class names.
* **Storage + Services** (:mod:`optimizer.storage`, :mod:`optimizer.nuke_services`) - persistence and Nuke actions.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Set, Tuple

# Qt binding compatibility (PySide2 / PySide6).
from mvc.qt_compat import QtWidgets, QtCore, CHECKED, PARTIALLY_CHECKED

from optimizer import storage, config, defaults
from optimizer.text_utils import unique_stripped_strings
from mvc.dialogs import DialogService


log = logging.getLogger(__name__)


def _make_config_mapping(classes: List[str], toggled: List[str]) -> dict:
    """Build a config dict ready to be saved/exported."""
    return {
        "version": config.CONFIG_VERSION,
        "classes": classes,
        "toggled": toggled,
    }


class Controller:
    """Application controller.

    Responsibilities:
        - Bootstrap the tool from storage (or defaults).
        - Wire View signals to controller handlers (no custom signals needed).
        - Update the Model and reflect changes in the View.
        - Persist structure (`classes`) and current UI toggles (`toggled`).

    The controller keeps the View's 'Select all' tri-state coherent and uses
    a `QSignalBlocker` during batch operations to avoid storms of itemChanged
    signals.
    """

    def __init__(self, view, model):
        """Initialize the controller and wire the view and model together.

        Sets up timers, loads persisted configuration, populates the view
        from the model, connects view signals to controller handlers, and
        ensures pending changes are flushed when the panel closes.

        Args:
            view: Passive View instance that owns the widgets and helper
                methods used by the controller.
            model: Model instance that owns the authoritative list of
                class names (order and membership).
        """
        self.view = view
        self.model = model
        self.dialogs = DialogService()

        self._refresh_timer = QtCore.QTimer(self.view)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._refresh_counts_now)

        self._save_timer = QtCore.QTimer(self.view)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._persist_state)
        self._save_delay_ms = 400

        # Initialize state from storage (or defaults) and paint the UI.
        self._bootstrap()

        # Wire raw widget signals from the passive view to controller handlers.
        self._connect_view_signals()

        # Ensure any pending changes are flushed when the panel closes.
        if hasattr(self.view, "closed"):
            self.view.closed.connect(self._persist_state)

        self._schedule_refresh()

    def _handle_ui_error(self, context: str, exc: Exception) -> None:
        """Log an unexpected UI error and show a user-facing dialog.

        Args:
            context: Short description of the operation that failed,
                used in both logs and the dialog text.
            exc: The exception instance that was raised.
        """
        log.exception("Unexpected error in UI context '%s': %s", context, exc)
        self.dialogs.error(
            self.view,
            "Unexpected error",
            (
                f"An unexpected error occurred while {context}.\n\n"
                f"Details: {exc}\n\n"
                "You can check optimizer.log for more information."
            ),
        )

    # -----------------------------------------------------------------------------
    # Timers / debounced operations
    # -----------------------------------------------------------------------------

    def _schedule_refresh(self, delay_ms: int = 150) -> None:
        """Schedule a debounced refresh of the heavy-node counts.

        Args:
            delay_ms: Delay in milliseconds before triggering the
                refresh. Multiple calls within this window coalesce into a single
                refresh to avoid redundant Nuke API calls.
        """
        # Coalesce multiple calls into one refresh.
        self._refresh_timer.start(delay_ms)

    def _schedule_persist_state(self, delay_ms: Optional[int] = None) -> None:
        """Schedule a debounced write of the current configuration.

        Args:
            delay_ms: Optional delay in milliseconds before writing the
                configuration. If ``None``, a default save delay is used.
                Multiple calls within this window are coalesced into a
                single disk write.
        """
        if delay_ms is None:
            delay_ms = self._save_delay_ms
        self._save_timer.start(delay_ms)

    def _refresh_counts_now(self) -> None:
        """Query Nuke for current per-class statistics and update the view.

        Calls `optimizer.nuke_services.class_stats()` with the model's class
        list and passes the resulting statistics to `view.set_counts()`.
        """
        from optimizer import nuke_services

        classes = self.model.as_list()
        stats = nuke_services.class_stats(classes)
        self.view.set_counts(stats)

    # -----------------------------------------------------------------------------
    # Boot / wiring
    # -----------------------------------------------------------------------------

    def _bootstrap(self) -> None:
        """Load persisted state, seed the model, and render the initial UI.

        Reads configuration using `optimizer.storage.safe_load_or_default()`,
        falling back to `optimizer.defaults.RENDER_INTENSIVE_NODES` when
        needed. Populates the model, rebuilds the list in the view, reapplies
        stored toggles, syncs the Select-all tri-state, and schedules an
        initial counts refresh.
        """
        data = storage.safe_load_or_default()
        classes = data.get("classes", list(defaults.RENDER_INTENSIVE_NODES))
        toggled_list = data.get("toggled", [])

        # Seed the authoritative list (order + membership).
        self.model.replace_all(classes)

        # Paint the list: start unchecked, then enable only persisted toggles.
        self.view.set_items(self.model.as_list(), checked=False)
        toggled_set = set(toggled_list)
        for name in self.model.as_list():
            if name in toggled_set:
                self.view.set_item_checked(name, True)

        # Keep tri-state (Unchecked/Partially/Checked) truthful.
        self.view.sync_select_all_from_items()
        self._schedule_refresh()

    def _connect_view_signals(self) -> None:
        """Connect passive view widget signals to controller handlers.

        Wires built-in Qt widget signals from the view (buttons, list,
        filter edit, and tri-state checkbox) to controller methods so
        user actions are reflected in the model, persisted, and applied
        to the Nuke scene when needed.
        """
        self.view.filter_edit.textChanged.connect(
            lambda text: self.view.apply_filter(text)
        )
        self.view.btn_toggle_heavy.clicked.connect(lambda: self._on_toggle_heavy())
        self.view.btn_add.clicked.connect(lambda: self._on_add_clicked())
        self.view.btn_remove.clicked.connect(lambda: self._on_remove_clicked())
        # export/import presets
        self.view.btn_export.clicked.connect(lambda: self._on_export_clicked())
        self.view.btn_import.clicked.connect(lambda: self._on_import_clicked())

        self.view.btn_defaults.clicked.connect(
            lambda: self._on_reset_defaults_clicked()
        )

        # Tri-state 'Select all' checkbox and per-item checkbox changes.
        self.view.chk_select_all.stateChanged.connect(
            lambda state: self._on_select_all_state_changed(state)
        )

        self.view.list_widget.itemChanged.connect(lambda item: self._on_item_changed(item))

        self.view.list_widget.model().rowsMoved.connect(lambda *args: self._on_list_reordered())

    # -----------------------------------------------------------------------------
    # Handlers: view -> controller
    # -----------------------------------------------------------------------------

    def _on_toggle_heavy(self) -> None:
        """Handle the 'Toggle heavy nodes' action.

        Uses `optimizer.nuke_services.toggle_heavy_nodes()` to apply the
        operation, shows a summarized result to the user in a dialog, and
        schedules a refresh of the heavy-node counts in the UI.
        """
        from optimizer import nuke_services

        toggle_result = nuke_services.toggle_heavy_nodes()

        # Better no-op messaging
        if toggle_result.get("action") == "noop" or toggle_result.get("total", 0) == 0:
            reason = toggle_result.get("reason")
            if reason == "no_active_classes":
                message = (
                    "No active classes selected.\n\n"
                    'Check at least one class in the list (or use "Select all"), then try again.'
                )
            elif reason == "no_matching_nodes":
                message = (
                    "No matching nodes found for the active classes.\n\n"
                    "Tip: the checked classes are enabled, but your script doesn't contain any nodes of those types."
                )
            else:
                # Fallback (in case reason is missing)
                message = "No heavy nodes found in the current scene."
        else:
            verb = "Disabled" if toggle_result["action"] == "disabled" else "Enabled"
            message = f"{verb} {toggle_result['changed']} node{'s' if toggle_result['changed'] != 1 else ''}."

        self.dialogs.info(self.view, "Optimizer", message)
        self._schedule_refresh()

    def _on_add_clicked(self) -> None:
        """Add classes from the selected Nuke nodes after confirmation.

        Uses optimizer.nuke_services.selected_class_names() to discover
        class names from the current selection, prompts the user for
        confirmation, adds any valid new classes to the model and view,
        persists the updated configuration, and shows a brief status
        message.
        """
        from optimizer import nuke_services

        classes = nuke_services.selected_class_names()
        if not classes:
            self.dialogs.warn(self.view, "No nodes selected", "Select one or more nodes.")
            return

        noun = f"class{'es' if len(classes) != 1 else ''}"
        names_text = ", ".join(classes)
        if not self.dialogs.ask_yes_no(
            self.view,
            "Confirm add",
            f"Add the following {noun} to the Optimizer list?\n\n{names_text}",
        ):
            return

        any_added = False
        added_count = 0

        for name in classes:
            added_successfully, error = self.model.add_class(name)
            if added_successfully:
                self.view.add_item(name, checked=True)
                any_added, added_count = True, added_count + 1
            else:
                title = {
                    "exists": "Duplicate class",
                    "empty": "No class name",
                    "type": "Invalid class",
                }.get(error, "Couldn't add class")
                self.dialogs.warn(self.view, title, f"Skipped '{name}': {error}")

        if any_added:
            if self._persist_state():
                self._schedule_refresh()
                self.view.show_status(
                    f"Added {added_count} class{'es' if added_count != 1 else ''}.",
                    kind="success",
                    timeout_ms=2500,
                )
        else:
            self.view.show_status("No classes added.", kind="info", timeout_ms=2000)

    def _on_remove_clicked(self) -> None:
        """Remove the selected classes after confirmation and persist.

        Collects the currently selected class names from the view,
        prompts the user for confirmation, removes them from the model,
        updates the view, persists the new configuration, and shows a
        brief status message describing the result.
        """
        names = self.view.get_selected_names()
        if not names:
            return
        count = len(names)
        if not self.dialogs.ask_yes_no(
            self.view,
            "Confirm remove",
            f"Remove {count} selected class{'es' if count != 1 else ''} from the Optimizer list?",
        ):
            return
        result = self.model.remove_classes(names)
        if not result.get("changed"):
            self.view.show_status("No classes removed.", kind="info", timeout_ms=2000)
            return
        removed = int(result.get("removed", 0))
        self.view.remove_selected()
        if self._persist_state():
            self._schedule_refresh()
            self.view.show_status(
                f"Removed {removed} {'class' if removed == 1 else 'classes'}.",
                kind="warn",
                timeout_ms=2500,
            )

    def _on_item_changed(self, item) -> None:
        """Update aggregate state and persistence when a row checkbox changes.

        Keeps the Select-all tri-state checkbox in sync with individual
        row check states, schedules a debounced configuration write, and
        schedules a counts refresh.

        Args:
            item: The `QtWidgets.QListWidgetItem` whose checkbox state has
                just changed.
        """
        try:
            # Update tri-state (Unchecked / PartiallyChecked / Checked).
            self.view.sync_select_all_from_items()

            self._schedule_persist_state()
            self._schedule_refresh()

        except Exception as exc:
            self._handle_ui_error("applying the checkbox change", exc)

    def _on_select_all_state_changed(self, state: int) -> None:
        """Apply the Select-all checkbox state to all rows and persist.

        The incoming state is interpreted as:

        - Checked -> check all items.
        - Unchecked -> uncheck all items.
        - Partially checked -> treated as 'check all' for mixed state.

        After applying the state, the method resynchronizes the tri-state
        checkbox, schedules a debounced configuration write, and
        schedules a counts refresh.

        Args:
            state: Integer check state value emitted by the tri-state
                Select-all checkbox.
        """
        try:
            # Convert the raw int state to the correct enum type for the active Qt binding.
            try:
                state_enum = QtCore.Qt.CheckState(state)
            except Exception:
                state_enum = state

            if state_enum == PARTIALLY_CHECKED:
                state_enum = CHECKED

            # Prevent storms of itemChanged signals during bulk updates.
            blocker = QtCore.QSignalBlocker(self.view.list_widget)
            try:
                for i in range(self.view.list_widget.count()):
                    item = self.view.list_widget.item(i)
                    if item is None:
                        continue
                    item.setCheckState(state_enum)
            finally:
                del blocker

            # Reflect aggregate state and persist new toggled subset.
            self.view.sync_select_all_from_items()
            self._schedule_persist_state()
            self._schedule_refresh()

        except Exception as exc:
            # Catch any Qt/logic errors so they don't escape the slot.
            self._handle_ui_error("updating the selection", exc)

    def _on_export_clicked(self) -> None:
        """Export the current list to a JSON/CSV preset file."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.view,
            "Export Optimizer preset",
            "",
            "JSON preset (*.json);;CSV preset (*.csv);;All files (*)",
        )
        if not path:
            return

        # Decide format by extension (default: JSON)
        lower = path.lower()
        fmt = "csv" if lower.endswith(".csv") else "json"

        classes = list(self.model.as_list())
        enabled_set = set(self.view.get_enabled_names())
        toggled_list = [name for name in classes if name in enabled_set]

        try:
            if fmt == "csv":
                import csv

                with open(path, "w", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerow(["class", "toggled"])
                    for name in classes:
                        writer.writerow([name, "1" if name in enabled_set else "0"])
            else:
                import json

                data = _make_config_mapping(classes, toggled_list)
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)
        except Exception as e:
            self.dialogs.error(self.view, "Export failed", f"Could not export preset:\n{e}")
            return

        self.view.show_status("Preset exported.", kind="success", timeout_ms=2500)

    def _on_import_clicked(self) -> None:
        """Import a JSON/CSV preset file and replace the current list."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.view,
            "Import Optimizer preset",
            "",
            "Preset files (*.json *.csv);;All files (*)",
        )
        if not path:
            return

        try:
            classes, toggled = self._load_preset_file(path)
        except Exception as e:
            self.dialogs.error(self.view, "Import failed", f"Could not import preset:\n{e}")
            return

        try:
            self.model.replace_all(classes)
            self.view.set_items(self.model.as_list(), checked=False)

            # Apply toggles in view order for deterministic behavior.
            for name in self.model.as_list():
                if name in toggled:
                    self.view.set_item_checked(name, True)

            self.view.sync_select_all_from_items()

            if self._persist_state():
                total = len(self.model.as_list())
                self.view.show_status(
                    f"Imported preset ({total} classes).",
                    kind="success",
                    timeout_ms=3000,
                )
                self._schedule_refresh()

        except Exception as exc:
            self._handle_ui_error("applying the imported preset", exc)

    def _load_preset_file(self, path: str) -> Tuple[List[str], Set[str]]:
        """Load a preset file (JSON/CSV) and return (classes, toggled)."""
        lower = path.lower()

        if lower.endswith(".csv"):
            import csv

            with open(path, "r", newline="", encoding="utf-8") as fh:
                rows = list(csv.reader(fh))

            if not rows:
                raise ValueError("CSV file is empty.")

            header = [h.strip().lower() for h in rows[0]]
            classes: List[str] = []
            toggled: Set[str] = set()

            if "class" in header:
                idx_class = header.index("class")
                idx_toggle = header.index("toggled") if "toggled" in header else None

                for row in rows[1:]:
                    if idx_class >= len(row):
                        continue
                    name = row[idx_class].strip()
                    if not name:
                        continue
                    classes.append(name)

                    if idx_toggle is not None and idx_toggle < len(row):
                        flag = row[idx_toggle].strip().lower()
                        if flag in ("1", "true", "yes", "y"):
                            toggled.add(name)
            else:
                # Fallback: first column of each row
                for row in rows:
                    if not row:
                        continue
                    name = row[0].strip()
                    if name:
                        classes.append(name)

            classes = unique_stripped_strings(classes)
            toggled &= set(classes)
            return classes, toggled

        else:
            import json

            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            if isinstance(data, dict):
                raw_classes = data.get("classes", [])
                raw_toggled = data.get("toggled", [])
            elif isinstance(data, list):
                raw_classes = data
                raw_toggled = []
            else:
                raise ValueError("JSON preset must be a list or an object with a 'classes' key.")

            if not isinstance(raw_classes, list) or not all(isinstance(x, str) for x in raw_classes):
                raise ValueError("'classes' must be a list of strings.")

            classes = unique_stripped_strings(raw_classes)
            toggled = {x.strip() for x in raw_toggled if isinstance(x, str) and x.strip()}

            # Ensure toggled is a subset of classes
            toggled &= set(classes)
            return classes, toggled

    # -----------------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------------

    def _persist_state(self) -> bool:
        """Save the current classes + toggled list to disk."""
        # Cancel any pending debounced save; this call will perform the write now.
        self._save_timer.stop()

        try:
            classes = list(self.model.as_list())
            allowed = set(classes)
            enabled = unique_stripped_strings(self.view.get_enabled_names())
            toggled = [name for name in enabled if name in allowed]

            storage.save(_make_config_mapping(classes, toggled))
            return True
        except OSError as e:
            self.dialogs.error(self.view, "Save Error", f"Could not write config:\n{e}")
            return False

    def _on_reset_defaults_clicked(self) -> None:
        """Reset the list to factory defaults, enable all items, and save."""
        if not self.dialogs.ask_yes_no(
            self.view,
            "Reset to Defaults",
            (
                "Reset the list to factory defaults? "
                "This will replace your current list and enable all classes."
            ),
        ):
            return

        try:
            self.model.replace_all(defaults.RENDER_INTENSIVE_NODES)
            self.view.set_items(self.model.as_list(), checked=True)
            if self._persist_state():
                total = len(self.model.as_list())
                self.view.show_status(
                    f"Defaults restored ({total} classes).",
                    kind="success",
                    timeout_ms=3000,
                )
                self._schedule_refresh()
        except Exception as exc:
            self._handle_ui_error("resetting the list to defaults", exc)

    def _on_list_reordered(self) -> None:
        """Sync model and storage after the user reorders items.

        Called when the user reorders rows via drag-and-drop. Copies the
        current visual order from the view into the model, persists the
        new configuration, and schedules a debounced counts refresh.
        """
        try:
            # View is authoritative for visual order; model mirrors it.
            self.model.replace_all(self.view.get_all_names())
            if self._persist_state():
                self._schedule_refresh()

        except Exception as exc:
            self._handle_ui_error("reordering the class list", exc)
