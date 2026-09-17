"""
Server B B15.14 - Model Router

The Model Router selects the appropriate AI provider.
Clients do not communicate directly with providers.
"""

from fastapi import HTTPException

from .providers.ollama import OllamaProvider


class ModelRouter:
    """Controlled provider/model routing layer."""

    def __init__(self) -> None:
        self.providers = {
            "ollama": OllamaProvider(),
        }

    def route(self, model: str, messages: list[dict]) -> dict:
        """
        Route a model request to the appropriate provider.

        Current B15.14 routing:
        qwen3:* -> Ollama
        """

        if model.startswith("qwen3:"):
            provider = self.providers["ollama"]

            try:
                response = provider.chat(
                    model=model,
                    messages=messages,
                )

            except Exception as exc:
                raise HTTPException(
                    status_code=502,
                    detail=f"Ollama provider failed: {exc}",
                ) from exc

            return {
                "provider": provider.name,
                "model": model,
                "response": response,
            }

        raise HTTPException(
            status_code=400,
            detail=f"No provider route configured for model: {model}",
        )
