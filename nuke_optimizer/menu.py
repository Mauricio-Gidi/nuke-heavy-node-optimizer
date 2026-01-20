"""
Register Nuke menu entries for the Optimizer tool.

This module is intended to be executed inside a running Nuke session.
When loaded, it registers menu items under:

    Nuke > Scripts > Optimizer

It also provides safe wrappers so menu/hotkey actions:
- configure logging once,
- handle exceptions cleanly,
- provide user feedback (warning on no-op, short success message).
"""


def _ensure_menu(nuke):
    return nuke.menu("Nuke").addMenu("Scripts").addMenu("Optimizer")


def _format_result(res: dict) -> str:
    total = int(res.get("total", 0))
    changed = int(res.get("changed", 0))
    action = res.get("action", "noop")
    reason = res.get("reason", "")

    if total == 0:
        if reason == "no_active_classes":
            return "No active heavy classes. Open 'Optimizer editor' and check at least one class."
        return "No heavy nodes found for the active classes in the current script."

    verb = "Disabled" if action == "disabled" else "Enabled"
    return f"{verb} {changed} node{'s' if changed != 1 else ''} (out of {total})."


def _run_action(action: str) -> None:
    """
    action: one of 'toggle', 'enable', 'disable'
    """
    import nuke
    from mvc import app
    from optimizer import nuke_services

    app.ensure_logging()

    try:
        if action == "toggle":
            res = nuke_services.toggle_heavy_nodes()
        elif action == "enable":
            res = nuke_services.apply_heavy_nodes("enable")
        elif action == "disable":
            res = nuke_services.apply_heavy_nodes("disable")
        else:
            nuke.message(f"Optimizer: Unknown action '{action}'.")
            return

        msg = _format_result(res)

        # Non-modal feedback by default (less annoying for hotkey use).
        # Use nuke.message only for errors; warnings go to the script editor/status.
        if int(res.get("total", 0)) == 0:
            nuke.warning(f"Heavy Node Optimizer: {msg}")
        else:
            nuke.tprint(f"Heavy Node Optimizer: {msg}")

    except Exception as e:
        # Friendly user-facing error + point to logs.
        nuke.message(
            "Heavy Node Optimizer failed.\n\n"
            f"{e}\n\n"
            "Check optimizer.log for details."
        )


def _add_optimizer_entries(menu):
    # Avoid accidental duplicates if register() is called more than once.
    try:
        if menu.findItem("Toggle heavy nodes"):
            return
    except Exception:
        pass

    menu.addCommand(
        "Toggle heavy nodes",
        "import menu; menu._run_action('toggle')",
        shortcut="Ctrl+Alt+O",
        tooltip="Toggle disable on all heavy nodes selected in Optimizer.",
    )

    menu.addCommand(
        "Optimizer editor",
        "from mvc import app; app.show()",
        tooltip="Open the Optimizer window to manage heavy node classes.",
    )

    menu.addSeparator()

    menu.addCommand(
        "Disable Heavy Nodes",
        "import menu; menu._run_action('disable')",
        tooltip="Disable all heavy nodes currently marked as heavy.",
    )

    menu.addCommand(
        "Enable Heavy Nodes",
        "import menu; menu._run_action('enable')",
        tooltip="Enable all heavy nodes currently marked as heavy.",
    )


def register():
    import nuke
    menu = _ensure_menu(nuke)
    _add_optimizer_entries(menu)


# Auto-register when Nuke loads this file
try:
    import nuke  # noqa: F401
except Exception:
    # Outside Nuke: do nothing
    pass
else:
    register()
