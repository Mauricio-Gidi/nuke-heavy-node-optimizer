"""Read/write the Optimizer config file (JSON)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

from optimizer import config
from optimizer.text_utils import unique_stripped_strings


logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Config persistence error."""


def _canonicalize(data: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize config data in-place and return it.

    Ensures:
      - `classes` has no duplicates (order preserved, first occurrence wins)
      - `toggled` has no duplicates (order preserved)
      - `toggled` is a subset of `classes`
    """
    classes = unique_stripped_strings(data.get("classes", []), require_list=True)
    toggled = unique_stripped_strings(data.get("toggled", []), require_list=True)

    allowed = set(classes)
    toggled = [name for name in toggled if name in allowed]

    data["classes"] = classes
    data["toggled"] = toggled
    return data


def safe_load_or_default() -> dict[str, Any]:
    """Return a valid configuration mapping, creating one if needed.

    Attempts to load the configuration from disk using `load()`. If loading
    fails for any reason represented by `StorageError` or `OSError` (for
    example, missing file, invalid JSON, failing `validate()`, or unexpected
    I/O errors), a new configuration is constructed from defaults and
    returned.

    This function does not propagate `StorageError` or `OSError`; both are
    logged at warning level. If persisting regenerated defaults fails, the
    in-memory defaults are still returned.

    The returned mapping always contains at least the keys:

    - `version`: Integer configuration version.
    - `classes`: List of class names.
    - `toggled`: List of class names that are enabled in the UI.

    Returns:
        dict[str, Any]: A validated configuration mapping suitable for use
        by the rest of the Optimizer code.
    """
    try:
        return load()
    except (StorageError, OSError) as e:
        logger.warning(
            "Config load failed or is outdated, falling back to defaults "
            "(reason: %s). Old config detected, resetting to defaults.",
            e,
        )
        from optimizer import defaults

        data: dict[str, Any] = {
            "version": config.CONFIG_VERSION,
            "classes": list(defaults.RENDER_INTENSIVE_NODES),
            "toggled": list(defaults.RENDER_INTENSIVE_NODES),  # default: enabled on first run
        }
        _canonicalize(data)
        try:
            save(data)
        except OSError as save_err:
            logger.warning(
                "Could not write default Optimizer config to disk: %s", save_err
            )
        return data


def load() -> dict[str, Any]:
    """Load the configuration from disk.

    Reads the JSON configuration file from the path computed by
    `_config_path()`, parses it, and validates the resulting mapping
    using `validate()`.

    Returns:
        dict[str, Any]: The configuration mapping if the file exists, can be
        parsed as JSON, and passes `validate()`.

    Raises:
        StorageError: If the configuration file does not exist, is not valid
            JSON, or has an invalid or outdated schema.
        OSError: If the underlying file I/O fails unexpectedly.
    """
    config_path = _config_path()
    if not config_path.exists():
        raise StorageError(f"Config not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except json.JSONDecodeError as json_decode_error:
        raise StorageError(f"Config is not valid JSON: {config_path}") from json_decode_error
    except OSError:
        # Re-raise unexpected I/O errors to the caller.
        raise

    if not isinstance(data, dict) or not validate(data):
        raise StorageError(f"Invalid config schema: {config_path}")

    return _canonicalize(data)


def save(metadata: dict[str, Any]) -> None:
    """Persist a configuration mapping to disk.

    Performs light normalization to ensure that all required keys are present
    before writing:

    - `version` is set to `config.CONFIG_VERSION` if missing.
    - `classes` is initialized from `optimizer.defaults.RENDER_INTENSIVE_NODES`
      if missing.
    - `toggled` is ensured to be a list (defaults to `[]` if missing or of the
      wrong type).

    The normalized mapping is then written as JSON to the path returned by
    `_config_path()`, creating parent directories as needed.

    Args:
        metadata: Mapping to write as JSON. Must be a dictionary; otherwise
            a `ValueError` is raised.

    Raises:
        ValueError: If `metadata` is not a dictionary.
        OSError: If the configuration file cannot be written.
    """
    if not isinstance(metadata, dict):
        raise ValueError("storage.save(metadata): expected a dict")
    config_path = _config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # --- light normalization (add a 'toggled' list if missing)
    if "version" not in metadata:
        metadata["version"] = config.CONFIG_VERSION
    if "classes" not in metadata or not isinstance(metadata.get("classes"), list):
        from optimizer import defaults

        metadata["classes"] = list(defaults.RENDER_INTENSIVE_NODES)
    else:
        # Keep only strings; `_canonicalize` will strip, drop empties, and dedupe.
        metadata["classes"] = [x for x in metadata["classes"] if isinstance(x, str)]
    if "toggled" not in metadata or not isinstance(metadata["toggled"], list):
        metadata["toggled"] = []
    else:
        metadata["toggled"] = [x for x in metadata["toggled"] if isinstance(x, str)]

    _canonicalize(metadata)

    with config_path.open("w", encoding="utf-8") as file_handle:
        json.dump(metadata, file_handle, indent=2, ensure_ascii=False)


def validate(data: dict[str, Any]) -> bool:
    """Validate a configuration mapping read from disk.

    Checks that the mapping has the expected structure, contains required
    keys, and uses a non-outdated configuration version. The following
    conditions must hold for the data to be considered valid:

    - `data` is a `dict`.
    - Keys `version` and `classes` are present.
    - `version` is an `int` and greater than or equal to `config.CONFIG_VERSION`.
    - `classes` is a list of strings.
    - If present, `toggled` is a list of strings.

    Args:
        data: Configuration mapping to validate.

    Returns:
        bool: `True` if the configuration looks valid and up to date,
        `False` otherwise.
    """
    if not isinstance(data, dict):
        return False

    if "version" not in data or "classes" not in data:
        return False

    if not isinstance(data["version"], int):
        return False

    if data["version"] < config.CONFIG_VERSION:
        # We only log here; the caller (safe_load_or_default) will decide
        # whether to reset the configuration back to defaults.
        logger.info(
            "Config version %s is older than current CONFIG_VERSION=%s",
            data["version"],
            config.CONFIG_VERSION,
        )
        return False

    if not isinstance(data["classes"], list) or not all(
        isinstance(x, str) for x in data["classes"]
    ):
        return False

    if "toggled" in data:
        if not isinstance(data["toggled"], list) or not all(
            isinstance(x, str) for x in data["toggled"]
        ):
            return False

    return True


# -----------------------------------------------------------------------------
# Path helpers (package)
# -----------------------------------------------------------------------------


def _config_path() -> Path:
    """Compute the on-disk path for the JSON configuration file.

    The configuration lives under the user's Nuke home directory, in a
    subdirectory derived from `config.APP_DIR_NAME`:

        ~/.nuke/{app_dir}_data/{file_name}

    where `app_dir` is `config.APP_DIR_NAME` and `file_name` is
    `config.FILE_NAME`.

    This function does not create any directories or files; directory
    creation happens in `save()`.

    Returns:
        Path: Absolute path to the JSON config file on disk.
    """
    root = Path.home() / ".nuke" / f"{config.APP_DIR_NAME}"
    return root / config.FILE_NAME


