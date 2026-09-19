"""
Server B B15.14 - Ollama Provider

Responsible only for communication with the local Ollama API.
The Model Router decides when this provider is used.
"""

import os
from typing import Literal

import httpx


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434",
)


ResponseProfile = Literal["default", "investigation_json"]


class OllamaProvider:
    """Controlled provider interface for Ollama."""

    name = "ollama"

    def chat(
        self,
        model: str,
        messages: list[dict],
        profile: ResponseProfile = "default",
    ) -> str:
        """Send a chat request to Ollama and return the model response."""

        if profile == "default":
            num_predict = 80
            output_format = None
        elif profile == "investigation_json":
            num_predict = 512
            output_format = "json"
        else:
            raise ValueError(f"Unsupported Ollama response profile: {profile}")

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "num_predict": num_predict,
            },
        }

        if output_format is not None:
            payload["format"] = output_format

        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=150.0,
        )
        response.raise_for_status()

        result = response.json()

        return result.get("message", {}).get("content", "")
