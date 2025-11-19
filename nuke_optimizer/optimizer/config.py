"""Global configuration constants for the Optimizer tool.

Centralises basic configuration values that are shared across the
package, including the configuration version, the Nuke application
directory name, and the JSON file name used for persistence.

Concrete paths are computed by optimizer.storage based on these
constants; code outside this module should rely on the helpers there
rather than constructing paths manually.
"""

# Configuration file version.
#
# Bump this integer whenever the shape or meaning of the JSON config
# changes in a non–backwards-compatible way. The storage layer compares
# the value on disk against this constant and, if the stored version is
# older, will treat the config as outdated and reset it to defaults.
CONFIG_VERSION: int = 1

# Base directory name for all Optimizer data under the user's Nuke home.
#
# The storage module constructs the full path as:
#   Path.home() / ".nuke" / f"{APP_DIR_NAME}_data" / FILE_NAME
#
# Changing this will cause the tool to look in a different directory
# (and effectively "forget" the previous configuration), so treat it as
# a stable identifier for this application.
APP_DIR_NAME: str = "nuke_optimizer"

# File name for the JSON configuration stored on disk.
#
# This is combined with APP_DIR_NAME inside optimizer.storage to
# form the full configuration path.
FILE_NAME: str = "config.json"

# Defaults for UI behavior (reserved for future use).
# The comments below document intended semantics for potential future
# configuration keys that may live alongside the constants above:
#
#   - scope: "selected" / "all"  → whether operations act only on
#     selected nodes or on every node in the script.
#   - recurse_into_groups: bool  → whether group nodes should be recursed
#     into when searching for heavy nodes.
