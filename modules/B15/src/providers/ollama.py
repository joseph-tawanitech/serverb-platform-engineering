"""
Server B B15.14 - Ollama Provider

Responsible only for communication with the local Ollama API.
The Model Router decides when this provider is used.
"""

import os

import httpx


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434",
)


class OllamaProvider:
    """Controlled provider interface for Ollama."""

    name = "ollama"

    def chat(self, model: str, messages: list[dict]) -> str:
        """Send a chat request to Ollama and return the model response."""

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "num_predict": 80,
            },
        }

        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()

        result = response.json()

        return result.get("message", {}).get("content", "")
