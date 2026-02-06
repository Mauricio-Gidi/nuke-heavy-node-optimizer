# Nuke Heavy Node Optimizer (`nuke-heavy-node-optimizer`)
![Nuke](https://img.shields.io/badge/Nuke-13%2B-informational)
![Qt](https://img.shields.io/badge/PySide-PySide2%20%7C%20PySide6-informational)
![OS](https://img.shields.io/badge/OS-Windows%20%7C%20macOS%20%7C%20Linux-informational)
![License](https://img.shields.io/badge/License-MIT-success)

Bulk disable, enable, or toggle "heavy" nodes (by node class) across the current Nuke script - safely (only touches each node's disable knob).

![Toggle heavy nodes demo](media/demo_toggle.gif)

**Read next:**
- **Case study:** [`docs/case-study-heavy-node-optimizer.md`](docs/case-study-heavy-node-optimizer.md)
- Install: jump to [Quick start](#quick-start)
- Usage: jump to [Usage](#usage)

**Key facts:**
- Menu: `Nuke > Scripts > Optimizer`  |  Hotkey: **Ctrl+Alt+O**
- Undo: bulk actions are **one** undo step
- Defaults: **common heavy nodes are enabled on first run** (editable in the Optimizer editor)

Links: [Portfolio](https://mauricio-gidi.github.io) | [GitHub](https://github.com/Mauricio-Gidi) | [LinkedIn](https://www.linkedin.com/in/mauricio-gidi-29689b22a/)

## Quick start

1) Copy the entire `nuke_optimizer/` folder into your `.nuke` directory so you end up with:
- Windows: `C:\Users\<you>\.nuke\nuke_optimizer\`
- macOS: `/Users/<you>/.nuke/nuke_optimizer/`
- Linux: `/home/<you>/.nuke/nuke_optimizer/`

2) Add this to your `.nuke/init.py` (create if needed):
- Windows: `C:\Users\<you>\.nuke\init.py`
- macOS/Linux: `~/.nuke/init.py`

```python
import nuke
nuke.pluginAddPath("./nuke_optimizer")
```

3) Restart Nuke (GUI) → open:
- `Nuke > Scripts > Optimizer > Toggle heavy nodes`

## Repository layout

```text
nuke-heavy-node-optimizer/
├─ nuke_optimizer/                # Nuke plugin package (this is what you install)
│  ├─ menu.py                     # Nuke menu registration entrypoint
│  ├─ mvc/                        # UI (Qt) layer
│  └─ optimizer/                  # Nuke-facing services + persistence
├─ docs/
│  └─ case-study-heavy-node-optimizer.md
└─ media/
   └─ demo_toggle.gif
```

## Problem

Heavy nodes (retime/denoise/defocus/mblur/etc.) can make scripts sluggish for viewer playback and test renders. Manually hunting and disabling nodes is repetitive and increases the chance of forgetting to re-enable before final output.

## Solution

Provides one menu/hotkey action to toggle a configurable list of node classes by setting only the node `disable` knob, plus a small editor UI to manage that list.

## Measurable impact

Preview switching becomes **N manual edits → 1 action** (N = number of heavy nodes in the script).

## Features

- Toggle / Disable / Enable heavy nodes (by Class)
- Editor UI to manage the class list (and choose which classes are active)
- Config saved to JSON
- Rotating log file for debugging

## Requirements / Compatibility

### Tested (verified)
- **Windows**: Nuke **13.0v10**, **15.2v6**, **16.0v8**

### Expected to work (untested)
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


## Share (quick blurb)

Bulk toggle heavy nodes in Nuke safely (only touches `disable`), with a class-list editor.

- Demo GIF: `media/demo_toggle.gif`
- Case study: `docs/case-study-heavy-node-optimizer.md`
- Repo: https://github.com/Mauricio-Gidi/nuke-heavy-node-optimizer
- Portfolio: https://mauricio-gidi.github.io/projects/#heavy-node-optimizer
- Install: see **Quick start** (or download the latest release from **Releases**).

## Safety, undo, and limitations

- **Undo:** Bulk actions (Toggle / Disable / Enable heavy nodes) are wrapped in **one** undo step (Ctrl+Z / Cmd+Z).
- **What it changes:** Only the `disable` knob on nodes whose **Class()** is marked as heavy and enabled in the Optimizer UI.
- **What it does not do:** Does not delete nodes, change connections, or modify any other knobs.
- **Limitations:** Nodes without a `disable` knob (or nodes that refuse edits due to locks/edge cases) are skipped and logged.

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
- Default on first run: `toggled` includes the default heavy-node class list (you can uncheck anything you don’t want).

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

## Feedback / bug reports

Open an issue: https://github.com/Mauricio-Gidi/nuke-heavy-node-optimizer/issues

Please include (so it’s reproducible):
- Nuke version (e.g. 15.2v6) + OS (Windows/macOS/Linux)
- Qt binding (PySide2 for Nuke 13–15, PySide6 for Nuke 16+)
- Steps to reproduce + expected vs actual
- Log file (`optimizer.log`) from the **Logging** section above
- (Optional) your config file from **Configuration** (redact any studio paths)

Copy/paste template:
```text
Nuke version:
OS:
Qt (PySide2/PySide6):
What I did (steps):
Expected:
Actual:
Log attached:
Config attached (optional):
```

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

### “Tool does nothing”
- No classes are active (checked) in the editor (you may have unchecked all)
- No nodes of those classes exist in the script
- Target nodes lack a `disable` knob (skipped)

## License

MIT License. See [LICENSE](LICENSE).
