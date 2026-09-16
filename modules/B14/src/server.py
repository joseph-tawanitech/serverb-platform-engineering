"""
Server B B14 - MCP Controlled Evidence Retrieval

B14.3.1
Read-only system status evidence.

Security boundary:
- Read-only
- No arbitrary shell execution
- No remediation
- No privileged operations
"""

import platform
import socket

from mcp.server import MCPServer

mcp = MCPServer("server-b-evidence")


@mcp.tool()
def get_system_status() -> dict:
    """
    Return basic, non-sensitive Server B system status.

    This is a read-only evidence tool.
    """

    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "mcp_service": "server-b-evidence",
        "capability": "read-only system evidence",
    }


if __name__ == "__main__":
    mcp.run()
