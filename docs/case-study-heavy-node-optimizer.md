# Nuke Heavy Node Optimizer — Case Study

**Repo:** https://github.com/Mauricio-Gidi/nuke-heavy-node-optimizer  
**Stack:** Nuke + Python (Qt/PySide)

## Overview
A lightweight Nuke tool that lets compositors **bulk disable / enable / toggle “heavy” nodes by node Class** using a menu action or hotkey. A small editor UI manages the “heavy class list” and saves it to a local JSON config. The tool only touches each node’s `disable` knob (safe, reversible).

## Demo (planned)
![Toggle heavy nodes demo](media/demo_toggle.gif)

**Planned assets**
- `/media/demo_toggle.gif`
- `/media/screenshot_nodegraph_before_after.png`
- `/media/screenshot_editor.png`

## Problem
- Heavy processing nodes can slow down iteration (viewer responsiveness + quick test renders).
- Manually disabling nodes is repetitive and inconsistent across scripts.
- It’s easy to forget to re-enable nodes before final output.

## Solution
- User-configurable list of “heavy” node **Classes**, managed in a small editor UI.
- One hotkey/menu action to **Toggle / Disable / Enable** all matching nodes.
- Safe operation: only modifies the `disable` knob (no rewiring, no other knob edits).

## Outcome (impact framing)
- Turns many manual per-node edits into **one repeatable action** (N edits → 1).
- Standardizes a predictable “preview mode” workflow via a saved class list.
- Reduces “forgot to re-enable” mistakes by providing a single global enable action.

## My role / responsibilities
- Designed the workflow UX (menu actions + editor UI) for compositor speed.
- Implemented node targeting by Class and safe bulk operations via the `disable` knob.
- Built persistence (JSON config/presets) and logging for troubleshooting.
- Ensured cross-version UI compatibility (PySide2 ↔ PySide6).

## How it works
- `menu.py` registers `Scripts > Optimizer` commands + hotkey (GUI sessions).  
- UI uses a small MVC layer (`mvc/`) and a compatibility shim (`qt_compat.py`).  
- Actions read config → find nodes by class via Nuke’s API → set `disable`.

## Compatibility / support posture
**Tested (verified):** Windows — Nuke **13.0v10**, **15.2v6**, **16.0v8**  
**Supported (claimed):** Nuke 13–16. Nuke 16+ uses PySide6; earlier versions use PySide2.

## Config + logs
- Config: `~/.nuke/nuke_optimizer_data/config.json`  
  Schema: `{ "version": 1, "classes": [...], "toggled": [...] }`
- Logs: `~/.nuke/optimizer.log` (rotating)
