"""Tests for LLM providers."""

import pytest

import fluff_cutter.providers.anthropic as anthropic_provider_module
import fluff_cutter.providers.openai as openai_provider_module
import fluff_cutter.providers.openrouter as openrouter_provider_module
from fluff_cutter.providers import AnthropicProvider, OpenAIProvider, OpenRouterProvider
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

    def test_analyze_paper_stream_yields_output_text_deltas(self, monkeypatch):
        """Should yield only output_text delta chunks from the stream."""

        class Event:
            def __init__(self, event_type, delta=None):
                self.type = event_type
                self.delta = delta

        class FakeResponses:
            def create(self, **kwargs):
                assert kwargs["stream"] is True
                return iter(
                    [
                        Event("response.created"),
                        Event("response.output_text.delta", "Hello "),
                        Event("response.output_text.delta", "world"),
                        Event("response.completed"),
                    ]
                )

        class FakeClient:
            def __init__(self, api_key):
                self.api_key = api_key
                self.responses = FakeResponses()

        monkeypatch.setattr(openai_provider_module, "OpenAI", FakeClient)

        provider = OpenAIProvider(api_key="test-key")
        chunks = list(provider.analyze_paper_stream("base64", "paper.pdf", "Prompt"))

        assert chunks == ["Hello ", "world"]


class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    def test_default_model(self):
        """Should have correct default model."""
        provider = AnthropicProvider(api_key="test-key")

        assert provider.default_model == "claude-sonnet-4-5"

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

        assert provider.model == "claude-sonnet-4-5"

    def test_get_model_info(self):
        """Should return formatted model info string."""
        provider = AnthropicProvider(api_key="test-key")

        result = provider.get_model_info()

        assert result == "Anthropic (claude-sonnet-4-5)"

    def test_analyze_paper_stream_yields_text_stream(self, monkeypatch):
        """Should yield text chunks from Anthropic text_stream helper."""

        class FakeStream:
            text_stream = ["Chunk A", "Chunk B"]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

        class FakeMessages:
            def stream(self, **kwargs):
                assert kwargs["model"] == "claude-sonnet-4-5"
                return FakeStream()

        class FakeClient:
            def __init__(self, api_key):
                self.api_key = api_key
                self.messages = FakeMessages()

        monkeypatch.setattr(anthropic_provider_module.anthropic, "Anthropic", FakeClient)

        provider = AnthropicProvider(api_key="test-key")
        chunks = list(provider.analyze_paper_stream("base64", "paper.pdf", "Prompt"))

        assert chunks == ["Chunk A", "Chunk B"]


class TestOpenRouterProvider:
    """Tests for OpenRouter provider."""

    def test_default_model(self):
        """Should have correct default model."""
        provider = OpenRouterProvider(api_key="test-key")

        assert provider.default_model == "anthropic/claude-sonnet-4-5"

    def test_provider_name(self):
        """Should return correct provider name."""
        provider = OpenRouterProvider(api_key="test-key")

        assert provider.provider_name == "OpenRouter"

    def test_custom_model_override(self):
        """Should allow custom model override."""
        provider = OpenRouterProvider(api_key="test-key", model="openai/gpt-5.2")

        assert provider.model == "openai/gpt-5.2"

    def test_uses_default_when_no_model_specified(self):
        """Should use default model when none specified."""
        provider = OpenRouterProvider(api_key="test-key")

        assert provider.model == "anthropic/claude-sonnet-4-5"

    def test_get_model_info(self):
        """Should return formatted model info string."""
        provider = OpenRouterProvider(api_key="test-key")

        result = provider.get_model_info()

        assert result == "OpenRouter (anthropic/claude-sonnet-4-5)"

    def test_analyze_paper_stream_parses_sse_deltas(self, monkeypatch):
        """Should parse OpenRouter SSE data lines into text chunks."""

        class FakeResponse:
            def raise_for_status(self):
                return None

            def iter_lines(self):
                return iter(
                    [
                        ": OPENROUTER PROCESSING",
                        'data: {"choices":[{"delta":{"content":"Hello "}}]}',
                        'data: {"choices":[{"delta":{"content":"world"}}]}',
                        "data: [DONE]",
                    ]
                )

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

        class FakeClient:
            def __init__(self, timeout):
                self.timeout = timeout

            def stream(self, method, url, headers=None, json=None):
                assert method == "POST"
                assert json["stream"] is True
                return FakeResponse()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

        monkeypatch.setattr(openrouter_provider_module.httpx, "Client", FakeClient)

        provider = OpenRouterProvider(api_key="test-key")
        chunks = list(provider.analyze_paper_stream("base64", "paper.pdf", "Prompt"))

        assert chunks == ["Hello ", "world"]


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
