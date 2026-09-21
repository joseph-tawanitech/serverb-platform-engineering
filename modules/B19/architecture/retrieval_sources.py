from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RetrievalSourceType(str, Enum):
    KUBERNETES = "kubernetes"
    PROMETHEUS = "prometheus"
    LOGS = "logs"
    OTEL = "otel"
    NETWORK = "network"
    SECURITY = "security"
    TERRAFORM = "terraform"
    ANSIBLE = "ansible"
    INCIDENT = "incident"
    RCA = "rca"
    DATABASE = "database"
    ITSM = "itsm"
    CMDB = "cmdb"
    GIT = "git"
    CLOUD = "cloud"
    STORAGE = "storage"
    WEBSITE = "website"
    BUSINESS_SYSTEM = "business_system"
    CCTV = "cctv"
    OTHER = "other"


class RetrievalInterface(str, Enum):
    MCP = "mcp"
    API = "api"
    CONNECTOR = "connector"
    FILE = "file"
    DATABASE = "database"
    OTHER = "other"


@dataclass(frozen=True)
class RetrievalSource:
    """
    B19.2 controlled retrieval source definition.

    Describes where RAG may retrieve information from and
    which controlled interface may provide that information.

    This object defines architecture only. It does not provide
    execution authority to RAG, AI models, or agents.
    """

    name: str
    source_type: RetrievalSourceType
    interface: RetrievalInterface
    description: str
    enabled: bool = True

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be empty")

        if not isinstance(self.source_type, RetrievalSourceType):
            raise ValueError(
                "source_type must be a RetrievalSourceType"
            )

        if not isinstance(self.interface, RetrievalInterface):
            raise ValueError(
                "interface must be a RetrievalInterface"
            )

        if not self.description.strip():
            raise ValueError("description must not be empty")
