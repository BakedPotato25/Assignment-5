import requests
import logging
from urllib.parse import urlparse

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from . import metrics

logger = logging.getLogger(__name__)

BOOK_SERVICE_URL     = "http://book-service:8000/books/"
CART_SERVICE_URL     = "http://cart-service:8000/carts/"
CART_ITEM_URL        = "http://cart-service:8000/cart-items/"
CUSTOMER_SERVICE_URL = "http://customer-service:8000/customers/"
ORDER_SERVICE_URL    = "http://order-service:8000/orders/"
REVIEW_SERVICE_URL   = "http://comment-rate-service:8000/reviews/"
AUTH_REGISTER_URL    = "http://auth-service:8000/auth/register/"
AUTH_LOGIN_URL       = "http://auth-service:8000/auth/login/"
AUTH_VALIDATE_URL    = "http://auth-service:8000/auth/validate/"

HEALTH_CHECK_URLS = {
    "auth-service": "http://auth-service:8000/health/",
    "order-service": "http://order-service:8000/health/",
    "pay-service": "http://pay-service:8000/health/",
    "ship-service": "http://ship-service:8000/health/",
}


def _gateway_headers(request):
    correlation_id = getattr(request, "correlation_id", None)
    if not correlation_id:
        return {}
    return {"X-Correlation-ID": correlation_id}


def _downstream_service_name(url):
    parsed = urlparse(url)
    host = parsed.netloc
    return host.split(":")[0] if host else "unknown"


def _gateway_request(request, method, url, **kwargs):
    headers = kwargs.pop("headers", {})
    merged_headers = {**headers, **_gateway_headers(request)}
    kwargs["headers"] = merged_headers

    service = _downstream_service_name(url)
    try:
        response = requests.request(method=method, url=url, **kwargs)
        metrics.record_downstream_call(service, method, response.status_code)
        return response
    except requests.exceptions.RequestException:
        metrics.record_downstream_call(service, method, "error")
        raise


def _gw_get(request, url, **kwargs):
    return _gateway_request(request, "GET", url, **kwargs)


def _gw_post(request, url, **kwargs):
    return _gateway_request(request, "POST", url, **kwargs)


def _gw_put(request, url, **kwargs):
    return _gateway_request(request, "PUT", url, **kwargs)


def _gw_delete(request, url, **kwargs):
    return _gateway_request(request, "DELETE", url, **kwargs)


def health_view(request):
    checks = {}
    overall_ok = True

    for service, url in HEALTH_CHECK_URLS.items():
        try:
            resp = _gw_get(request, url, timeout=3)
            ok = resp.status_code == 200
            checks[service] = {
                "ok": ok,
                "status_code": resp.status_code,
            }
            overall_ok = overall_ok and ok
        except requests.exceptions.RequestException as exc:
            checks[service] = {
                "ok": False,
                "error": str(exc),
            }
            overall_ok = False

    status_code = 200 if overall_ok else 503
    return JsonResponse(
        {
            "service": "api-gateway",
            "status": "ok" if overall_ok else "degraded",
            "checks": checks,
        },
        status=status_code,
    )


def metrics_view(request):
    return HttpResponse(metrics.to_prometheus(), content_type="text/plain; version=0.0.4")


# ──────────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────────
def _get_customer_id(request):
    cid = request.session.get("customer_id")
    if cid:
        return cid
    try:
        resp = _gw_get(request, CUSTOMER_SERVICE_URL, timeout=5)
        resp.raise_for_status()
        for c in resp.json():
            if c.get("email") == request.user.email:
                request.session["customer_id"] = c["id"]
                return c["id"]
    except requests.exceptions.RequestException as e:
        logger.warning("customer-service unreachable: %s", e)
    return None


def _validate_gateway_token(request):
    token = request.session.get("access_token")
    if not token:
        return False, {}
    try:
        resp = _gw_post(request, AUTH_VALIDATE_URL, json={"token": token}, timeout=5)
        if resp.status_code == 200 and resp.json().get("valid"):
            payload = resp.json().get("payload", {})
            request.session["auth_role"] = payload.get("role", "customer")
            return True, payload
    except requests.exceptions.RequestException as e:
        logger.warning("auth-service validation unavailable: %s", e)
    return False, {}


def _require_gateway_auth(request):
    ok, _ = _validate_gateway_token(request)
    if not ok:
        logout(request)
        messages.error(request, "Phien dang nhap khong hop le hoac da het han. Vui long dang nhap lai.")
        return redirect("login")
    return None


