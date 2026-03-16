import threading
import time

_START_TS = time.time()
_LOCK = threading.Lock()
_METRICS = {
    "shipment_create_total": 0,
    "shipment_create_success_total": 0,
    "shipment_create_failed_total": 0,
}


def increment(key):
    with _LOCK:
        _METRICS[key] = _METRICS.get(key, 0) + 1


def snapshot():
    with _LOCK:
        data = dict(_METRICS)
    data["uptime_seconds"] = int(time.time() - _START_TS)
    return data


def to_prometheus():
    data = snapshot()
    lines = [
        "# HELP ship_service_uptime_seconds Ship-service uptime",
        "# TYPE ship_service_uptime_seconds gauge",
        f"ship_service_uptime_seconds {data['uptime_seconds']}",
    ]
    for key, value in data.items():
        if key == "uptime_seconds":
            continue
        lines.append(f"{key} {value}")
    return "\n".join(lines) + "\n"
