import httpx

from .models import ChatRequest, GatewayHealth


class GatewayClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8081"):
        self.base_url = base_url.rstrip("/")

    async def health(self) -> GatewayHealth:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return GatewayHealth.model_validate(response.json())

    async def chat(self, request: ChatRequest) -> dict:
        async with httpx.AsyncClient(timeout=125.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat",
                json=request.model_dump(),
            )
            response.raise_for_status()
            return response.json()