def _is_staff_role(request):
    return request.session.get("auth_role", "customer") in ("staff", "admin")


# ──────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect("book_list")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email    = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        # 1) Register account in central auth-service
        try:
            auth_resp = _gw_post(
                request,
                AUTH_REGISTER_URL,
                json={"username": username, "email": email, "password": password, "role": "customer"},
                timeout=5,
            )
            if auth_resp.status_code != 201:
                detail = auth_resp.json() if auth_resp.headers.get("content-type", "").startswith("application/json") else auth_resp.text
                return render(request, "register.html", {"error": f"Khong the tao tai khoan: {detail}"})
        except requests.exceptions.RequestException as e:
            return render(request, "register.html", {"error": f"auth-service khong kha dung: {e}"})

        # 2) Sync customer profile for shopping domain
        try:
            resp = _gw_post(request, CUSTOMER_SERVICE_URL, json={"name": username, "email": email}, timeout=5)
            if resp.status_code == 201:
                request.session["customer_id"] = resp.json().get("id")
        except requests.exceptions.RequestException as e:
            logger.warning("Could not sync to customer-service: %s", e)

        # 3) Auto-login via auth-service token and bridge to local Django session
        try:
            login_resp = _gw_post(
                request,
                AUTH_LOGIN_URL,
                json={"username": username, "password": password},
                timeout=5,
            )
            if login_resp.status_code == 200:
                data = login_resp.json()
                role = data.get("role", "customer")
                user, _ = User.objects.get_or_create(username=username, defaults={"email": email})
                if email and user.email != email:
                    user.email = email
                user.is_staff = role in ("staff", "admin")
                user.set_unusable_password()
                user.save()
                user.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, user)
                request.session["access_token"] = data.get("access_token")
                request.session["auth_role"] = role
        except requests.exceptions.RequestException as e:
            logger.warning("Could not auto-login from auth-service: %s", e)

        messages.success(request, f"Chao mung {username}! Tai khoan da duoc tao thanh cong.")
        return redirect("book_list")
    return render(request, "register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("book_list")
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        try:
            auth_resp = _gw_post(
                request,
                AUTH_LOGIN_URL,
                json={"username": username, "password": password},
                timeout=5,
            )
        except requests.exceptions.RequestException as e:
            return render(request, "login.html", {"error": f"auth-service khong kha dung: {e}"})

        if auth_resp.status_code == 200:
            data = auth_resp.json()
            email = data.get("email", "")
            role = data.get("role", "customer")

            user, created = User.objects.get_or_create(username=username, defaults={"email": email})
            changed = False
            if email and user.email != email:
                user.email = email
                changed = True

            should_staff = role in ("staff", "admin")
            if user.is_staff != should_staff:
                user.is_staff = should_staff
                changed = True

            if created:
                user.set_unusable_password()
                changed = True

            if changed:
                user.save()

            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
            request.session["access_token"] = data.get("access_token")
            request.session["auth_role"] = role
            _get_customer_id(request)
            messages.success(request, f"Dang nhap thanh cong! Chao {user.username}.")
            return redirect("book_list")

        if auth_resp.status_code == 401:
            return render(request, "login.html", {"error": "Sai ten dang nhap hoac mat khau."})

        detail = auth_resp.json() if auth_resp.headers.get("content-type", "").startswith("application/json") else auth_resp.text
        return render(request, "login.html", {"error": f"Khong the dang nhap: {detail}"})
    return render(request, "login.html")


def logout_view(request):
    request.session.pop("access_token", None)
    request.session.pop("auth_role", None)
    logout(request)
    messages.info(request, "Ban da dang xuat.")
    return redirect("book_list")


# ──────────────────────────────────────────────
# BOOKS
# ──────────────────────────────────────────────
def book_list(request):
    try:
        resp = _gw_get(request, BOOK_SERVICE_URL, timeout=5)
        resp.raise_for_status()
        books = resp.json()
        print(f"[book_list] Loaded {len(books)} books.")
    except requests.exceptions.RequestException as e:
        print(f"[book_list] ERROR: {e}")
        logger.warning("book-service unreachable: %s", e)
        books = []
    return render(request, "books.html", {"books": books})


@login_required(login_url="/login/")
def staff_books(request):
    auth_redirect = _require_gateway_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _is_staff_role(request):
        messages.error(request, "Ban khong co quyen truy cap chuc nang nay.")
        return redirect("book_list")

    try:
        resp = _gw_get(request, BOOK_SERVICE_URL, timeout=5)
        resp.raise_for_status()
        books = resp.json()
    except requests.exceptions.RequestException as e:
        logger.warning("book-service unreachable for staff_books: %s", e)
        books = []
        messages.error(request, "Khong the tai danh sach sach tu book-service.")

    return render(request, "staff_books.html", {"books": books})


# ──────────────────────────────────────────────
# STAFF: Book management (proxies to book-service)
# ──────────────────────────────────────────────
@login_required(login_url="/login/")
def staff_add_book(request):
    auth_redirect = _require_gateway_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _is_staff_role(request):
        messages.error(request, "Ban khong co quyen truy cap chuc nang nay.")
        return redirect("book_list")
    if request.method == "POST":
        payload = {
            "title":  request.POST.get("title", "").strip(),
            "author": request.POST.get("author", "").strip(),
            "price":  request.POST.get("price", 0),
            "stock":  request.POST.get("stock", 0),
        }
        try:
            resp = _gw_post(request, BOOK_SERVICE_URL, json=payload, timeout=5)
            if resp.status_code == 201:
                messages.success(request, f"Da them sach: {payload['title']}")
            else:
                messages.error(request, f"Loi: {resp.json()}")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"book-service khong kha dung: {e}")
        return redirect("book_list")
    return render(request, "staff_book_form.html", {"action": "add"})


