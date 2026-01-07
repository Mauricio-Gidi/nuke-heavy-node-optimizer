"""Factory defaults for the Optimizer tool.

Defines the canonical list of heavy node classes used by the Optimizer.
Other modules (such as storage and the controller) use this list when
creating a brand-new configuration or when falling back to safe
defaults.

This module is intentionally data-only: it performs no I/O, and the
order and spelling of entries are expected to match Nuke Class() names
exactly.
"""

from __future__ import annotations

try:
    # Python 3.8+
    from typing import Final, Tuple
except ImportError:
    # Python 3.7 (Nuke 13.x): Final is provided by typing_extensions
    from typing import Tuple

    from typing_extensions import Final

# Canonical list consumed by the app.
# This tuple represents the built-in set of heavy node classes. Users can
# later override or extend this list via the Optimizer UI and config.
RENDER_INTENSIVE_NODES: Final[Tuple[str, ...]] = (
    # Retiming
    "Kronos",  # NukeX/Studio
    "OFlow2",
    "TimeBlur",
    # Motion blur
    "MotionBlur",  # NukeX/Studio
    "MotionBlur3D",
    "VectorBlur2",
    # Defocus / bokeh
    "Defocus",
    "ZDefocus2",
    "Convolve2",
    # Denoise
    "Denoise2",
    # Deep
    "DeepRecolor",
)

# Sanity guard: enforce uniqueness at import time.
# Since this module defines the "factory default" class list, duplicated
# entries would cause confusing UI behavior and inconsistent counts, so
# fail fast if a duplicate ever sneaks in.
if len(set(RENDER_INTENSIVE_NODES)) != len(RENDER_INTENSIVE_NODES):
    raise ValueError("Duplicate class in RENDER_INTENSIVE_NODES")
