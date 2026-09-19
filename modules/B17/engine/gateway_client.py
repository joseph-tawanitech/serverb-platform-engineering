from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class GatewayError(RuntimeError):
    """Raised when the B15 AI Gateway request fails."""


class B15GatewayClient:
    """
    Read-only client for the existing Server B B15 AI Gateway.

    B17 uses the gateway for AI inference only.
    The gateway does not grant execution authority.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8081",
        timeout: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        return self._request(
            method="GET",
            path="/health",
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "qwen3:4b",
        profile: str = "default",
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "profile": profile,
        }

        return self._request(
            method="POST",
            path="/v1/chat",
            payload=payload,
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        url = f"{self.base_url}{path}"

        data = None
        headers = {
            "Accept": "application/json",
        }

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw)

        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GatewayError(
                f"Gateway HTTP {exc.code}: {body}"
            ) from exc

        except urllib.error.URLError as exc:
            raise GatewayError(
                f"Unable to reach B15 AI Gateway at {url}: {exc}"
            ) from exc

        except json.JSONDecodeError as exc:
            raise GatewayError(
                f"Gateway returned invalid JSON from {url}"
            ) from exc
