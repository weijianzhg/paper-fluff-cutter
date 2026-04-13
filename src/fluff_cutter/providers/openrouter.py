"""OpenRouter provider implementation with universal PDF support."""

import json
from typing import Iterator

import httpx

from .base import BaseLLMProvider

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider with access to 300+ models and universal PDF support."""

    @property
    def default_model(self) -> str:
        return "anthropic/claude-sonnet-4-5"

    @property
    def provider_name(self) -> str:
        return "OpenRouter"

    def analyze_paper(self, pdf_base64: str, filename: str, prompt: str) -> str:
        """
        Analyze a paper using OpenRouter's universal PDF support.

        OpenRouter automatically handles PDF processing for all models:
        - Models with native PDF support receive the file directly
        - Other models receive parsed content via OpenRouter's PDF processing

        Args:
            pdf_base64: Base64-encoded PDF data.
            filename: Original filename of the PDF.
            prompt: The analysis prompt to send to the model.

        Returns:
            The model's analysis as a string.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "file",
                            "file": {
                                "filename": filename,
                                "file_data": f"data:application/pdf;base64,{pdf_base64}",
                            },
                        },
                    ],
                }
            ],
        }

        # Use a longer timeout for PDF processing
        with httpx.Client(timeout=300.0) as client:
            response = client.post(OPENROUTER_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"] or ""

    def analyze_paper_stream(self, pdf_base64: str, filename: str, prompt: str) -> Iterator[str]:
        """
        Analyze a paper and stream OpenRouter chat completion deltas.

        Args:
            pdf_base64: Base64-encoded PDF data.
            filename: Original filename of the PDF.
            prompt: The analysis prompt to send to the model.

        Yields:
            Incremental text chunks from the model response.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "file",
                            "file": {
                                "filename": filename,
                                "file_data": f"data:application/pdf;base64,{pdf_base64}",
                            },
                        },
                    ],
                }
            ],
            "stream": True,
        }

        with httpx.Client(timeout=300.0) as client:
            with client.stream(
                "POST", OPENROUTER_API_URL, headers=headers, json=payload
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line or line.startswith(":"):
                        continue
                    if not line.startswith("data:"):
                        continue

                    data_part = line[5:].strip()
                    if data_part == "[DONE]":
                        break

                    try:
                        event = json.loads(data_part)
                    except json.JSONDecodeError:
                        continue

                    if event.get("error"):
                        message = event["error"].get("message", "OpenRouter streaming error")
                        raise RuntimeError(message)

                    choices = event.get("choices") or []
                    if not choices:
                        continue

                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        yield content
