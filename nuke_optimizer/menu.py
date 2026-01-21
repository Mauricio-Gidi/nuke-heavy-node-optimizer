"""Nuke menu integration for the Optimizer tool."""

def _ensure_menu(nuke):
    """Return the Optimizer submenu attached to Nuke's Scripts menu.

    Ensures that the 'Scripts/Optimizer' submenu exists and returns it so
    Optimizer-related commands can be registered under it.

    Args:
        nuke: Nuke module used to access and manipulate menus.

    Returns:
        The Optimizer submenu under the Scripts menu.
    """
    return nuke.menu("Nuke").addMenu("Scripts").addMenu("Optimizer")


def _add_optimizer_entries(menu):
    """Register Optimizer commands under the given Nuke menu.

    Adds menu entries to launch the Optimizer UI and to enable, disable,
    or toggle heavy nodes using the user's saved configuration.

    Args:
        menu: Nuke menu object under which Optimizer commands are added.
    """
    menu.addCommand(
        "Toggle heavy nodes",
        "from mvc import app; from optimizer import nuke_services; "
        "app.ensure_logging(); nuke_services.toggle_heavy_nodes()",
        shortcut="Ctrl+Alt+O",
        tooltip="Toggle disable on all heavy nodes selected in Optimizer.",
    )

    menu.addCommand(
        "Optimizer editor",
        "from mvc import app; app.show()",
        tooltip=(
            "Open the Optimizer window to choose which node classes are "
            "treated as heavy node classes."
        ),
    )

    # Visual separator between the main toggle/editor entries and the
    # explicit enable/disable actions.
    menu.addSeparator()

    menu.addCommand(
        "Disable Heavy Nodes",
        "from mvc import app; from optimizer import nuke_services; "
        "app.ensure_logging(); nuke_services.heavy_nodes(toggle=False)",
        tooltip="Disable all heavy nodes currently marked as heavy.",
    )

    menu.addCommand(
        "Enable Heavy Nodes",
        "from mvc import app; from optimizer import nuke_services; "
        "app.ensure_logging(); nuke_services.heavy_nodes(toggle=True)",
        tooltip="Enable all heavy nodes currently marked as heavy.",
    )


def main():
    """Create or refresh the Optimizer entries in the Nuke menu.

    Ensures that the Scripts menu exists and (re)adds the Optimizer
    commands under the Optimizer submenu. Safe to call multiple times
    in a session.
    """
    import nuke

    menu = _ensure_menu(nuke)
    _add_optimizer_entries(menu)


if __name__ == "__main__":
    main()
