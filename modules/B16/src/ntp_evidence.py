import subprocess


def _run(command: list[str]) -> dict:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    return {
        "command": " ".join(command),
        "return_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def collect_ntp_evidence() -> dict:
    return {
        "timedatectl": _run(["timedatectl", "status"]),
        "chrony_tracking": _run(["chronyc", "tracking"]),
        "chrony_sources": _run(["chronyc", "sources", "-v"]),
        "chrony_sourcestats": _run(["chronyc", "sourcestats", "-v"]),
        "chrony_service": _run(
            ["systemctl", "show", "chrony", "--property=ActiveState,SubState,NRestarts"]
        ),
    }
