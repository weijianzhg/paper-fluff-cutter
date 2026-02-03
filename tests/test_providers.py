"""Tests for LLM providers."""

import pytest

from fluff_cutter.providers import AnthropicProvider, OpenAIProvider
from fluff_cutter.providers.base import BaseLLMProvider


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_default_model(self):
        """Should have correct default model."""
        provider = OpenAIProvider(api_key="test-key")

        assert provider.default_model == "gpt-5.2"

    def test_provider_name(self):
        """Should return correct provider name."""
        provider = OpenAIProvider(api_key="test-key")

        assert provider.provider_name == "OpenAI"

    def test_custom_model_override(self):
        """Should allow custom model override."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-5.2-turbo")

        assert provider.model == "gpt-5.2-turbo"

    def test_uses_default_when_no_model_specified(self):
        """Should use default model when none specified."""
        provider = OpenAIProvider(api_key="test-key")

        assert provider.model == "gpt-5.2"

    def test_get_model_info(self):
        """Should return formatted model info string."""
        provider = OpenAIProvider(api_key="test-key")

        result = provider.get_model_info()

        assert result == "OpenAI (gpt-5.2)"


class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    def test_default_model(self):
        """Should have correct default model."""
        provider = AnthropicProvider(api_key="test-key")

        assert provider.default_model == "claude-opus-4-5"

    def test_provider_name(self):
        """Should return correct provider name."""
        provider = AnthropicProvider(api_key="test-key")

        assert provider.provider_name == "Anthropic"

    def test_custom_model_override(self):
        """Should allow custom model override."""
        provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-4-20250514")

        assert provider.model == "claude-sonnet-4-20250514"

    def test_uses_default_when_no_model_specified(self):
        """Should use default model when none specified."""
        provider = AnthropicProvider(api_key="test-key")

        assert provider.model == "claude-opus-4-5"

    def test_get_model_info(self):
        """Should return formatted model info string."""
        provider = AnthropicProvider(api_key="test-key")

        result = provider.get_model_info()

        assert result == "Anthropic (claude-opus-4-5)"


class TestBaseLLMProvider:
    """Tests for base provider class."""

    def test_is_abstract(self):
        """Should not be instantiable directly."""
        with pytest.raises(TypeError):
            BaseLLMProvider(api_key="test")

    def test_stores_api_key(self):
        """Concrete implementations should store API key."""
        provider = OpenAIProvider(api_key="my-secret-key")

        assert provider.api_key == "my-secret-key"
