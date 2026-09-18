from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .gateway_client import GatewayClient
from .models import ChatRequest, DashboardSnapshot
from .ntp_evidence import collect_ntp_evidence
from .evidence_context import build_ntp_evidence_context
from .services import collect_service_health
from .system_health import collect_system_health


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Server B B16 AI-SRE Operations Console",
    version="0.1.0",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")

gateway = GatewayClient()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
    )


@app.get("/api/health")
async def api_health():
    try:
        return await gateway.health()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"B15 AI Gateway unavailable: {exc}",
        ) from exc


@app.get("/api/system")
async def api_system():
    return collect_system_health()


@app.get("/api/services")
async def api_services():
    return collect_service_health()


@app.get("/api/evidence/ntp")
async def api_ntp_evidence():
    return collect_ntp_evidence()


@app.get("/api/snapshot", response_model=DashboardSnapshot)
async def api_snapshot():
    system = collect_system_health()
    services = collect_service_health()

    try:
        gateway_health = await gateway.health()
    except Exception:
        gateway_health = None

    return DashboardSnapshot(
        gateway=gateway_health,
        system=system,
        services=services,
    )


@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    try:
        evidence_context = build_ntp_evidence_context()

        investigation_messages = [
            {
                "role": "system",
                "content": (
                    "You are the Server B AI-SRE investigation assistant. "
                    "Analyze the supplied infrastructure evidence. "
                    "Distinguish observed facts, potential risks, and recommendations. "
                    "Do not claim that any remediation was performed. "
                    "Do not execute or authorize changes."
                ),
            },
            {
                "role": "system",
                "content": evidence_context,
            },
            *[message.model_dump() for message in request.messages],
        ]

        investigation_request = request.model_copy(
            update={"messages": investigation_messages}
        )

        return await gateway.chat(investigation_request)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"B15 AI Gateway request failed: {exc}",
        ) from exc
