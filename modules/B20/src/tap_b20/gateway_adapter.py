"""B20.5 adapter for the existing TAP B15 AI Gateway."""

from __future__ import annotations

from typing import Any
from urllib import error, request
import json


class SecurityGatewayError(RuntimeError):
    """Raised when the B15 AI Gateway cannot serve a request."""


class SecurityGatewayClient:
    """Provider-neutral B20 client for controlled AI inference."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8081",
        timeout: int = 150,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def investigate(
        self,
        prompt: str,
        *,
        model: str = "qwen3:4b",
    ) -> dict[str, Any]:
        """Send a governed investigation request through B15."""

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "profile": "investigation_json",
        }

        return self._post("/v1/chat", payload)

    def _post(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform a controlled JSON POST request."""

        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")

        req = request.Request(
            url,
            data=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(
                    response.read().decode("utf-8")
                )

        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SecurityGatewayError(
                f"B15 Gateway HTTP {exc.code}: {body}"
            ) from exc

        except error.URLError as exc:
            raise SecurityGatewayError(
                f"Unable to reach B15 Gateway at {url}: {exc}"
            ) from exc

        except json.JSONDecodeError as exc:
            raise SecurityGatewayError(
                f"B15 Gateway returned invalid JSON from {url}"
            ) from exc
