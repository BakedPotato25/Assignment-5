import requests
import logging

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

logger = logging.getLogger(__name__)

BOOK_SERVICE_URL     = "http://book-service:8000/books/"
CART_SERVICE_URL     = "http://cart-service:8000/carts/"
CART_ITEM_URL        = "http://cart-service:8000/cart-items/"
CUSTOMER_SERVICE_URL = "http://customer-service:8000/customers/"
ORDER_SERVICE_URL    = "http://order-service:8000/orders/"
REVIEW_SERVICE_URL   = "http://comment-rate-service:8000/reviews/"


# ──────────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────────
def _get_customer_id(request):
    cid = request.session.get("customer_id")
    if cid:
        return cid
    try:
        resp = requests.get(CUSTOMER_SERVICE_URL, timeout=5)
        resp.raise_for_status()
        for c in resp.json():
            if c.get("email") == request.user.email:
                request.session["customer_id"] = c["id"]
                return c["id"]
    except requests.exceptions.RequestException as e:
        logger.warning("customer-service unreachable: %s", e)
    return None


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
        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Ten dang nhap da ton tai."})
        if User.objects.filter(email=email).exists():
            return render(request, "register.html", {"error": "Email da duoc su dung."})
        user = User.objects.create_user(username=username, email=email, password=password)
        try:
            resp = requests.post(CUSTOMER_SERVICE_URL, json={"name": username, "email": email}, timeout=5)
            if resp.status_code == 201:
                request.session["customer_id"] = resp.json().get("id")
        except requests.exceptions.RequestException as e:
            logger.warning("Could not sync to customer-service: %s", e)
        login(request, user)
        messages.success(request, f"Chao mung {username}! Tai khoan da duoc tao thanh cong.")
        return redirect("book_list")
    return render(request, "register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("book_list")
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            _get_customer_id(request)
            messages.success(request, f"Dang nhap thanh cong! Chao {user.username}.")
            return redirect("book_list")
        return render(request, "login.html", {"error": "Sai ten dang nhap hoac mat khau."})
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Ban da dang xuat.")
    return redirect("book_list")


# ──────────────────────────────────────────────
# BOOKS
# ──────────────────────────────────────────────
def book_list(request):
    try:
        resp = requests.get(BOOK_SERVICE_URL, timeout=5)
        resp.raise_for_status()
        books = resp.json()
        print(f"[book_list] Loaded {len(books)} books.")
    except requests.exceptions.RequestException as e:
        print(f"[book_list] ERROR: {e}")
        logger.warning("book-service unreachable: %s", e)
        books = []
    return render(request, "books.html", {"books": books})


# ──────────────────────────────────────────────
# STAFF: Book management (proxies to book-service)
# ──────────────────────────────────────────────
@login_required(login_url="/login/")
def staff_add_book(request):
    if not request.user.is_staff:
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
            resp = requests.post(BOOK_SERVICE_URL, json=payload, timeout=5)
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
    if not request.user.is_staff:
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
            resp = requests.put(f"{BOOK_SERVICE_URL}{book_id}/", json=payload, timeout=5)
            if resp.status_code == 200:
                messages.success(request, "Cap nhat sach thanh cong.")
            else:
                messages.error(request, f"Loi: {resp.json()}")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"book-service khong kha dung: {e}")
        return redirect("book_list")
    # Pre-fill form with current data
    try:
        resp = requests.get(f"{BOOK_SERVICE_URL}{book_id}/", timeout=5)
        book = resp.json() if resp.status_code == 200 else {}
    except requests.exceptions.RequestException:
        book = {}
    return render(request, "staff_book_form.html", {"action": "edit", "book": book, "book_id": book_id})


@login_required(login_url="/login/")
def staff_delete_book(request, book_id):
    if not request.user.is_staff:
        messages.error(request, "Ban khong co quyen truy cap chuc nang nay.")
        return redirect("book_list")
    if request.method == "POST":
        try:
            requests.delete(f"{BOOK_SERVICE_URL}{book_id}/", timeout=5)
            messages.success(request, f"Da xoa sach #{book_id}.")
        except requests.exceptions.RequestException as e:
            messages.error(request, f"book-service khong kha dung: {e}")
    return redirect("book_list")


# ──────────────────────────────────────────────
# CART
# ──────────────────────────────────────────────
@login_required(login_url="/login/")
def view_cart(request):
    customer_id = _get_customer_id(request)
    if not customer_id:
        messages.warning(request, "Khong tim thay thong tin khach hang.")
        return render(request, "cart.html", {"items": [], "error": "Khong tim thay khach hang."})
    try:
        resp = requests.get(f"{CART_SERVICE_URL}{customer_id}/", timeout=5)
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
    if request.method != "POST":
        return redirect("book_list")
    customer_id = _get_customer_id(request)
    if not customer_id:
        messages.error(request, "Khong tim thay khach hang.")
        return redirect("book_list")
    book_id  = request.POST.get("book_id")
    quantity = request.POST.get("quantity", 1)
    try:
        resp = requests.post(
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
    if request.method != "POST":
        return redirect("view_cart")
    quantity = request.POST.get("quantity", 1)
    try:
        resp = requests.put(
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
        resp = requests.get(f"{CART_SERVICE_URL}{customer_id}/", timeout=5)
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
        resp = requests.post(
            ORDER_SERVICE_URL,
            json={
                "customer_id":      customer_id,
                "items":            items,
                "total_amount":     total,
                "payment_method":   payment_method,
                "shipping_address": f"{shipping_address} [{shipping_method}]",
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
        resp = requests.post(REVIEW_SERVICE_URL, json=payload, timeout=5)
        if resp.status_code == 201:
            messages.success(request, "Cam on ban da danh gia sach!")
        else:
            messages.error(request, f"Loi danh gia: {resp.json()}")
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Dich vu danh gia khong kha dung: {e}")
    return redirect("book_list")
