import threading
import time

_START_TS = time.time()
_LOCK = threading.Lock()
_METRICS = {
    "payment_process_total": 0,
    "payment_process_success_total": 0,
    "payment_compensate_total": 0,
    "payment_refunded_total": 0,
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
        "# HELP pay_service_uptime_seconds Pay-service uptime",
        "# TYPE pay_service_uptime_seconds gauge",
        f"pay_service_uptime_seconds {data['uptime_seconds']}",
    ]
    for key, value in data.items():
        if key == "uptime_seconds":
            continue
        lines.append(f"{key} {value}")
    return "\n".join(lines) + "\n"
