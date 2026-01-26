"""Config paths and constants for the Optimizer tool."""

# Configuration file version.
#
# Bump this integer whenever the shape or meaning of the JSON config
# changes in a non-backwards-compatible way. The storage layer compares
# the value on disk against this constant and, if the stored version is
# incompatible, will reset the configuration to defaults.
CONFIG_VERSION: int = 1

# Directory name under the user's Nuke home used to store Optimizer data.
#
# The full path is computed by optimizer.storage and is typically:
#   ~/.nuke/<APP_DIR_NAME>/<FILE_NAME>
APP_DIR_NAME: str = "nuke_optimizer_data"

# File name for the JSON configuration stored on disk.
#
# This is combined with APP_DIR_NAME inside optimizer.storage to
# form the full configuration path.
FILE_NAME: str = "config.json"
