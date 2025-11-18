````markdown
# Nuke Optimizer

A small Nuke helper to quickly disable/enable “heavy” nodes (Kronos, OFlow2, Denoise2, etc.) across the current script, plus a UI to manage which node classes are considered heavy.

The tool integrates into Nuke’s **Scripts → Optimizer** menu and stores its configuration under your `~/.nuke` directory. 

---

## Features

- **One-click bulk toggle of heavy nodes**
  - Toggle, disable, or enable all configured heavy nodes via Nuke menu commands. 
- **Configurable heavy-node class list**
  - Ships with a sensible default list (Kronos, OFlow2, MotionBlur, ZDefocus2, Denoise2, DeepRecolor, etc.).
  - Add/remove classes based on your current pipeline. 
- **Per-class statistics**
  - UI shows, for each class, how many nodes exist and how many are currently disabled. 
- **Preset import/export**
  - Save or load class lists and their toggled state as JSON or CSV presets. :contentReference[oaicite:4]{index=4}
- **Persistent configuration and logging**
  - Config JSON and log file under your `~/.nuke` directory, versioned and validated. 
- **Defensive, Nuke-safe behavior**
  - Fails gracefully when Nuke API is unavailable or nodes are missing `disable` knobs; logs details instead of raising. 

---

## Repository layout

