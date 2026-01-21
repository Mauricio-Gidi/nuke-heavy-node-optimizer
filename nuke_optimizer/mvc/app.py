"""Application entry points for the Optimizer UI.

This module provides two small utilities that are used by the Nuke menu:

* :func:`show` opens (or focuses) the Optimizer window.
* :func:`ensure_logging` enables file logging without opening the UI.

The UI is intentionally managed as a *single instance* per Nuke session.
This avoids duplicate panels and keeps the interaction simple.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


log = logging.getLogger(__name__)


# Single-instance window handle.
#
# The controller and model are created on-demand in :func:`show` and are
# intentionally not stored globally. Only the view is cached so we can reuse
# the same window and preserve its Qt state.
VIEW = None  # type: ignore[assignment]
LOG_DIR = Path.home() / ".nuke"
LOG_FILE = LOG_DIR / "optimizer.log"
LOG_LEVEL = logging.INFO


def _configure_logging() -> None:
    """Configure logging for the Optimizer.

    Writes log records to ~/.nuke/optimizer.log using a rotating file handler.
    The handler is attached to the *root logger* so logs from both `optimizer.*`
    and `mvc.*` are captured (with a namespace filter to keep the log focused).
    """

    root_logger = logging.getLogger()
    package_logger = logging.getLogger("optimizer")

    # Ensure our package logger emits INFO+ (even if root is more permissive)
    package_logger.setLevel(LOG_LEVEL)

    def _find_rotating_file_handler(logger_obj: logging.Logger) -> Optional[RotatingFileHandler]:
        """Return the Optimizer rotating file handler if it is already attached."""
        for handler in logger_obj.handlers:
            if isinstance(handler, RotatingFileHandler) and getattr(
                handler, "baseFilename", None
            ) == str(LOG_FILE):
                return handler
        return None

    # If root already has the handler, we're done.
    if _find_rotating_file_handler(root_logger) is not None:
        return

    # If an older session already attached it to the package logger, migrate it to root.
    handler = _find_rotating_file_handler(package_logger)
    if handler is not None:
        package_logger.removeHandler(handler)
    else:
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=1_000_000,
                backupCount=5,
                encoding="utf-8",
            )
        except OSError as exc:
            log.warning(
                "Unable to configure Optimizer file logging at %s: %s",
                LOG_FILE,
                exc,
            )
            return

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s:%(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.setLevel(LOG_LEVEL)

    # Keep the log focused on this tool (captures both optimizer.* and mvc.*)
    class _NamespaceFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            name = record.name or ""
            return name == "optimizer" or name.startswith("optimizer.") or name == "mvc" or name.startswith("mvc.")

    # Avoid stacking filters if handler was migrated/reused
    handler.filters = []
    handler.addFilter(_NamespaceFilter())

    root_logger.addHandler(handler)

    # Ensure INFO logs aren't dropped by a stricter root level.
    if root_logger.level > LOG_LEVEL:
        root_logger.setLevel(LOG_LEVEL)

    # Let optimizer.* bubble to root (default True, but keep it explicit)
    package_logger.propagate = True


def show() -> None:
    """Show (or raise) the Optimizer window.

    If a window already exists and is visible, it is raised and focused.
    Otherwise, this function constructs the MVC stack (Model, View,
    Controller), caches the view at module scope for reuse, and shows it.

    Raises:
        ImportError: If required UI or MVC modules (for example,
            ``mvc.view``, ``mvc.model``, ``mvc.controller`` or Qt bindings)
            cannot be imported.

    Notes:
        - This function does not perform Nuke or storage operations
          directly; the controller is responsible for persistence and
          engine/service calls.
        - Imports for Qt and MVC components are kept inside the function
          so this module can be imported safely in non-UI contexts.
    """
    _configure_logging()
    global VIEW

    # Reuse existing window if already open
    if VIEW is not None and VIEW.isVisible():
        VIEW.show()
        VIEW.raise_()
        VIEW.activateWindow()
        return

    # Build MVC (order matters)
    # Local imports keep this module importable without immediately pulling in UI deps.
    from mvc import view, model, controller  # type: ignore

    # Model: authoritative list state (no Qt deps)
    model_instance = model.Model()

    # View: passive UI (widgets + layout)
    view_instance = view.View()

    # Controller: wires view<->model and handles persistence/behavior
    controller.Controller(view_instance, model_instance)  # noqa: F841  (intentionally unused binding)

    # Cache the view for single-instance reuse and present it
    VIEW = view_instance
    view_instance.show()
    view_instance.raise_()


def ensure_logging() -> None:
    """Ensure logging is configured for the Optimizer package.

    This is a convenience helper for external entry points (such as
    Nuke menu commands) that need logging without showing the UI.
    It delegates to `_configure_logging()` and is safe to call multiple
    times; it will not add duplicate handlers.
    """
    _configure_logging()