@login_required(login_url="/login/")
def staff_edit_book(request, book_id):
    auth_redirect = _require_gateway_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _is_staff_role(request):
        messages.error(request, "Ban khong co quyen truy cap chuc nang nay.")
        return redirect("book_list")
    if request.method == "POST":
        payload = {
            "title":  request.POST.get("title", "").strip(),
            "author": request.POST.get("author", "").strip(),
            "price":  request.POST.get("price", 0),
            "stock":  request.POST.get("stock", 0),
        }
        try:
            resp = _gw_put(request, f"{BOOK_SERVICE_URL}{book_id}/", json=payload, timeout=5)
            if resp.status_code == 200:
                messages.success(request, "Cap nhat sach thanh cong.")
            else:
                messages.error(request, f"Loi: {resp.json()}")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"book-service khong kha dung: {e}")
        return redirect("book_list")
    # Pre-fill form with current data
    try:
        resp = _gw_get(request, f"{BOOK_SERVICE_URL}{book_id}/", timeout=5)
        book = resp.json() if resp.status_code == 200 else {}
    except requests.exceptions.RequestException:
        book = {}
    return render(request, "staff_book_form.html", {"action": "edit", "book": book, "book_id": book_id})


@login_required(login_url="/login/")
def staff_delete_book(request, book_id):
    auth_redirect = _require_gateway_auth(request)
    if auth_redirect:
        return auth_redirect
    if not _is_staff_role(request):
        messages.error(request, "Ban khong co quyen truy cap chuc nang nay.")
        return redirect("book_list")
    if request.method == "POST":
        try:
            _gw_delete(request, f"{BOOK_SERVICE_URL}{book_id}/", timeout=5)
            messages.success(request, f"Da xoa sach #{book_id}.")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"book-service khong kha dung: {e}")
    return redirect("book_list")


# ──────────────────────────────────────────────
# CART
# ──────────────────────────────────────────────
@login_required(login_url="/login/")
def view_cart(request):
    auth_redirect = _require_gateway_auth(request)
    if auth_redirect:
        return auth_redirect
    customer_id = _get_customer_id(request)
    if not customer_id:
        messages.warning(request, "Khong tim thay thong tin khach hang.")
        return render(request, "cart.html", {"items": [], "error": "Khong tim thay khach hang."})
    try:
        resp = _gw_get(request, f"{CART_SERVICE_URL}{customer_id}/", timeout=5)
        resp.raise_for_status()
        cart  = resp.json()
        items = cart.get("items", [])
        error = None
    except requests.exceptions.HTTPError as e:
        items = []
        error = "Gio hang chua duoc khoi tao." if e.response.status_code == 404 else "Loi dich vu gio hang."
    except requests.exceptions.RequestException as e:
        logger.warning("cart-service unreachable: %s", e)
        items = []
        error = "Dich vu gio hang khong kha dung."
    return render(request, "cart.html", {"items": items, "error": error, "customer_id": customer_id})


