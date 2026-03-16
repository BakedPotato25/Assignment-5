import threading
import time
from collections import Counter

_START_TS = time.time()
_LOCK = threading.Lock()

_request_total = 0
_status_counts = Counter()
_route_counts = Counter()
_rate_limit_blocked = 0
_auth_validate_total = 0
_auth_validate_success = 0
_downstream_calls = Counter()


def record_request(path, status_code):
    global _request_total
    with _LOCK:
        _request_total += 1
        _status_counts[str(status_code)] += 1
        _route_counts[path] += 1


def record_rate_limit_blocked():
    global _rate_limit_blocked
    with _LOCK:
        _rate_limit_blocked += 1


def record_auth_validation(success):
    global _auth_validate_total, _auth_validate_success
    with _LOCK:
        _auth_validate_total += 1
        if success:
            _auth_validate_success += 1


def record_downstream_call(service, method, status):
    key = f"{service}|{method.upper()}|{status}"
    with _LOCK:
        _downstream_calls[key] += 1


def snapshot():
    with _LOCK:
        return {
            "uptime_seconds": int(time.time() - _START_TS),
            "request_total": _request_total,
            "status_counts": dict(_status_counts),
            "route_counts": dict(_route_counts),
            "rate_limit_blocked": _rate_limit_blocked,
            "auth_validate_total": _auth_validate_total,
            "auth_validate_success": _auth_validate_success,
            "downstream_calls": dict(_downstream_calls),
        }


def to_prometheus():
    data = snapshot()
    lines = [
        "# HELP gateway_uptime_seconds Gateway uptime in seconds",
        "# TYPE gateway_uptime_seconds gauge",
        f"gateway_uptime_seconds {data['uptime_seconds']}",
        "# HELP gateway_requests_total Total HTTP requests received by gateway",
        "# TYPE gateway_requests_total counter",
        f"gateway_requests_total {data['request_total']}",
        "# HELP gateway_rate_limit_blocked_total Requests blocked by gateway rate limiter",
        "# TYPE gateway_rate_limit_blocked_total counter",
        f"gateway_rate_limit_blocked_total {data['rate_limit_blocked']}",
        "# HELP gateway_auth_validate_total Auth validation calls made by gateway",
        "# TYPE gateway_auth_validate_total counter",
        f"gateway_auth_validate_total {data['auth_validate_total']}",
        "# HELP gateway_auth_validate_success_total Successful auth validations",
        "# TYPE gateway_auth_validate_success_total counter",
        f"gateway_auth_validate_success_total {data['auth_validate_success']}",
    ]

    for status, value in sorted(data["status_counts"].items()):
        lines.append(f'gateway_status_total{{status="{status}"}} {value}')

    for path, value in sorted(data["route_counts"].items()):
        escaped_path = path.replace('"', '\\"')
        lines.append(f'gateway_route_total{{path="{escaped_path}"}} {value}')

    for key, value in sorted(data["downstream_calls"].items()):
        service, method, status = key.split("|", 2)
        lines.append(
            f'gateway_downstream_calls_total{{service="{service}",method="{method}",status="{status}"}} {value}'
        )

    return "\n".join(lines) + "\n"
