# Nuke Heavy Node Optimizer (`nuke-heavy-node-optimizer`)

A small Nuke Python tool that helps you **bulk disable / enable / toggle “heavy” nodes** (nodes you choose by class) and keep that class list in a simple UI.

- **Menu actions** live under: `Nuke > Scripts > Optimizer`
- **Config UI**: “Optimizer editor” (MVC + Qt)
- **Persistence**: JSON config + optional JSON/CSV presets
- **Safety**: minimal edits to nodes—only touches the `disable` knob

---

## Compatibility (what we claim)

### Supported
- **Nuke 13+** (Python 3.7.7, Qt5/PySide2) through **Nuke 16+** (Python 3.11, Qt6/PySide6)

### Tested
- **Windows**: Nuke **15.x** and **16.x**  
  *(Other OSes should work; they’re just not the primary test target.)*

**Why this matters:** Nuke 16+ uses **PySide6** and will error on startup if plugins import **PySide2** directly. This repo uses a small shim (`mvc/qt_compat.py`) to run in both environments.

References:
- Nuke 13 → Python 3.7.7: https://campaigns.foundry.com/products/nuke-family/releases/13-0
- Nuke 16.0v1 → Python 3.11, Qt/PySide 6.5: https://learn.foundry.com/nuke/content/release_notes/16.0/nuke_16.0v1_releasenotes.html
- Foundry note about PySide2 breaking in Nuke 16+: https://support.foundry.com/hc/en-us/articles/25604028087570-Q100715-How-to-address-Python-PySide-issues-in-Nuke-16

---

## Repo-wide correctness guarantees (after applying the planned fixes)

1) **Global node discovery (correct scope)**
- Operations and statistics scan the **entire script**, including nodes **inside Groups (nested too)**, independent of current UI/context.
- Nuke’s `nuke.allNodes()` is context/group-scoped unless you provide a root group (or traverse from `nuke.root()`).
  - Docs: https://learn.foundry.com/nuke/developers/140/pythonreference/_autosummary/nuke.allNodes.html

2) **Qt compatibility**
- UI code runs in both:
  - **PySide2 / Qt5** (Nuke 13–15)
  - **PySide6 / Qt6** (Nuke 16+)

3) **No duplicates / data integrity**
- Config/presets are canonicalized so:
  - `classes` has **no duplicates** (order preserved; first occurrence wins)
  - `toggled` has **no duplicates** and is always a **subset** of `classes`

---

## What it does (behavior)

- Maintains a list of “heavy” **node classes** (e.g., `Kronos`, `VectorBlur2`).
- Maintains a **toggled subset** (checkboxes) of those classes.
- Finds all nodes whose `Class()` is in the toggled subset, **globally** across the script.
- Applies bulk operations by setting the node’s `disable` knob:
  - **Disable Heavy Nodes** → `disable = True`
  - **Enable Heavy Nodes** → `disable = False`
  - **Toggle heavy nodes** → disables all if any are enabled, otherwise enables all

> Note: Nodes without a `disable` knob are skipped.

---

## Installation (per-user `.nuke`)

1) Copy the **`nuke_optimizer/`** folder into your Nuke home, typically:
- Windows: `C:\Users\<you>\.nuke\`
- macOS: `/Users/<you>/.nuke/`
- Linux: `/home/<you>/.nuke/`

2) Add the plugin path in `~/.nuke/init.py` (create it if needed):

```python
import nuke
nuke.pluginAddPath("./nuke_optimizer")
```

3) Launch Nuke. You should see:
- `Nuke > Scripts > Optimizer`

---

## Usage

### 1) Configure heavy classes
Open:
- `Nuke > Scripts > Optimizer > Optimizer editor`

In the editor you can:
- Check/uncheck which classes are active (toggled subset)
- Filter by typing
- Add classes from selected nodes
- Remove selected classes
- Import/export presets
- Reset defaults

### 2) Apply actions
Use:
- `Nuke > Scripts > Optimizer > Toggle heavy nodes`
- `Nuke > Scripts > Optimizer > Disable Heavy Nodes`
- `Nuke > Scripts > Optimizer > Enable Heavy Nodes`

---

## Presets + config

### Presets
- **Export** / **Import** from the UI
- Supported formats:
  - JSON: `{"version": <int>, "classes": [...], "toggled": [...]}`
  - CSV: `class,toggled` where toggled is typically `1/0` or `true/false`

### Config file
- Stored under your `~/.nuke/` folder in a tool-specific subdirectory.
- See `nuke_optimizer/optimizer/storage.py` for the exact computed path on your system.

---

## Logging

- A rotating log is written to:
  - `~/.nuke/optimizer.log`

If something behaves unexpectedly, check that file first.

---

## Demo

*TODO (recommended for a “final” portfolio-grade README):*
- Add **1 screenshot** of the editor window
- Add a **10–20s GIF** showing:
  - open editor → toggle a couple of classes → run “Toggle heavy nodes” → observe result

---

## Folder layout

```text
nuke_optimizer/
  __init__.py
  menu.py
  mvc/
    app.py
    controller.py
    dialogs.py
    model.py
    view.py
    qt_compat.py
  optimizer/
    config.py
    defaults.py
    nuke_services.py
    storage.py
```

---

## Troubleshooting

### “ModuleNotFoundError: No module named 'PySide2'” in Nuke 16+
That typically means some plugin is importing PySide2 in a PySide6-only environment.
Foundry guidance: https://support.foundry.com/hc/en-us/articles/25604028087570-Q100715-How-to-address-Python-PySide-issues-in-Nuke-16

### “Tool does nothing”
Common causes:
- No classes are toggled in the editor
- There are no nodes of those classes in the script
- Target nodes lack a `disable` knob (they are skipped)

---

## License

MIT — see `LICENSE`.
