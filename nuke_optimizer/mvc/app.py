"""Application bootstrap and logging configuration for the Optimizer.

Provides the show() entrypoint used by Nuke menu commands to create and
display the main Optimizer window. This module is responsible for:

- Configuring a rotating log file under the user's Nuke home directory.
- Ensuring logging is only configured once per session.
- Enforcing a single top-level Optimizer window per process.

All UI behavior is delegated to the MVC stack under the mvc package.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Minimal, reliable boot + single-instance behavior
VIEW = None  # type: ignore[assignment]
# ^ module-level handle to the currently constructed View (if any).
#   The controller and model are constructed on-demand in `show()` and are
#   intentionally not stored globally; only the View is cached for reuse.
LOG_DIR = Path.home() / ".nuke"
LOG_FILE = LOG_DIR / "optimizer.log"
LOG_LEVEL = logging.INFO


def _configure_logging() -> None:
    """Configure logging for the Optimizer package.

    Initialises a rotating file handler for the ``optimizer`` logger and
    writes log records to ``~/.nuke/optimizer.log`` (1 MB per file, up to
    5 backups). The handler is attached only once, so repeated calls do
    not add duplicate handlers.

    If the log directory or file cannot be created (for example, due to
    filesystem permissions), the error is logged as a warning on the root
    logger and file logging is skipped. This helper does not propagate
    ``OSError`` to callers.

    This configuration applies to all loggers under the ``optimizer``
    namespace and propagates messages to the root logger.
    """
    # Parent logger for your package
    package_logger = logging.getLogger("optimizer")
    package_logger.setLevel(LOG_LEVEL)

    # Avoid adding multiple handlers if this is called more than once
    already_configured = any(
        isinstance(h, RotatingFileHandler)
        and getattr(h, "baseFilename", None) == str(LOG_FILE)
        for h in package_logger.handlers
    )
    if already_configured:
        return

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8",
        )
    except OSError as exc:
        logging.getLogger(__name__).warning(
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

    package_logger.addHandler(handler)

    # Send messages to the root logger as well
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
    m = model.Model()

    # View: passive UI (widgets + layout)
    v = view.View()

    # Controller: wires view<->model and handles persistence/behavior
    controller.Controller(v, m)  # noqa: F841  (intentionally unused binding)

    # Cache the view for single-instance reuse and present it
    VIEW = v
    v.show()
    v.raise_()


def ensure_logging() -> None:
    """Ensure logging is configured for the Optimizer package.

    This is a convenience helper for external entry points (such as
    Nuke menu commands) that need logging without showing the UI.
    It delegates to `_configure_logging()` and is safe to call multiple
    times; it will not add duplicate handlers.
    """
    _configure_logging()
