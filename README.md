````markdown
# nuke-heavy-node-optimizer

A configurable helper for Foundry Nuke that lets you quickly **disable / enable / toggle “heavy” nodes** from the Nuke menu, plus a small UI to manage which node classes are treated as “heavy”.

**Repo-wide correctness guarantees (after applying the planned fixes):**
- **Global node discovery:** operations and stats scan the *entire script*, including nodes inside **Groups (nested too)**, independent of current UI context. (Uses `nuke.allNodes(..., recurseGroups=True)` semantics; see API docs.)  
  Reference: https://learn.foundry.com/nuke/developers/140/pythonreference/_autosummary/nuke.allNodes.html
- **Qt compatibility:** works in **Nuke 13.x (PySide2/Qt5)** and **Nuke 16+ (PySide6/Qt6)** via a small shim (`mvc/qt_compat.py`).  
  References:  
  - https://support.foundry.com/hc/en-us/articles/25604028087570-Q100715-How-to-address-Python-PySide-issues-in-Nuke-16  
  - https://learn.foundry.com/nuke/content/release_notes/16.0/nuke_16.0v1_releasenotes.html  
  - https://doc.qt.io/qtforpython-6/faq/porting_from2.html
- **No duplicates / data integrity:** config and presets are canonicalized so:
  - `classes` has no duplicates (order preserved; first occurrence wins)
  - `toggled` has no duplicates and is always a subset of `classes`

---

## Features

- Adds an **Optimizer** submenu under **Scripts** in Nuke’s main menu.
- One-click actions:
  - **Toggle heavy nodes** – bulk toggle all configured heavy nodes.
  - **Disable Heavy Nodes** – force-disable all heavy nodes.
  - **Enable Heavy Nodes** – force-enable all heavy nodes.
- Configurable list of heavy node classes via a dedicated **Optimizer editor** UI.
- Per-class statistics in the UI:
  - Total nodes of each class.
  - How many are currently disabled.
- Preset import/export (JSON or CSV) for sharing heavy-node setups across shows or teams.
- Safe JSON-backed configuration stored in your `~/.nuke` directory, versioned and validated.
- Rotating log file for debugging (`optimizer.log`).

---

## Compatibility

| Nuke version | Python | Qt binding | Status |
|---|---:|---|---|
| Nuke **13.x** | 3.7.7 | PySide2 / Qt5 | Supported |
| Nuke **16+** | 3.11 | PySide6 / Qt6 | Supported |

References:
- Nuke 13 Python 3.7.7: https://campaigns.foundry.com/products/nuke-family/releases/13-0  
- Nuke 16 Qt/PySide 6.5 + Python 3.11: https://learn.foundry.com/nuke/content/release_notes/16.0/nuke_16.0v1_releasenotes.html

---

## Repository layout

```text
nuke-heavy-node-optimizer/
    README.md
    nuke_optimizer/
        __init__.py
        menu.py
        mvc/
            __init__.py
            app.py
            controller.py
            dialogs.py
            model.py
            view.py
            qt_compat.py
        optimizer/
            __init__.py
            config.py
            defaults.py
            nuke_services.py
            storage.py
````

The `nuke_optimizer` folder is the plugin package you install into Nuke.

---

## Installation

1. **Locate your `.nuke` directory**

   On most systems this is:

   * Windows: `C:\Users\<you>\.nuke`
   * macOS: `/Users/<you>/.nuke`
   * Linux: `/home/<you>/.nuke`

2. **Copy the plugin folder**

   Copy the entire `nuke_optimizer` directory into your `.nuke` folder, so you end up with:

   ```text
   ~/.nuke/
       init.py       # may already exist
       nuke_optimizer/
           __init__.py
           menu.py
           mvc/
               __init__.py
               app.py
               controller.py
               dialogs.py
               model.py
               view.py
               qt_compat.py
           optimizer/
               __init__.py
               config.py
               defaults.py
               nuke_services.py
               storage.py
   ```

3. **Register the plugin path in `init.py`**

   Edit (or create) `~/.nuke/init.py` and add:

   ```python
   import nuke
   nuke.pluginAddPath("./nuke_optimizer")
   ```

4. **Start Nuke**

   Launch Nuke. If installed correctly, you should see:

   * `Nuke > Scripts > Optimizer`

---

## What gets created at runtime

When you use the tool, it writes configuration and logs into your `.nuke` folder.

* **Config file (JSON):** stored under a tool-specific directory inside `~/.nuke/`.

  * The directory and filename are defined in `nuke_optimizer/optimizer/config.py`.
  * The `storage` module computes the full path at runtime.
* **Log file:** `~/.nuke/optimizer.log` (rotating: up to 1 MB per file, 5 backups).

The config contains:

* `version`
* `classes` (all known heavy classes)
* `toggled` (which classes are currently active)

---

## Usage

1. Open **Scripts → Optimizer → Optimizer editor**
   This opens the Optimizer window (Qt/PySide panel; binding depends on your Nuke version).

2. In the panel you can:

   * See a list of known heavy node classes.
   * Check/uncheck which classes are treated as heavy in the current configuration.
   * Filter the list by typing in the filter box.
   * Add classes from the currently selected nodes in your script.
   * Remove selected classes.
   * Export/import presets.
   * Reset to factory defaults.

3. To operate on the script:

   * Use **Scripts → Optimizer → Toggle heavy nodes** to toggle all active heavy nodes.
   * Use **Disable Heavy Nodes** or **Enable Heavy Nodes** for one-way operations.

**Important behavior:** node discovery is **global** and includes nodes inside **Groups (recursively)**; operations do not depend on your current group/context.

---

## Heavy node classes (defaults)

Out of the box, the tool ships with a curated list of render-intensive node classes, which you can customize:

* Retiming:

  * `Kronos`
  * `OFlow2`
  * `TimeBlur`
* Motion blur:

  * `MotionBlur`
  * `MotionBlur3D`
  * `VectorBlur2`
* Defocus / bokeh:

  * `Defocus`
  * `ZDefocus2`
  * `Convolve2`
* Denoise:

  * `Denoise2`
* Deep:

  * `DeepRecolor`

---

## Configuration and presets

* Persistent configuration is loaded and validated from `config.json`.
* If it is missing or invalid, the tool safely falls back to defaults and rewrites the file.
* Duplicates are removed and `toggled` is kept as a subset of `classes` during load/save and preset import.

Preset formats:

* **JSON**: includes `version`, `classes`, and `toggled`.
* **CSV**: columns `class` and optional `toggled` (`1/0`, `true/false`, `yes/no`).

---

## Troubleshooting

* **Nuke 16+ import error for PySide2:** if you have older custom scripts importing `PySide2`, Nuke 16+ can fail with `ModuleNotFoundError: No module named 'PySide2'`. Foundry guidance:
  [https://support.foundry.com/hc/en-us/articles/25604028087570-Q100715-How-to-address-Python-PySide-issues-in-Nuke-16](https://support.foundry.com/hc/en-us/articles/25604028087570-Q100715-How-to-address-Python-PySide-issues-in-Nuke-16)
* Check the log at `~/.nuke/optimizer.log` for warnings and errors.

---

## License

Copyright (c) 2025 Mauricio Gidi

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file in this repository for the complete license text.
