"""OpenRouter provider implementation with universal PDF support."""

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
