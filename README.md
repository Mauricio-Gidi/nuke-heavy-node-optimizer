# Nuke Heavy Node Optimizer (`nuke-heavy-node-optimizer`)

Bulk **disable / enable / toggle** “heavy” nodes (by node **Class**) across the whole script, with a small editor UI to manage the class list.

- Menu: `Nuke > Scripts > Optimizer`
- Hotkey: **Ctrl+Alt+O**
- Safety: only touches the node’s `disable` knob

**Highlights**
- One hotkey toggles **N heavy nodes** (N→1 action)
- Tested on **Windows** (Nuke 13.x, 15.2v6, 16.x)
- Only modifies the `disable` knob (low-risk change)

## Demo

<!-- Uncomment once the file exists:
![Toggle heavy nodes demo](media/demo_toggle.gif)
-->

**Planned 10–20s GIF (procedural / no external footage):**
1. Show Node Graph + Viewer with the “heavy nodes” chain **enabled**.
2. Briefly show: `Nuke > Scripts > Optimizer`.
3. Trigger **Toggle heavy nodes** (Ctrl+Alt+O) → heavy nodes go **disabled** (visible in graph) and Viewer output changes.
4. Optional: toggle again for a quick **A/B/A** loop.
5. Optional (1–2s): open **Optimizer editor** to show the class list is configurable.

Planned screenshots:
- `media/screenshot_menu.png` (Scripts > Optimizer menu)
- `media/screenshot_editor.png` (Optimizer editor)

## Quick start

1) Copy `nuke_optimizer/` into your `.nuke` directory (see Installation).
2) Add `nuke.pluginAddPath("./nuke_optimizer")` in `~/.nuke/init.py`.
3) Restart Nuke (GUI) → `Nuke > Scripts > Optimizer > Toggle heavy nodes`.

## Problem

Heavy nodes (retime/denoise/defocus/mblur/etc.) can make scripts sluggish for viewer playback and test renders. Manually hunting and disabling nodes is repetitive and increases the chance of forgetting to re-enable before final output.

## Solution

Provides one menu/hotkey action to toggle a configurable list of node classes by setting only the node `disable` knob, plus a small editor UI to manage that list.

## Measurable impact

**Measurable:** preview switching becomes **N manual edits → 1 action** (N = number of heavy nodes in the script).  
**Demo target:** the procedural demo script will include ~10–30 “heavy” nodes to show the reduction clearly.

## Requirements / Compatibility

### Tested (verified)
- **Windows**: Nuke **13.x**, **15.2v6**, **16.x**

### Supported (claimed)
- **Nuke 13+ → Nuke 16+**
- Nuke 16+ uses **PySide6 / Qt 6.5** (and Python 3.11). This repo includes a small Qt compatibility shim (`mvc/qt_compat.py`) to run on both:
  - **PySide2 / Qt5** (Nuke 13–15)
  - **PySide6 / Qt6** (Nuke 16+)

### Not tested
- **macOS / Linux** (expected to work, but not currently in the test matrix)

## Installation (per-user `.nuke`)

