import os
import platform
import shutil
import subprocess
from datetime import datetime


def _read_meminfo() -> dict[str, int]:
    values = {}

    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            key, value = line.split(":", 1)
            values[key] = int(value.strip().split()[0])

    return values


def _uptime_seconds() -> float:
    with open("/proc/uptime", "r", encoding="utf-8") as f:
        return float(f.read().split()[0])


def _ntp_status() -> str:
    try:
        result = subprocess.run(
            [
                "timedatectl",
                "show",
                "--property=NTPSynchronized",
                "--value",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        return result.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def collect_system_health() -> dict:
    mem = _read_meminfo()
    disk = shutil.disk_usage("/")

    memory_total_mb = mem.get("MemTotal", 0) / 1024
    memory_available_mb = mem.get("MemAvailable", 0) / 1024
    swap_total_mb = mem.get("SwapTotal", 0) / 1024
    swap_free_mb = mem.get("SwapFree", 0) / 1024

    root_disk_used_percent = (
        ((disk.total - disk.free) / disk.total) * 100
        if disk.total
        else 0
    )

    load_1m = os.getloadavg()[0]

    return {
        "hostname": platform.node(),
        "os": platform.platform(),
        "kernel": platform.release(),
        "uptime_seconds": _uptime_seconds(),
        "load_1m": load_1m,
        "memory_total_mb": memory_total_mb,
        "memory_available_mb": memory_available_mb,
        "swap_total_mb": swap_total_mb,
        "swap_free_mb": swap_free_mb,
        "root_disk_total_gb": disk.total / (1024 ** 3),
        "root_disk_free_gb": disk.free / (1024 ** 3),
        "root_disk_used_percent": root_disk_used_percent,
        "local_time": datetime.now().astimezone().isoformat(),
        "ntp_synchronized": _ntp_status(),
    }
