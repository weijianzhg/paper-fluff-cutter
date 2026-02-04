"""OpenRouter provider implementation with universal PDF support."""

from openrouter import OpenRouter

from .base import BaseLLMProvider


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
        with OpenRouter(api_key=self.api_key) as client:
            response = client.chat.send(
                model=self.model,
                messages=[
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
                stream=False,
            )

        return response.choices[0].message.content or ""
