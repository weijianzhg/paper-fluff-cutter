"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest
import yaml

from fluff_cutter.config import (
    get_api_key,
    get_default_model,
    get_default_provider,
    is_configured,
    load_config,
    load_config_file,
    save_config,
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".fluff-cutter"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def mock_config_file(temp_config_dir, tmp_path):
    """Patch the config file location to use temp directory."""
    config_file = temp_config_dir / "config.yaml"
    # Create a non-existent old config path to prevent migration
    old_config_dir = tmp_path / "old_config"
    old_config_file = old_config_dir / "config.json"
    with patch("fluff_cutter.config.CONFIG_FILE", config_file):
        with patch("fluff_cutter.config.CONFIG_DIR", temp_config_dir):
            with patch("fluff_cutter.config.OLD_CONFIG_FILE", old_config_file):
                with patch("fluff_cutter.config.OLD_CONFIG_DIR", old_config_dir):
                    yield config_file


class TestLoadConfigFile:
    """Tests for load_config_file function."""

    def test_returns_empty_dict_when_no_file(self, mock_config_file):
        """Should return empty dict when config file doesn't exist."""
        assert load_config_file() == {}

    def test_loads_valid_config(self, mock_config_file):
        """Should load and return config from file."""
        config_data = {"openai_api_key": "sk-test", "default_provider": "openai"}
        mock_config_file.write_text(yaml.dump(config_data))

        result = load_config_file()

        assert result == config_data

    def test_returns_empty_dict_on_invalid_yaml(self, mock_config_file):
        """Should return empty dict when config file has invalid YAML."""
        mock_config_file.write_text("invalid: yaml: content: [")

        assert load_config_file() == {}


class TestSaveConfig:
    """Tests for save_config function."""

    def test_saves_config_to_file(self, mock_config_file, temp_config_dir):
        """Should save config to file."""
        config_data = {"anthropic_api_key": "sk-ant-test", "default_provider": "anthropic"}

        save_config(config_data)

        saved = yaml.safe_load(mock_config_file.read_text())
        assert saved == config_data

    def test_creates_directory_if_not_exists(self, tmp_path):
        """Should create config directory if it doesn't exist."""
        config_dir = tmp_path / "new_dir" / ".fluff-cutter"
        config_file = config_dir / "config.yaml"
        old_config_dir = tmp_path / "old_config"
        old_config_file = old_config_dir / "config.json"

        with patch("fluff_cutter.config.CONFIG_FILE", config_file):
            with patch("fluff_cutter.config.CONFIG_DIR", config_dir):
                with patch("fluff_cutter.config.OLD_CONFIG_FILE", old_config_file):
                    with patch("fluff_cutter.config.OLD_CONFIG_DIR", old_config_dir):
                        save_config({"test": "value"})

        assert config_file.exists()


class TestLoadConfig:
    """Tests for load_config function with environment variable precedence."""

    def test_env_vars_override_config_file(self, mock_config_file):
        """Environment variables should override config file values."""
        # Save config file with one set of values
        config_data = {"openai_api_key": "file-key", "default_provider": "openai"}
        mock_config_file.write_text(yaml.dump(config_data))

        # Set environment variables with different values
        env_vars = {
            "OPENAI_API_KEY": "env-key",
            "FLUFF_CUTTER_PROVIDER": "anthropic",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            result = load_config()

        assert result["openai_api_key"] == "env-key"
        assert result["default_provider"] == "anthropic"

    def test_model_env_vars(self, mock_config_file):
        """Model environment variables should be loaded."""
        env_vars = {
            "FLUFF_CUTTER_OPENAI_MODEL": "gpt-5.2-turbo",
            "FLUFF_CUTTER_ANTHROPIC_MODEL": "claude-opus-4-5-latest",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            result = load_config()

        assert result["openai_model"] == "gpt-5.2-turbo"
        assert result["anthropic_model"] == "claude-opus-4-5-latest"


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_returns_key_from_config(self, mock_config_file):
        """Should return API key from config."""
        config_data = {"openai_api_key": "sk-test-key"}
        mock_config_file.write_text(yaml.dump(config_data))

        result = get_api_key("openai")

        assert result == "sk-test-key"

    def test_returns_none_when_not_configured(self, mock_config_file):
        """Should return None when API key is not configured."""
        result = get_api_key("openai")

        assert result is None


class TestGetDefaultProvider:
    """Tests for get_default_provider function."""

    def test_returns_configured_provider(self, mock_config_file):
        """Should return configured default provider."""
        config_data = {"default_provider": "openai"}
        mock_config_file.write_text(yaml.dump(config_data))

        result = get_default_provider()

        assert result == "openai"

    def test_returns_anthropic_as_fallback(self, mock_config_file):
        """Should return 'anthropic' as default when not configured."""
        result = get_default_provider()

        assert result == "anthropic"


class TestGetDefaultModel:
    """Tests for get_default_model function."""

    def test_returns_configured_model(self, mock_config_file):
        """Should return configured model for provider."""
        config_data = {"openai_model": "gpt-5.2-custom"}
        mock_config_file.write_text(yaml.dump(config_data))

        result = get_default_model("openai")

        assert result == "gpt-5.2-custom"

    def test_returns_none_when_not_configured(self, mock_config_file):
        """Should return None when model is not configured."""
        result = get_default_model("openai")

        assert result is None


class TestIsConfigured:
    """Tests for is_configured function."""

    def test_returns_true_with_openai_key(self, mock_config_file):
        """Should return True when OpenAI key is configured."""
        config_data = {"openai_api_key": "sk-test"}
        mock_config_file.write_text(yaml.dump(config_data))

        assert is_configured() is True

    def test_returns_true_with_anthropic_key(self, mock_config_file):
        """Should return True when Anthropic key is configured."""
        config_data = {"anthropic_api_key": "sk-ant-test"}
        mock_config_file.write_text(yaml.dump(config_data))

        assert is_configured() is True

    def test_returns_false_when_no_keys(self, mock_config_file):
        """Should return False when no API keys are configured."""
        assert is_configured() is False
