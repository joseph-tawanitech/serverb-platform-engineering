import subprocess

from .models import ServiceHealth


MANAGED_SERVICES = [
    "serverb-b15-ai-gateway.service",
]


def _systemctl_user_show(service: str, property_name: str) -> str:
    result = subprocess.run(
        [
            "systemctl",
            "--user",
            "show",
            service,
            f"--property={property_name}",
            "--value",
        ],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    if result.returncode != 0:
        return "unknown"

    return result.stdout.strip() or "unknown"


def collect_service_health() -> list[ServiceHealth]:
    services = []

    for service in MANAGED_SERVICES:
        pid_value = _systemctl_user_show(service, "MainPID")

        try:
            pid = int(pid_value)
        except ValueError:
            pid = 0

        services.append(
            ServiceHealth(
                name=service,
                active_state=_systemctl_user_show(service, "ActiveState"),
                sub_state=_systemctl_user_show(service, "SubState"),
                main_pid=pid,
                enabled=_systemctl_user_show(service, "UnitFileState"),
            )
        )

    return services
