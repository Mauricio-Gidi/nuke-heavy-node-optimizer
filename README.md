# Nuke Optimizer

Nuke Optimizer is a small PySide2 utility for managing “heavy” nodes in Nuke
(Denoise, ZDefocus, Deep nodes, etc.). It lets you define which node classes
are considered heavy, see how many of each exist in the current script, and
bulk enable/disable/toggle them while you work.

The tool is designed to be safe, defensive around Nuke API errors, and fully
per-user: each artist gets their own config and log file under their Nuke home
directory. :contentReference[oaicite:0]{index=0}

---

## Features

- Configurable list of “heavy” node classes, with sensible defaults.
- Displays a count of how many nodes of each class are present in the current
  script.
- Checkboxes to decide which classes are affected by bulk operations.
- Nuke menu commands under `Scripts ▸ Optimizer` to:
  - Open the Optimizer window.
  - Enable heavy nodes.
  - Disable heavy nodes.
  - Toggle heavy nodes.
- Per-user JSON configuration stored under the user’s Nuke home directory.
- Rotating log file (`optimizer.log`) in the same area for debugging.
- Import / export of presets (JSON or CSV) for the class list and toggled
  subset, so you can share settings between artists or shows.

---

## Repository layout

The core pieces you need to ship are:

```text
nuke_optimizer/               # Plugin folder (this is what you point Nuke at)
  menu.py                     # Registers "Scripts/Optimizer" menu entries
  mvc/
    __init__.py
    app.py                    # Application bootstrap & logging
    controller.py             # Wires view ↔ model, talks to nuke_services
    model.py                  # In-memory list of classes
    view.py                   # PySide2 UI
    dialogs.py                # QMessageBox helpers
  optimizer/
    __init__.py
    config.py                 # Global config constants (APP_DIR_NAME, etc.)
    defaults.py               # Built-in heavy node class list
    nuke_services.py          # All Nuke API calls & bulk ops
    storage.py                # JSON config load/save/validation
````

You do **not** need to distribute per-user data such as:

```text
nuke_optimizer_data/
  config.json
  optimizer.log
```

Those files will be created automatically for each artist when they use the
tool.

---

## Installation

You can install Nuke Optimizer either:

* per-user (by pointing Nuke at a folder in the user’s home), or
* in a shared studio location on the network.

Nuke discovers startup scripts by scanning all directories in its plug-in
path (`nuke.pluginPath()` / `NUKE_PATH`) and executing any `init.py` and
`menu.py` it finds. ([Foundry Support][1])

### 1. Put the plugin folder somewhere Nuke can see

Copy the entire `nuke_optimizer/` folder (shown above) to a location of your
choice, for example:

* Per-user: `~/.nuke/nuke_optimizer`
* Shared: `/studio/pipeline/nuke/nuke_optimizer`

The folder you point Nuke at must directly contain `menu.py` (Nuke does not
scan subdirectories for `menu.py`). ([Foundry Support][1])

### 2. Add that folder to the Nuke plug-in path

In your user `~/.nuke/init.py` (or a studio-wide init script), add:

```python
# ~/.nuke/init.py
import nuke

# Path to the folder that contains menu.py, mvc/, optimizer/
nuke.pluginAddPath("/studio/pipeline/nuke/nuke_optimizer")
```

Or, for a per-user install:

```python
nuke.pluginAddPath(os.path.expanduser("~/.nuke/nuke_optimizer"))
```

You can also achieve the same by adding that directory to the `NUKE_PATH`
environment variable, but `nuke.pluginAddPath()` is usually simpler for
per-user setup. ([Foundry Support][1])

### 3. Restart Nuke

When you launch Nuke in GUI mode, it will:

1. Scan all plug-in paths.
2. Execute any `init.py` files it finds.
3. Execute any `menu.py` files it finds.

At this point `nuke_optimizer/menu.py` runs and registers the
`Scripts ▸ Optimizer` menu and commands automatically, without any extra
code in your own `~/.nuke/menu.py`. ([Foundry Support][1])

### Optional: alternative package-style integration

If you prefer not to rely on `menu.py` being on the plug-in path, you can
also install `nuke_optimizer/` on `PYTHONPATH` and explicitly call its
registration entry point from your own `~/.nuke/menu.py`:

```python
# ~/.nuke/menu.py
import nuke_optimizer.menu
nuke_optimizer.menu.main()
```

In this mode, you are treating Nuke Optimizer purely as a Python package;
you are responsible for calling `main()` yourself.

---

## Usage

1. Launch Nuke.

2. In the main menu bar, go to:

   `Scripts ▸ Optimizer`

   and choose the command that opens the Optimizer window.

3. In the Optimizer window you can:

   * See the list of configured heavy node classes.
   * See how many nodes of each class are present in the current script.
   * Check/uncheck which classes should be affected by bulk operations.
   * Add or remove class names to tailor the list to your pipeline.

4. Use the other `Scripts ▸ Optimizer` commands to:

   * Disable heavy nodes.
   * Enable heavy nodes.
   * Toggle heavy nodes.

Only nodes whose `Class()` appears in the configured list **and** whose class
is currently checked are affected. Nodes must also expose a `disable` knob to
be modified.

---

## Configuration & data

Configuration and logs are stored under the user’s Nuke home directory
(typically the `.nuke` folder in the user’s home). ([Foundry Support][1])

* Config directory: `~/.nuke/<APP_DIR_NAME>_data/`

  * JSON file: `config.json`
  * Contains:

    * `classes`: ordered list of heavy node class names.
    * `toggled`: subset of `classes` that should be affected by bulk ops.
    * `version`: config schema version.
* Log file: `~/.nuke/optimizer.log`

  * Rotating log, suitable for troubleshooting (IO errors, Nuke API errors,
    preset load failures, etc.).

If `config.json` is missing or invalid, the storage layer will automatically
fall back to the factory defaults and write a fresh config to disk.

You should **not** commit or distribute any artist’s personal `config.json`
or `optimizer.log` files; they are intended to be local and per-user.

---

## Presets

The UI exposes preset import/export helpers:

* **Export preset**

  * Saves the current `classes` and `toggled` sets to a JSON or CSV file.
* **Import preset**

  * Loads a preset from JSON or CSV, replaces the current list, and persists
    it to `config.json`.

This makes it easy to distribute standard heavy-node lists per show or
department: maintain a set of preset files in source control, and have
artists import the matching preset.

---

## Dependencies

* Nuke (with its bundled Python and Nuke Python API).
* PySide2 (bundled with modern Nuke versions, no extra install needed). ([erwanleroy.com][2])

No third-party Python packages are required.

---

## License

This project is licensed under the MIT License.

Copyright (c) 2025 Mauricio Gidi

See the [LICENSE](LICENSE) file for the full license text.
