"""Base class for LLM providers."""

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers with PDF support."""

    def __init__(self, api_key: str, model: str | None = None):
        """
        Initialize the provider.

        Args:
            api_key: API key for the provider.
            model: Optional model override. If not provided, uses default.
        """
        self.api_key = api_key
        self.model = model or self.default_model

    @property
    @abstractmethod
    def default_model(self) -> str:
        """The default model to use for this provider."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name of the provider."""
        pass

    @abstractmethod
    def analyze_paper(self, pdf_base64: str, filename: str, prompt: str) -> str:
        """
        Analyze a paper PDF using native PDF support.

        Args:
            pdf_base64: Base64-encoded PDF data.
            filename: Original filename of the PDF.
            prompt: The analysis prompt to send to the model.

        Returns:
            The model's analysis as a string.
        """
        pass

    def get_model_info(self) -> str:
        """Get a string describing the provider and model being used."""
        return f"{self.provider_name} ({self.model})"
