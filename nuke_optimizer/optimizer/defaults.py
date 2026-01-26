"""Factory default list of heavy node classes."""

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
