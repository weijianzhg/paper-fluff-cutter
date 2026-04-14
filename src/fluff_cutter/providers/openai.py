"""OpenAI provider implementation with native PDF support."""

from typing import Iterator

from openai import OpenAI

from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT-5.2 provider with native PDF support."""

    @property
    def default_model(self) -> str:
        return "gpt-5.2"

    @property
    def provider_name(self) -> str:
        return "OpenAI"

    def analyze_paper(self, pdf_base64: str, filename: str, prompt: str) -> str:
        """
        Analyze a paper using OpenAI's native PDF support.

        Args:
            pdf_base64: Base64-encoded PDF data.
            filename: Original filename of the PDF.
            prompt: The analysis prompt to send to the model.

        Returns:
            The model's analysis as a string.
        """
        client = OpenAI(api_key=self.api_key)

        # Use the Responses API with native PDF support
        response = client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": filename,
                            "file_data": f"data:application/pdf;base64,{pdf_base64}",
                        },
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        return response.output_text or ""

    def analyze_paper_stream(self, pdf_base64: str, filename: str, prompt: str) -> Iterator[str]:
        """
        Analyze a paper and stream OpenAI response text deltas.

        Args:
            pdf_base64: Base64-encoded PDF data.
            filename: Original filename of the PDF.
            prompt: The analysis prompt to send to the model.

        Yields:
            Incremental text chunks from the model response.
        """
        client = OpenAI(api_key=self.api_key)

        stream = client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": filename,
                            "file_data": f"data:application/pdf;base64,{pdf_base64}",
                        },
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                    ],
                }
            ],
            stream=True,
        )

        for event in stream:
            event_type = getattr(event, "type", None)
            if event_type is None and isinstance(event, dict):
                event_type = event.get("type")

            if event_type == "response.output_text.delta":
                delta = getattr(event, "delta", None)
                if delta is None and isinstance(event, dict):
                    delta = event.get("delta")
                if delta:
                    yield delta