1) Copy `nuke_optimizer/` into your `.nuke` directory:
- Windows: `C:\Users\<you>\.nuke\`
- macOS: `/Users/<you>/.nuke/`
- Linux: `/home/<you>/.nuke/`

2) Add this to `~/.nuke/init.py` (create if needed):

```python
import nuke
nuke.pluginAddPath("./nuke_optimizer")
```

2.5) Verify Nuke can see the plugin path (optional but recommended)

In Nuke’s Script Editor:

```python
import nuke
print(nuke.pluginPath())
```

3) Restart Nuke (GUI) → open:
- `Nuke > Scripts > Optimizer > Toggle heavy nodes`

**Why `init.py` vs `menu.py` (startup behavior):**
- `init.py` runs for **all** Nuke sessions (including terminal/renders), so it’s the right place to add plugin paths.
- `menu.py` runs only for **GUI** sessions; this repo’s menu items/hotkey live in `nuke_optimizer/menu.py`, so they appear only when you launch Nuke with a UI.
- Note: in terminal/render-only sessions, `menu.py` won’t run, so menu items/hotkeys won’t appear (this is expected).

## Usage

### Behavior definitions
- **Heavy class**: a node class name listed in the Optimizer editor (e.g., `ZDefocus2`, `TimeBlur`).
- **Active class**: a heavy class that is currently checked/enabled in the editor (the tool only operates on these).
- **Target nodes**: all nodes in the current script whose `Class()` is an active class **and** that expose a `disable` knob.
- **Enabled vs disabled**: `disable = False` means the node is enabled; `disable = True` means the node is disabled.

### Configure heavy classes
Open:
- `Nuke > Scripts > Optimizer > Optimizer editor`

In the editor you can:
- Check/uncheck which classes are active
- Filter classes
- Add classes from selected nodes
- Remove classes
- Import/export presets
- Reset defaults

### Apply actions
- `Nuke > Scripts > Optimizer > Toggle heavy nodes` (**Ctrl+Alt+O**)  
  If **any target node** is enabled (`disable=False`) → sets `disable=True` on all target nodes; otherwise sets `disable=False` on all target nodes.
- `Disable Heavy Nodes` → sets `disable = True` on all target nodes
- `Enable Heavy Nodes` → sets `disable = False` on all target nodes

> Nodes without a `disable` knob are skipped.

## Configuration (file + schema)

### Config file location
The tool stores its config under your **user `.nuke`** directory:

- Windows: `C:\Users\<you>\.nuke\nuke_optimizer_data\config.json`
- macOS: `/Users/<you>/.nuke/nuke_optimizer_data/config.json`
- Linux: `/home/<you>/.nuke/nuke_optimizer_data/config.json`

### What’s stored (JSON schema)
```json
{
  "version": 1,
  "classes": ["Kronos", "ZDefocus2"],
  "toggled": ["Kronos"]
}
```

- `classes`: ordered list of node **Class** names shown in the editor.
- `toggled`: subset of `classes` that are currently **active** (checked in the editor).
- First run behavior: the default list is present, and **nothing is active** until you check classes.

### When it writes to disk
- The editor auto-saves shortly after edits (check/uncheck, add/remove, reorder, import, reset defaults).

### Reset / recovery
- Use **Optimizer editor → Reset defaults**.
- Or delete the config file; it will be recreated on next run.

### Presets (import/export)
- JSON: `{"version": <int>, "classes": [...], "toggled": [...]}`
- CSV: `class,toggled` (toggled supports `1/0`, `true/false`, `yes/no`)

## Logging

### Log file location
- Windows: `C:\Users\<you>\.nuke\optimizer.log`
- macOS: `/Users/<you>/.nuke/optimizer.log`
- Linux: `/home/<you>/.nuke/optimizer.log`

### Rotation
- Rotates at ~**1 MB** per file
- Keeps up to **5** backups: `optimizer.log.1` … `optimizer.log.5`

### Need more detail?
- Set the log level to `DEBUG` in `mvc/app.py` (`LOG_LEVEL = logging.DEBUG`).

## How it works (high-level)

- `menu.py` registers menu commands/hotkeys (GUI sessions).
- `nuke_services.py` finds target nodes and sets the `disable` knob.
- The editor UI (MVC) updates the class list and persists config.

## Troubleshooting

### Menu doesn’t appear
- Confirm the folder is in the plugin path (Script Editor): `print(nuke.pluginPath())`
- Restart Nuke (GUI).

### `ModuleNotFoundError: No module named 'PySide2'` in Nuke 16+
- Nuke 16+ uses PySide6; any plugin importing PySide2 directly will fail.
- This repo uses a compatibility shim, but check custom/local edits and other plugins first.

### Tool does nothing
- No classes are toggled in the editor
- No nodes of those classes exist in the script
- Target nodes lack a `disable` knob (skipped)

## Roadmap (small)
- Add demo GIF + procedural demo `.nk`
- Optional: undo block around bulk toggles
- Optional: selection-only mode (if requested)

## License
MIT License. See [LICENSE](LICENSE).
