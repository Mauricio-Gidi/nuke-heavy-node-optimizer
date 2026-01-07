# Nuke Heavy Node Optimizer (`nuke-heavy-node-optimizer`)

Bulk **disable / enable / toggle** “heavy” nodes (by node **Class**) across a script, with a small editor UI to manage the class list.

- Menu: `Nuke > Scripts > Optimizer`
- Hotkey: **Ctrl+Alt+O**
- Safety: only touches each node’s `disable` knob

## Demo

<!-- Uncomment once the file exists:
![Toggle heavy nodes demo](media/demo_toggle.gif)
-->

Short demo (coming next): one hotkey toggles **N heavy nodes** (**N→1 action**).

**Planned 10–20s GIF (procedural / no external footage):**
1. Show Node Graph + Viewer with the “heavy nodes” chain **enabled**.
2. Briefly show: `Nuke > Scripts > Optimizer`.
3. Trigger **Toggle heavy nodes** (Ctrl+Alt+O) → nodes go **disabled** (visible in graph) and Viewer output changes.
4. Optional: toggle again for a quick **A/B/A** loop.
5. Optional (1–2s): open **Optimizer editor** to show the class list is configurable.

Planned screenshots:
- `media/screenshot_menu.png` (Scripts > Optimizer menu)
- `media/screenshot_editor.png` (Optimizer editor)

## Quick start

1) Copy `nuke_optimizer/` into your `.nuke` directory:
- Windows: `C:\Users\<you>\.nuke\`
- macOS: `/Users/<you>/.nuke/`
- Linux: `/home/<you>/.nuke/`

2) Add this to `~/.nuke/init.py` (create if needed):

```python
import nuke
nuke.pluginAddPath("./nuke_optimizer")
```

3) Restart Nuke (GUI) → open:
- `Nuke > Scripts > Optimizer > Toggle heavy nodes`

## Problem

Heavy nodes (retime/denoise/defocus/mblur/etc.) can make scripts sluggish for viewer playback and test renders. Manually hunting and disabling nodes is repetitive and increases the chance of forgetting to re-enable before final output.

## Solution

Provides one menu/hotkey action to toggle a configurable list of node classes by setting only the node `disable` knob, plus a small editor UI to manage that list.

## Measurable impact

Preview switching becomes **N manual edits → 1 action** (N = number of heavy nodes in the script; the planned demo uses ~10–30 nodes).

## Features

- Toggle / Disable / Enable heavy nodes (by Class)
- Editor UI to manage the class list (and choose which classes are active)
- Config saved to JSON
- Rotating log file for debugging

## Requirements / Compatibility

### Tested (verified)
- **Windows**: Nuke **13.0v10**, **15.2v6**, **16.0v8**

### Supported (claimed)
- **Nuke 13+ → Nuke 16+**
- Nuke 16+ uses **PySide6 / Qt 6.5** (and Python 3.11).  
  This repo includes a small Qt compatibility shim (`mvc/qt_compat.py`) to run on both:
  - **PySide2 / Qt5** (Nuke 13–15)
  - **PySide6 / Qt6** (Nuke 16+)

### Not tested
- **macOS / Linux** (expected to work, but not currently in the test matrix)

## Usage

### Behavior definitions

- **Heavy class**: a node class name listed in the Optimizer editor (e.g., `ZDefocus`, `TimeBlur`).
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
- Windows: `C:\Users\<you>\.nuke\nuke_optimizer_data\config.json`
- macOS: `/Users/<you>/.nuke/nuke_optimizer_data/config.json`
- Linux: `/home/<you>/.nuke/nuke_optimizer_data/config.json`

### What’s stored (JSON schema)
```json
{
  "version": 1,
  "classes": ["ZDefocus", "TimeBlur"],
  "toggled": ["ZDefocus"]
}
```

- `classes`: ordered list of node Class names shown in the editor.
- `toggled`: subset of `classes` that are currently active (checked).
- Default on first run: `toggled` is empty (nothing active until you check classes).

### Reset / recovery
- Use **Optimizer editor → Reset defaults** (restores default class list), or delete the config file and restart Nuke.

Preset formats (import/export):
- JSON: `{"version": <int>, "classes": [...], "toggled": [...]}`
- CSV: `class,toggled`

## Logging

Log file:
- Windows: `C:\\Users\\<you>\\.nuke\\optimizer.log`
- macOS: `/Users/<you>/.nuke/optimizer.log`
- Linux: `/home/<you>/.nuke/optimizer.log`

## How it works (high-level)

- `menu.py` registers menu commands and the hotkey (GUI sessions).
- The editor UI (MVC) updates the class list and persists it to JSON.
- Actions load config, find nodes by class via Nuke’s API, then set each node’s `disable` knob.

## Troubleshooting

### Menu or hotkey doesn’t appear
- Confirm you are launching Nuke with a **GUI** (menu.py doesn’t run in terminal sessions).
- In Script Editor:
  ```python
  import nuke
  print(nuke.pluginPath())
  ```
  Confirm your `.nuke` path (and/or `./nuke_optimizer`) is listed, then restart Nuke.

### `ModuleNotFoundError: No module named 'PySide2'` in Nuke 16+
- Nuke 16+ uses PySide6; any plugin importing PySide2 directly will fail.
- This repo uses a compatibility shim; if you edited imports, revert to the shim approach.
- Check `optimizer.log` for the exact failing module.

### “Tool does nothing”
- No classes are active (checked) in the editor
- No nodes of those classes exist in the script
- Target nodes lack a `disable` knob (skipped)

## License

MIT License. See [LICENSE](LICENSE).
