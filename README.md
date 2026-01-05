
# nuke-heavy-node-optimizer

A configurable helper for Foundry Nuke that lets you quickly disable, enable, or toggle “heavy” nodes (retiming, defocus, deep, etc.) from the Nuke menu, plus a UI to manage which node classes are treated as heavy.

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

## Repository layout

This is what the repository looks like:

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
        optimizer/
            __init__.py
            config.py
            defaults.py
            nuke_services.py
            storage.py
````

The `nuke_optimizer` folder is the plugin package you will install into Nuke.

---

## Installation

1. **Locate your `.nuke` directory**

   On most systems this is:

   * Windows: `C:\Users\<you>\.nuke`
   * macOS: `/Users/<you>/.nuke`
   * Linux: `/home/<you>/.nuke`

2. **Copy the plugin folder**

   From this repository, copy the entire `nuke_optimizer` directory into your `.nuke` folder, so you end up with:

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
               model.py
               view.py
           optimizer/
               __init__.py
               config.py
               defaults.py
               nuke_services.py
               storage.py
   ```

3. **Register the plugin path in `init.py`**

   Edit (or create) `~/.nuke/init.py` and add the following line:

   ```python
   import nuke
   nuke.pluginAddPath("./nuke_optimizer")
   ```

4. **Start Nuke**

   Launch Nuke. If installed correctly, you should see a new menu entry:

   * `Nuke > Scripts > Optimizer`

   with several commands registered underneath. 

---

## What gets created at runtime

When you use the tool, it writes configuration and logs into your `.nuke` folder. The resulting structure will look like:

```text
.nuke/
    nuke_optimizer/
        __init__.py
        menu.py
        mvc/
            __init__.py
            app.py
            controller.py
            model.py
            view.py
        optimizer/
            __init__.py
            config.py
            defaults.py
            nuke_services.py
            storage.py

    nuke_optimizer_data/
        config.json        # your saved heavy-node config
    optimizer.log          # rotating log file created by the app
```

* `nuke_optimizer_data/config.json` holds:

  * `version`
  * `classes` (all known heavy classes)
  * `toggled` (which classes are currently active).  
* `optimizer.log` collects runtime information and warnings from the tool. 

---

## Usage

Once installed and Nuke is running:

1. Open **Scripts → Optimizer → Optimizer editor**
   This opens the main Optimizer window (a small PySide2-based panel).  

2. In the panel you can:

   * See a list of known heavy node classes.
   * Check/uncheck which classes should be treated as heavy in the current configuration.
   * Filter the list by typing in the filter box.
   * Add classes from the currently selected nodes in your script.
   * Remove selected classes.
   * Export/import presets.
   * Reset to factory defaults.   

3. To operate on the script:

   * Use **Scripts → Optimizer → Toggle heavy nodes** to toggle all active heavy nodes.
   * Use **Disable Heavy Nodes** or **Enable Heavy Nodes** for one-way operations.  

The tool computes statistics (total and disabled counts per class) and displays them in the list as you work.  

---

## Heavy node classes (defaults)

Out of the box, the tool ships with a curated list of render-intensive node classes, which you can then customize:

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

The UI allows you to add/remove classes and save them to your user config.

---

## Configuration and presets

* Persistent configuration is loaded and validated from `config.json`. If it is missing or invalid, the tool safely falls back to defaults and rewrites the file.  
* You can export/import presets as:

  * **JSON**: includes `version`, `classes`, and `toggled`.
  * **CSV**: with columns `class` and optional `toggled`. 

Presets make it easy to share heavy-node lists between artists or shows.

---

## Logging

The application writes to `~/.nuke/optimizer.log` using a rotating file handler (up to 1 MB per file, 5 backups). 

If something does not behave as expected, you can inspect this log or share it with whoever is maintaining the tool.

---

## Requirements

* Foundry Nuke with Python support.
* PySide2 available in the Nuke Python environment (used by the UI).   

---

## License

Copyright (c) 2025 Mauricio Gidi  

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file in this repository for the complete license text.
