from pydantic import BaseModel, Field
from typing import Literal


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    model: str = Field(default="qwen3:4b", min_length=1, max_length=200)
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)


class GatewayHealth(BaseModel):
    status: str
    service: str
    version: str
    capability: str


class SystemHealth(BaseModel):
    hostname: str
    os: str
    kernel: str
    uptime_seconds: float
    load_1m: float
    memory_total_mb: float
    memory_available_mb: float
    swap_total_mb: float
    swap_free_mb: float
    root_disk_total_gb: float
    root_disk_free_gb: float
    root_disk_used_percent: float
    local_time: str
    ntp_synchronized: str


class ServiceHealth(BaseModel):
    name: str
    active_state: str
    sub_state: str
    main_pid: int
    enabled: str


class DashboardSnapshot(BaseModel):
    gateway: GatewayHealth | None = None
    system: SystemHealth
    services: list[ServiceHealth]