```text
nuke_optimizer_data/        # Runtime data written under ~/.nuke/
  config.json               # Persistent user configuration (JSON)
  optimizer.log             # Rotating log file

nuke_optimizer/             # Main package (put this on Nuke's PYTHONPATH)
  __init__.py
  menu.py                   # Nuke menu integration entrypoint

  mvc/                      # MVC UI stack (PySide2)
    __init__.py
    app.py                  # App bootstrap + logging + show()
    controller.py           # Wires view/model, storage, and nuke_services
    model.py                # In-memory list of node classes
    view.py                 # Qt widgets, list, controls, and counts

  optimizer/
    __init__.py
    config.py               # Global config constants and file naming
    defaults.py             # Built-in heavy node class list
    nuke_services.py        # Nuke API helpers (class stats, toggling)
    storage.py              # Config load/save/validate helpers
````

---

## Installation

1. **Copy the package into your Nuke home**

   Place the `nuke_optimizer` directory somewhere on Nuke’s Python path, typically:

   * Linux/macOS: `~/.nuke/nuke_optimizer`
   * Windows: `%USERPROFILE%\.nuke\nuke_optimizer`

   The tool expects to write:

   * A config file under `~/.nuke/nuke_optimizer_data/config.json`.
   * A log file at `~/.nuke/optimizer.log`.

2. **Register the menu in your `~/.nuke/menu.py`**

   In your user `menu.py` (in `~/.nuke`), add:

   ```python
   import nuke_optimizer.menu
   nuke_optimizer.menu.main()
   ```

   This creates/refreshes a **Scripts → Optimizer** submenu and adds Optimizer commands under it. 

3. **Restart Nuke**

   On the next launch, you should see:

   * `Scripts → Optimizer → Toggle heavy nodes`
   * `Scripts → Optimizer → Optimizer editor`
   * `Scripts → Optimizer → Disable Heavy Nodes`
   * `Scripts → Optimizer → Enable Heavy Nodes` 

---

## Usage

### Menu commands

Once installed, use the following actions from the **Scripts → Optimizer** submenu:

* **Toggle heavy nodes** (`Ctrl+Alt+O` by default)

  * If any heavy node is currently enabled, all heavy nodes are disabled.
  * Otherwise, all heavy nodes are enabled.
* **Disable Heavy Nodes**

  * Forces all configured heavy nodes to `disable=True`.
* **Enable Heavy Nodes**

  * Forces all configured heavy nodes to `disable=False`.
* **Optimizer editor**

  * Opens the Optimizer configuration window (MVC UI).

All three operations act only on nodes whose classes are in the configured list and currently marked as “toggled” in the UI. Nodes are changed by flipping their `disable` knob.

### Optimizer window (UI)

Open via **Scripts → Optimizer → Optimizer editor**. This constructs the MVC stack (`Model`, `View`, `Controller`) and ensures logging is configured.

The window provides:

* **Class list**

  * Each row is a node class name.
  * Checkbox indicates whether that class is active as a heavy class.
  * Right-aligned suffix shows `(disabled/total disabled)` stats for that class in the current script.

* **Filter field**

  * Text filter over the class list. 

* **Select all (tri-state)**

  * Unchecked: no classes active.
  * Checked: all classes active.
  * Partially checked: mix of checked/unchecked; clicking will check all.

* **Buttons**

  * **Toggle heavy nodes**
    Runs the same bulk toggle as the Nuke menu action.
  * **Add**
    Uses the current Nuke node selection to discover class names and add them to the list (with confirmation).
  * **Remove**
    Removes selected classes from the list (with confirmation).
  * **Presets → Export… / Import… / Reset to defaults**

    * Export/import JSON or CSV presets with `classes` and `toggled` fields.
    * Reset to the built-in defaults from `optimizer.defaults.RENDER_INTENSIVE_NODES`.
  * **Help**
    Shows a short help dialog describing Optimizer and its usage.

* **Status line**

  * Non-modal text for quick feedback, such as “Preset exported.” or “Added 3 classes.”

The controller debounces both Nuke API calls (for per-class stats) and config saves, so the UI remains responsive even with many classes.

---

## Configuration and persistence

* **Config file**

  * Stored as JSON under `~/.nuke/nuke_optimizer_data/config.json`.
  * Keys:

    * `version`: integer schema version (compared against `CONFIG_VERSION`).
    * `classes`: list of all known heavy classes in UI order.
    * `toggled`: subset of `classes` that are currently enabled in the UI.

* **Defaults and migration**

  * `CONFIG_VERSION`, `APP_DIR_NAME`, and `FILE_NAME` are defined in `optimizer.config`. 
  * On load:

    * `safe_load_or_default()` reads the existing file.
    * If the file is missing, invalid, or has an outdated schema, it logs a warning and rebuilds a fresh config from `RENDER_INTENSIVE_NODES`.

* **Validation**

  * `storage.validate()` ensures the config is a dict with a non-outdated `version`, a list of string `classes`, and optional list-of-string `toggled`.

---

## Logging

The UI bootstrap configures a rotating file handler for the `optimizer` logger:

* Log path: `~/.nuke/optimizer.log`
* Max size: 1 MB per file, up to 5 backups.
* Format: timestamp, level, logger name, message. 

Nuke-facing services and persistence helpers log warnings/info when something goes wrong (e.g., invalid config, missing `disable` knob, failed Nuke queries). This makes it easier to debug broken scenes or configuration issues.

---

## Development notes

* **MVC separation**

  * `Model`: in-memory, ordered set of class names, with simple add/remove/replace operations and no Qt/Nuke knowledge. 
  * `View`: passive PySide2 widgets, layouts, and helpers; exposes a small API driven entirely by the controller. 
  * `Controller`: owns the model and `DialogService`, subscribes to view signals, persists config via `storage`, and invokes `nuke_services` for Nuke operations.

* **Nuke API integration**

  * All direct Nuke calls live in `optimizer.nuke_services`:

    * `class_stats(classes)` for per-class disabled/total counts.
    * `apply_heavy_nodes()` and wrappers (`heavy_nodes`, `toggle_heavy_nodes`) for bulk node operations.
    * `selected_class_names()` for deriving classes from the current node selection. 

* **Safety**

  * The code uses defensive error handling around Nuke and file I/O so that the UI continues to work even when scripts or environments are imperfect.

---

## License

Add your project’s license information here.

```
::contentReference[oaicite:35]{index=35}
```