@login_required(login_url="/login/")
def add_to_cart(request):
    auth_redirect = _require_gateway_auth(request)
    if auth_redirect:
        return auth_redirect
    if request.method != "POST":
        return redirect("book_list")
    customer_id = _get_customer_id(request)
    if not customer_id:
        messages.error(request, "Khong tim thay khach hang.")
        return redirect("book_list")
    book_id  = request.POST.get("book_id")
    quantity = request.POST.get("quantity", 1)
    try:
        resp = _gw_post(
            request,
            CART_ITEM_URL,
            json={"customer_id": customer_id, "book_id": int(book_id), "quantity": int(quantity)},
            timeout=5,
        )
        if resp.status_code == 201:
            messages.success(request, "Da them sach vao gio hang!")
        elif resp.status_code == 404:
            messages.error(request, "Sach khong ton tai trong he thong.")
        else:
            messages.warning(request, "Co loi khi them vao gio hang.")
    except requests.exceptions.RequestException as e:
        logger.error("cart-service error: %s", e)
        messages.error(request, "Dich vu gio hang khong kha dung.")
    return redirect("book_list")


@login_required(login_url="/login/")
def update_cart_item(request, item_id):
    """PUT /cart/update/<item_id>/ — Update quantity of a cart item."""
    auth_redirect = _require_gateway_auth(request)
    if auth_redirect:
        return auth_redirect
    if request.method != "POST":
        return redirect("view_cart")
    quantity = request.POST.get("quantity", 1)
    try:
        resp = _gw_put(
            request,
            f"{CART_ITEM_URL}{item_id}/",
            json={"quantity": int(quantity)},
            timeout=5,
        )
        if resp.status_code in (200, 204):
            messages.success(request, "Cap nhat so luong thanh cong.")
        else:
            messages.error(request, "Khong the cap nhat.")
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Loi dich vu: {e}")
    return redirect("view_cart")


# ──────────────────────────────────────────────
# CHECKOUT — user selects payment & shipping
# ──────────────────────────────────────────────
@login_required(login_url="/login/")
def checkout(request):
    auth_redirect = _require_gateway_auth(request)
    if auth_redirect:
        return auth_redirect
    if request.method != "POST":
        return redirect("view_cart")
    customer_id      = _get_customer_id(request)
    payment_method   = request.POST.get("payment_method", "COD")
    shipping_method  = request.POST.get("shipping_method", "Standard")
    shipping_address = request.POST.get("shipping_address", "").strip() or f"{request.user.email} — Ha Noi"
    if not customer_id:
        messages.error(request, "Khong tim thay khach hang.")
        return redirect("view_cart")
    try:
        resp = _gw_get(request, f"{CART_SERVICE_URL}{customer_id}/", timeout=5)
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except requests.exceptions.RequestException:
        messages.error(request, "Khong the lay thong tin gio hang.")
        return redirect("view_cart")
    if not items:
        messages.warning(request, "Gio hang trong, khong the thanh toan.")
        return redirect("view_cart")
    total = sum(item.get("quantity", 1) * 100000 for item in items)
    try:
        resp = _gw_post(
            request,
            ORDER_SERVICE_URL,
            json={
                "customer_id":      customer_id,
                "items":            items,
                "total_amount":     total,
                "payment_method":   payment_method,
                "shipping_method":  shipping_method,
                "shipping_address": shipping_address,
            },
            timeout=10,
        )
        if resp.status_code == 201:
            order = resp.json()
            messages.success(request, f"Dat hang thanh cong! Don #{order.get('id')} | TT: {payment_method} | Ship: {shipping_method}")
        else:
            messages.error(request, f"Dat hang that bai: {resp.json().get('error', 'Unknown')}")
    except requests.exceptions.RequestException as e:
        logger.error("order-service error: %s", e)
        messages.error(request, "Dich vu dat hang khong kha dung.")
    return redirect("view_cart")


# ──────────────────────────────────────────────
# REVIEWS — customer rates a book
# ──────────────────────────────────────────────
@login_required(login_url="/login/")
def submit_review(request):
    auth_redirect = _require_gateway_auth(request)
    if auth_redirect:
        return auth_redirect
    if request.method != "POST":
        return redirect("book_list")
    customer_id = _get_customer_id(request)
    if not customer_id:
        messages.error(request, "Khong tim thay khach hang.")
        return redirect("book_list")
    payload = {
        "customer_id": customer_id,
        "book_id":     request.POST.get("book_id"),
        "rating":      int(request.POST.get("rating", 5)),
        "comment":     request.POST.get("comment", "").strip(),
    }
    try:
        resp = _gw_post(request, REVIEW_SERVICE_URL, json=payload, timeout=5)
        if resp.status_code == 201:
            messages.success(request, "Cam on ban da danh gia sach!")
        else:
            messages.error(request, f"Loi danh gia: {resp.json()}")
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Dich vu danh gia khong kha dung: {e}")
    return redirect("book_list")
