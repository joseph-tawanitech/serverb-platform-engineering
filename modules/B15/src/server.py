"""
Server B B15 - AI Gateway / Model Router

B15.14
Model routing architecture.

Security boundary:
- Gateway only
- No unrestricted shell execution
- No direct infrastructure modification
- Clients communicate through the controlled Gateway API
- Model providers are accessed through the Model Router
"""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .router import ModelRouter


app = FastAPI(
    title="Server B AI Gateway",
    version="0.1.0",
)


router = ModelRouter()

# B15.15 Basic AI Guardrail:
# Only explicitly approved models may reach the Model Router.
ALLOWED_MODELS = {
    "qwen3:4b",
}


class ChatMessage(BaseModel):
    """A single message in a controlled AI conversation."""

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=32000)


ResponseProfile = Literal["default", "investigation_json"]


class ChatRequest(BaseModel):
    """Controlled client request to the AI Gateway."""

    model: str = Field(default="qwen3:4b", min_length=1, max_length=200)
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)
    profile: ResponseProfile = "default"


class ChatResponse(BaseModel):
    """Controlled response returned by the AI Gateway."""

    provider: str
    model: str
    response: str
    status: Literal["ok"]


@app.get("/health")
def health() -> dict:
    """Return basic gateway health information."""

    return {
        "status": "ok",
        "service": "server-b-ai-gateway",
        "version": "0.1.0",
        "capability": "gateway + model routing",
    }


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Receive a controlled client request and send it
    through the Model Router.
    """

    if request.model not in ALLOWED_MODELS:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail=f"Model not authorized: {request.model}",
        )

    result = router.route(
        model=request.model,
        messages=[
            {
                "role": message.role,
                "content": message.content,
            }
            for message in request.messages
        ],
        profile=request.profile,
    )

    return ChatResponse(
        provider=result["provider"],
        model=result["model"],
        response=result["response"],
        status="ok",
    )
