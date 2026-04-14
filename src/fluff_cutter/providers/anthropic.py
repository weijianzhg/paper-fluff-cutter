"""Anthropic provider implementation with native PDF support."""

from typing import Iterator

import anthropic

from .base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider with native PDF support."""

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-5"

    @property
    def provider_name(self) -> str:
        return "Anthropic"

    def analyze_paper(self, pdf_base64: str, filename: str, prompt: str) -> str:
        """
        Analyze a paper using Anthropic's native PDF support.

        Args:
            pdf_base64: Base64-encoded PDF data.
            filename: Original filename of the PDF.
            prompt: The analysis prompt to send to the model.

        Returns:
            The model's analysis as a string.
        """
        client = anthropic.Anthropic(api_key=self.api_key)

        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        # Extract text from the response
        text_blocks = [block.text for block in response.content if block.type == "text"]
        return "\n".join(text_blocks)

    def analyze_paper_stream(self, pdf_base64: str, filename: str, prompt: str) -> Iterator[str]:
        """
        Analyze a paper and stream Anthropic text deltas.

        Args:
            pdf_base64: Base64-encoded PDF data.
            filename: Original filename of the PDF.
            prompt: The analysis prompt to send to the model.

        Yields:
            Incremental text chunks from the model response.
        """
        client = anthropic.Anthropic(api_key=self.api_key)

        with client.messages.stream(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        ) as stream:
            for text in stream.text_stream:
                if text:
                    yield text
