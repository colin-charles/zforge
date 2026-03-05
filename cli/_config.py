"""Shared credential / configuration helpers for the zforge CLI.

All config lives in ~/.zforge/config.json (chmod 600).
This module is the single source of truth for reading and writing it.
"""
import json as _json
from pathlib import Path

CONFIG_DIR: Path = Path.home() / ".zforge"
CONFIG_PATH: Path = CONFIG_DIR / "config.json"


def load_credentials() -> dict:
    """Load saved API key + handle from ~/.zforge/config.json.

    Returns an empty dict if the file is missing or unreadable.
    """
    if not CONFIG_PATH.exists():
        return {}
    try:
        return _json.loads(CONFIG_PATH.read_text())
    except Exception:
        return {}


def save_credentials(api_key: str, handle: str) -> None:
    """Persist *api_key* and *handle* into ~/.zforge/config.json (chmod 600).

    Merges with any existing keys so other config values are preserved.
    """
    CONFIG_DIR.mkdir(exist_ok=True)
    config: dict = {}
    if CONFIG_PATH.exists():
        try:
            config = _json.loads(CONFIG_PATH.read_text())
        except Exception:
            config = {}
    config["api_key"] = api_key
    config["handle"] = handle
    CONFIG_PATH.write_text(_json.dumps(config, indent=2))
    CONFIG_PATH.chmod(0o600)
