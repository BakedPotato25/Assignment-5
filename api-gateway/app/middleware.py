import logging
import os
import threading
import time
import uuid

import requests
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse

from . import metrics

logger = logging.getLogger(__name__)

AUTH_VALIDATE_URL = os.environ.get("AUTH_VALIDATE_URL", "http://auth-service:8000/auth/validate/")

_RATE_LOCK = threading.Lock()
_RATE_BUCKETS = {}
_RATE_WINDOW_SECONDS = int(os.environ.get("GATEWAY_RATE_WINDOW_SECONDS", "60"))
_RATE_LIMIT_REQUESTS = int(os.environ.get("GATEWAY_RATE_LIMIT_REQUESTS", "120"))


class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.correlation_id = correlation_id
        response = self.get_response(request)
        response["X-Correlation-ID"] = correlation_id
        return response


class GatewayRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith("/static/") or path.startswith("/admin/") or path in ("/health/", "/metrics/"):
            return self.get_response(request)

        client_ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "unknown"))
        now = time.time()

        with _RATE_LOCK:
            bucket = _RATE_BUCKETS.get(client_ip)
            if not bucket or now - bucket["window_start"] >= _RATE_WINDOW_SECONDS:
                bucket = {"window_start": now, "count": 0}
                _RATE_BUCKETS[client_ip] = bucket
            bucket["count"] += 1
            current_count = bucket["count"]

        if current_count > _RATE_LIMIT_REQUESTS:
            metrics.record_rate_limit_blocked()
            retry_after = max(1, int(_RATE_WINDOW_SECONDS - (now - bucket["window_start"])))
            return JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "retry_after_seconds": retry_after,
                },
                status=429,
            )

        return self.get_response(request)


class GatewayAuthMiddleware:
    PROTECTED_PREFIXES = ("/cart/", "/reviews/submit/", "/staff/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith("/static/") or path.startswith("/admin/"):
            return self.get_response(request)
        if path in ("/login/", "/register/", "/logout/", "/health/", "/metrics/"):
            return self.get_response(request)

        protected = any(path.startswith(prefix) for prefix in self.PROTECTED_PREFIXES)
        if not protected:
            return self.get_response(request)

        if not request.user.is_authenticated:
            return HttpResponseRedirect("/login/")

        token = request.session.get("access_token")
        if not token:
            messages.error(request, "Phien dang nhap khong hop le hoac da het han. Vui long dang nhap lai.")
            return HttpResponseRedirect("/login/")

        try:
            resp = requests.post(
                AUTH_VALIDATE_URL,
                json={"token": token},
                headers={"X-Correlation-ID": getattr(request, "correlation_id", "")},
                timeout=5,
            )
            is_valid = resp.status_code == 200 and resp.json().get("valid")
            metrics.record_auth_validation(is_valid)
            if not is_valid:
                messages.error(request, "Phien dang nhap khong hop le hoac da het han. Vui long dang nhap lai.")
                return HttpResponseRedirect("/login/")

            payload = resp.json().get("payload", {})
            role = payload.get("role", "customer")
            request.session["auth_role"] = role
            request.auth_payload = payload

            if path.startswith("/staff/") and role not in ("staff", "admin"):
                messages.error(request, "Ban khong co quyen truy cap chuc nang nay.")
                return HttpResponseRedirect("/books/")
        except requests.exceptions.RequestException as exc:
            logger.warning("gateway auth validation failed: %s", exc)
            metrics.record_auth_validation(False)
            messages.error(request, "Dich vu xac thuc tam thoi khong kha dung.")
            return HttpResponseRedirect("/login/")

        return self.get_response(request)


class GatewayMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        metrics.record_request(request.path, response.status_code)
        return response


class GatewayRequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration_ms = int((time.time() - start) * 1000)
        correlation_id = getattr(request, "correlation_id", "")
        logger.warning(
            "GATEWAY_REQUEST method=%s path=%s status=%s duration_ms=%s correlation_id=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            correlation_id,
        )
        return response
