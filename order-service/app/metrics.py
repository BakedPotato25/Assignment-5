import threading
import time

_START_TS = time.time()
_LOCK = threading.Lock()
_METRICS = {
    "order_create_total": 0,
    "order_create_success_total": 0,
    "order_payment_failed_total": 0,
    "order_shipping_failed_total": 0,
    "order_compensated_total": 0,
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
        "# HELP order_service_uptime_seconds Order-service uptime",
        "# TYPE order_service_uptime_seconds gauge",
        f"order_service_uptime_seconds {data['uptime_seconds']}",
    ]
    for key, value in data.items():
        if key == "uptime_seconds":
            continue
        lines.append(f"{key} {value}")
    return "\n".join(lines) + "\n"
