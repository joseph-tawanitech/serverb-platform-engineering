const $ = (id) => document.getElementById(id);

function setNotice(message) {
    $("global-status").textContent = message;
}

function formatUptime(seconds) {
    const total = Math.floor(seconds);
    const days = Math.floor(total / 86400);
    const hours = Math.floor((total % 86400) / 3600);
    const minutes = Math.floor((total % 3600) / 60);

    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    }

    return `${hours}h ${minutes}m`;
}

function stateClass(state) {
    if (state === "active" || state === "running") {
        return "state-ok";
    }

    if (state === "inactive" || state === "deactivating") {
        return "state-warning";
    }

    return "state-error";
}

async function getJson(url, options = {}) {
    const response = await fetch(url, options);

    if (!response.ok) {
        let detail = `HTTP ${response.status}`;

        try {
            const body = await response.json();
            detail = body.detail || detail;
        } catch (_) {
            // Keep the HTTP status when the response is not JSON.
        }

        throw new Error(detail);
    }

    return response.json();
}

async function refreshDashboard() {
    const button = $("refresh-button");

    button.disabled = true;
    setNotice("Refreshing...");

    try {
        const snapshot = await getJson("/api/snapshot");

        const gateway = snapshot.gateway;
        const system = snapshot.system;
        const services = snapshot.services || [];

        if (gateway) {
            $("gateway-status").textContent = gateway.status.toUpperCase();
            $("gateway-detail").textContent =
                `${gateway.service} · ${gateway.version}`;
        } else {
            $("gateway-status").textContent = "UNAVAILABLE";
            $("gateway-detail").textContent = "B15 Gateway not reachable";
        }

        $("host-name").textContent = system.hostname;
        $("host-detail").textContent = system.kernel;

        $("memory-value").textContent =
            `${system.memory_available_mb.toFixed(0)} MB`;
        $("memory-detail").textContent =
            `of ${system.memory_total_mb.toFixed(0)} MB available`;

        $("disk-value").textContent =
            `${system.root_disk_used_percent.toFixed(1)}%`;
        $("disk-detail").textContent =
            `${system.root_disk_free_gb.toFixed(1)} GB free`;

        $("system-hostname").textContent = system.hostname;
        $("system-uptime").textContent = formatUptime(system.uptime_seconds);
        $("system-load").textContent = system.load_1m.toFixed(2);
        $("system-ntp").textContent = system.ntp_synchronized;
        $("system-kernel").textContent = system.kernel;
        $("system-time").textContent = system.local_time;

        const servicesList = $("services-list");
        servicesList.innerHTML = "";

        for (const service of services) {
            const row = document.createElement("div");
            row.className = "service-row";

            const left = document.createElement("div");

            const name = document.createElement("div");
            name.className = "service-name";
            name.textContent = service.name;

            const meta = document.createElement("div");
            meta.className = "service-meta";
            meta.textContent =
                `PID ${service.main_pid} · ${service.enabled}`;

            left.appendChild(name);
            left.appendChild(meta);

            const state = document.createElement("div");
            state.className =
                `service-state ${stateClass(service.active_state)}`;
            state.textContent =
                `${service.active_state} / ${service.sub_state}`;

            row.appendChild(left);
            row.appendChild(state);
            servicesList.appendChild(row);
        }

        $("last-refresh").textContent =
            `Last refresh: ${new Date().toLocaleString()}`;

        setNotice("Refresh complete");
    } catch (error) {
        setNotice(`Refresh failed: ${error.message}`);
    } finally {
        button.disabled = false;
    }
}

async function submitChat(event) {
    event.preventDefault();

    const button = $("chat-button");
    const status = $("chat-status");
    const responseBox = $("chat-response");
    const prompt = $("prompt").value.trim();
    const model = $("model").value;

    if (!prompt) {
        status.textContent = "Enter an investigation request.";
        return;
    }

    button.disabled = true;
    status.textContent = "Investigating...";
    responseBox.classList.add("hidden");

    try {
        const result = await getJson("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                model,
                messages: [
                    {
                        role: "user",
                        content: prompt,
                    },
                ],
            }),
        });

        $("response-provider").textContent =
            `Provider: ${result.provider}`;
        $("response-model").textContent =
            `Model: ${result.model}`;
        $("response-state").textContent =
            `Status: ${result.status}`;
        $("response-text").textContent =
            result.response || "No response content returned.";

        responseBox.classList.remove("hidden");
        status.textContent = "Investigation complete.";
    } catch (error) {
        status.textContent = `Investigation failed: ${error.message}`;
    } finally {
        button.disabled = false;
    }
}

$("refresh-button").addEventListener("click", refreshDashboard);
$("chat-form").addEventListener("submit", submitChat);

refreshDashboard();
setInterval(refreshDashboard, 30000);
