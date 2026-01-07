# Nuke Heavy Node Optimizer (`nuke-heavy-node-optimizer`)

Bulk **disable / enable / toggle** “heavy” nodes (by node **Class**) across the whole script, with a small editor UI to manage the class list.

- Menu: `Nuke > Scripts > Optimizer`
- Hotkey: **Ctrl+Alt+O**
- Safety: only touches the node’s `disable` knob

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

## Problem

Heavy nodes (retime/denoise/defocus/mblur/etc.) can make scripts sluggish for viewer playback and test renders. Manually hunting and disabling nodes is repetitive and increases the chance of forgetting to re-enable before final output.

## Solution

Provides one menu/hotkey action to toggle a configurable list of node classes by setting only the node `disable` knob, plus a small editor UI to manage that list.

## Measurable impact

Reduces preview switching from **N manual knob edits → 1 action**, where **N** is the number of heavy nodes in the script.

## Features

- Toggle / Disable / Enable heavy nodes (by Class)
- Editor UI to manage the class list (and choose which classes are active)
- Config saved to JSON
- Log file for debugging

## Requirements / Compatibility

### Tested (verified)
- **Windows**: Nuke **13.x**, **15.2v6**, **16.x**

### Supported (claimed)
- **Nuke 13+ → Nuke 16+**
- Nuke 16+ uses **PySide6 / Qt 6.5** (and Python 3.11).  
  This repo includes a small Qt compatibility shim (`mvc/qt_compat.py`) to run on both:
  - **PySide2 / Qt5** (Nuke 13–15)
  - **PySide6 / Qt6** (Nuke 16+)

### Not tested
- **macOS / Linux** (expected to work, but not currently in the test matrix)

## Usage

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
  If any heavy node is enabled → disables all; otherwise enables all.
- `Disable Heavy Nodes` → `disable = True`
- `Enable Heavy Nodes` → `disable = False`

> Nodes without a `disable` knob are skipped.

## Configuration

- Config file is stored under your `~/.nuke/` folder in a tool-specific subdirectory.
- See `nuke_optimizer/optimizer/storage.py` for the exact computed path on your system.

Preset formats (import/export):
- JSON: `{"version": <int>, "classes": [...], "toggled": [...]}`
- CSV: `class,toggled`

## Logging

- Log file: `~/.nuke/optimizer.log`

## How it works (high-level)

- `menu.py` registers menu commands/hotkeys (GUI sessions).
- `nuke_services.py` finds nodes whose `Class()` is in the active list and sets the `disable` knob.
- The editor UI (MVC) updates the class list and persists config.

## Troubleshooting

### Menu doesn’t appear
- Confirm the folder is in the plugin path (Script Editor): `print(nuke.pluginPath())`
- Restart Nuke (GUI).

### `ModuleNotFoundError: No module named 'PySide2'` in Nuke 16+
- Nuke 16+ uses PySide6; any plugin importing PySide2 directly will fail.  
  This repo uses a compatibility shim, but check custom/local edits and other plugins first.

### Tool does nothing
- No classes are toggled in the editor
- No nodes of those classes exist in the script
- Target nodes lack a `disable` knob (skipped)

## Roadmap (small)

- Add demo GIF + demo `.nk` (procedural)
- Optional: undo block around bulk toggles
- Optional: selection-only mode (if requested)

## License

MIT License. See [LICENSE](LICENSE).
