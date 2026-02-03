"""Configuration management for Paper Fluff Cutter."""

import json
import os
from pathlib import Path
from typing import Any

# Config file location
CONFIG_DIR = Path.home() / ".config" / "fluff-cutter"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default values
DEFAULT_PROVIDER = "anthropic"


def get_config_path() -> Path:
    """Get the path to the config file."""
    return CONFIG_FILE


def load_config_file() -> dict[str, Any]:
    """
    Load configuration from the config file.

    Returns:
        Dictionary with config values, or empty dict if file doesn't exist.
    """
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict[str, Any]) -> None:
    """
    Save configuration to the config file.

    Args:
        config: Dictionary with config values to save.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def load_config() -> dict[str, Any]:
    """
    Load configuration with precedence:
    1. Environment variables (highest)
    2. Config file (lowest)

    Returns:
        Merged configuration dictionary.
    """
    # Start with config file values
    config = load_config_file()

    # Override with environment variables
    if os.environ.get("OPENAI_API_KEY"):
        config["openai_api_key"] = os.environ["OPENAI_API_KEY"]

    if os.environ.get("ANTHROPIC_API_KEY"):
        config["anthropic_api_key"] = os.environ["ANTHROPIC_API_KEY"]

    if os.environ.get("FLUFF_CUTTER_PROVIDER"):
        config["default_provider"] = os.environ["FLUFF_CUTTER_PROVIDER"]

    if os.environ.get("FLUFF_CUTTER_OPENAI_MODEL"):
        config["openai_model"] = os.environ["FLUFF_CUTTER_OPENAI_MODEL"]

    if os.environ.get("FLUFF_CUTTER_ANTHROPIC_MODEL"):
        config["anthropic_model"] = os.environ["FLUFF_CUTTER_ANTHROPIC_MODEL"]

    return config


def get_api_key(provider: str, config: dict[str, Any] | None = None) -> str | None:
    """
    Get the API key for a specific provider.

    Args:
        provider: The provider name ('openai' or 'anthropic').
        config: Optional pre-loaded config. If None, loads config.

    Returns:
        The API key or None if not configured.
    """
    if config is None:
        config = load_config()

    key_name = f"{provider}_api_key"
    return config.get(key_name)


def get_default_provider(config: dict[str, Any] | None = None) -> str:
    """
    Get the default provider.

    Args:
        config: Optional pre-loaded config. If None, loads config.

    Returns:
        The default provider name.
    """
    if config is None:
        config = load_config()

    return config.get("default_provider", DEFAULT_PROVIDER)


def get_default_model(provider: str, config: dict[str, Any] | None = None) -> str | None:
    """
    Get the configured default model for a provider.

    Args:
        provider: The provider name ('openai' or 'anthropic').
        config: Optional pre-loaded config. If None, loads config.

    Returns:
        The configured model name, or None to use provider default.
    """
    if config is None:
        config = load_config()

    model_key = f"{provider}_model"
    return config.get(model_key)


def is_configured() -> bool:
    """
    Check if at least one provider is configured.

    Returns:
        True if at least one API key is available.
    """
    config = load_config()
    return bool(config.get("openai_api_key") or config.get("anthropic_api_key"))
