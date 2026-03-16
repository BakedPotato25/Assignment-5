# TÀI LIỆU API HỆ THỐNG BOOKSTORE MICROSERVICES

Tài liệu này bao gồm danh sách các API endpoints của 12 microservices trong hệ thống BookStore, được tự động trích xuất trực tiếp từ mã nguồn `views.py` và `urls.py`.

---

## 1. API Gateway (`api-gateway` | Cổng 8000)
Đóng vai trò là cửa ngõ duy nhất (*Single Entry Point*), giao tiếp với người dùng cuối, render giao diện Bootstrap 5 và gọi các dịch vụ backend nội bộ.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **GET** | `/` hoặc `/books/` | Lấy danh sách toàn bộ sách để hiển thị ở trang chủ. | Không | Render `books.html` với danh sách sách lấy được từ `book-service`. |
| **GET**, **POST** | `/register/` | Đăng ký tài khoản người dùng mới. | `username`, `email`, `password` (Form HTTP POST) | Tạo User ở Gateway, gọi `customer-service` tạo profile và tự động tạo Giỏ hàng rỗng. Render `books.html`. |
| **GET**, **POST** | `/login/` | Đăng nhập vào hệ thống. | `username`, `password` (Form HTTP POST) | Sinh Session tạm và kiểm tra mã `customer_id` từ `customer-service`. Render `books.html`. |
| **GET** | `/logout/` | Đăng xuất người dùng. | Không | Đăng xuất phiên và chuyển hường về `/books/`. |
| **GET** | `/cart/` | Chi tiết hóa giỏ hàng hiện tại của phiên đăng nhập. | Không | Gọi `cart-service` để truy vấn số lượng, render `cart.html`. |
| **POST** | `/cart/add/` | Yêu cầu thêm một cuốn sách vào giỏ. | `book_id`, `quantity` (Form HTTP POST) | Gọi `cart-service` tạo `CartItem`. Redirect về `/books/`. |
| **POST** | `/cart/update/<item_id>/` | Cập nhật số lượng của một mặt hàng trong giỏ. | `quantity` (Form HTTP POST) | Gọi `cart-service` sửa đổi số lượng. Redirect qua `/cart/`. |
| **POST** | `/cart/checkout/` | Tiến hành thanh toán rành buộc các mặt hàng trong giỏ. | `payment_method`, `shipping_method`, `shipping_address` | Gọi `order-service` để tạo đơn. `order-service` sẽ làm nhạc trưởng tự động gọi Payment và Shipment. Redirect về `/cart/`. |
| **POST** | `/reviews/submit/` | Gửi đánh giá cho cuốn sách. | `book_id`, `rating`, `comment` (Form HTTP POST) | Chuyển tiếp payload JSON (gắn thêm `customer_id`) tới `comment-rate-service`. |
| **GET**, **POST** | `/staff/books/add/` | Nhân viên đăng một cuốn sách mới lên hệ thống. | `title`, `author`, `price`, `stock` | Gửi HTTP POST JSON trực tiếp đến `book-service`. |
| **GET**, **POST** | `/staff/books/<book_id>/edit/` | Cập nhật thông tin cuốn sách dựa trên ID. | `title`, `author`, `price`, `stock` | Gửi HTTP PUT JSON trực tiếp đến `book-service`. |
| **POST** | `/staff/books/<book_id>/delete/` | Xóa một cuốn sách trong kho nghiệp vụ. | Không | Gửi HTTP DELETE đến `book-service`. |

---

## 2. Customer Service (`customer-service` | Cổng nội bộ 8003)
Quản lý hồ sơ người dùng mua hàng.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **GET** | `/customers/` | Lấy danh sách toàn bộ hồ sơ khách hàng. | Không | Danh sách mảng JSON khách hàng hiện có. |
| **POST** | `/customers/` | Tạo hồ sơ khách hàng mới. *(Automate)* Tự động bắn request tới `cart-service/carts/` để khởi tạo giỏ hàng cho ID vừa tạo. | `{"name": "khaind", "email": "khaind@ptit.edu.vn"}` | HTTP 201 Created. Trả về thông tin khách hàng vừa phân bổ kèm `id`. HTTP 400 Bad Request nếu lỗi. |

---

## 3. Book Service (`book-service` | Cổng nội bộ 8005)
Quản lý kho sách, thông tin đầu ấn.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **GET** | `/books/` | List list toàn bộ sách trong Database sách. | Không | Mảng JSON các Object `Book`. |
| **POST** | `/books/` | Thêm ấn bản/sách mới vào kho. | `{"title": "Lập trình Python", "author": "John Doe", "price": "100000", "stock": "50"}` | HTTP 201 Created. Trả về JSON thông tin sách vừa thêm. |
| **GET** | `/books/<pk>/` | Lấy chi tiết thông tin của cuốn sách theo Primary Key. | Không | JSON chi tiết về cuốn sách. 404 nếu không tìm thấy. |
| **PUT** | `/books/<pk>/` | Chỉnh sửa một phần cấu trúc sách hiện tại. | `{"price": "120000", "stock": "45"}` | JSON thông tin sách hậu chỉnh sửa. |
| **DELETE** | `/books/<pk>/` | Tiêu hủy một cuốn sách khỏi database. | Không | HTTP 204 No Content. |

---

## 4. Cart Service (`cart-service` | Cổng nội bộ 8006)
Xử lý các giỏ hàng logic trung gian chưa quyết toán thanh toán.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **POST** | `/carts/` | Khởi tạo bảng Cart trống mới dành riêng cho `customer_id`. | `{"customer_id": 1}` | HTTP 201 Created. Rành buộc Cart rỗng JSON. |
| **GET** | `/carts/<customer_id>/` | Lấy toàn bộ hàng tồn đang nằm trong giỏ của `customer`. | Không | JSON phản ánh giỏ hàng và mảng `items` đại diện cho các mặt hàng bên trong. |
| **POST** | `/cart-items/` | Thêm vào giỏ. Điểm nhấn kiến trúc: Gọi thẳng API GET sang `book-service/books/` để xác minh ID sách này có chân thực và khả dụng hay không, tránh ngoại vi dữ liệu. | `{"customer_id": 1, "book_id": 5, "quantity": 2}` | HTTP 201 Created, hoặc HTTP 404 Not Found (sách không tồn tại bên `book-service`) / 503 (Dịch vụ sách die). |
| **PUT** | `/cart-items/<item_id>/` | Cập nhật số lượng của dòng hàng hóa. Nếu quantity <= 0 thì xóa dòng đó khỏi giỏ. | `{"quantity": 3}` | JSON dòng hàng hóa mới cập nhật, hoặc HTTP 204 No Content. |

---

## 5. Order Service (`order-service` | Cổng nội bộ 8007)
Nhạc trưởng - Orchestrator quản lý quy trình phân tán từ lúc bắt đầu tạo đơn tới thu tiền và điều xe.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **POST** | `/orders/` | Xử lý việc đặt đơn hàng tổng thể. Nhận dữ liệu Order, tự gọi Payment Service, nếu pass sẽ tiếp tục gọi Shipment Service. Fail ở khâu nào chặn lại ở khâu đó (Saga Pattern). | `{"customer_id": 1, "total_amount": 250000, "items": [{"book_id": 2, "quantity": 1}], "payment_method": "COD", "shipping_method": "Express", "shipping_address": "Dong Da, HN"}` | HTTP 201 Created nếu chuỗi Payment và Shipment thành công, cập nhật trạng thái đơn hàng là `Confirmed`. Nếu lỗi trả về lỗi (502 Gateway), kèm lý do. |

---

## 6. Payment Service (`pay-service` | Cổng nội bộ 8009)
Quản trị phương pháp thanh khoản.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **POST** | `/payments/` | Sinh Mock giao dịch (Mô phỏng VNPay/Momo). | `{"order_id": 15, "amount": "250000.00", "method": "COD"}` | HTTP 201 Created, biểu hiện Payment record đã sinh trên hệ thống. |

---

## 7. Shipment Service (`ship-service` | Cổng nội bộ 8008)
Quản trị vận đơn.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **POST** | `/shipments/` | Sinh Mock lộ trình gói hàng (Mô phỏng GHTK/AhaMove). | `{"order_id": 15, "address": "B22DCCN441, Dong Da, HN", "method": "Standard"}` | HTTP 201 Created, biểu hiện tracking record đã sinh. |

---

## 8. Comment / Rate Service (`comment-rate-service` | Cổng nội bộ 8010)
Review từ người dùng.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **GET** | `/reviews/` | Lấy Feedback. Cung cấp tham số query `?book_id=` để filter chỉ riêng theo Sách đó. | Không | Trả mảng Feedback Rate Sao. |
| **POST** | `/reviews/` | Nhận Feedback từ khách hàng ẩn danh hoặc có ID. | `{"customer_id": 1, "book_id": 5, "rating": 5, "comment": "Good"}` | HTTP 201 Created. |

---

## 9. Recommender AI Service (`recommender-ai-service` | Cổng nội bộ 8011)
AI gợi ý dựa trên hồ sơ đọc.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **GET** | `/recommendations/<customer_id>/` | Trả về thuật toán Random ngẫu nhiên 3 ID sách để hiển thị gợi ý mồi (Mock Recommendation Engine). | Không | `{"customer_id": 1, "recommended_books": [14, 2, 49]}` HTTP 200 OK. |

---

## 10. Catalog Service (`catalog-service` | Cổng nội bộ 8004)
Phân chia thể loại (Categories) định danh cho hệ thống.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **GET** | `/categories/` | Liệt kê thể loại (`Science`, `Art`, `Fiction`...). | Không | Danh mục lưu trữ cục bộ. |
| **POST** | `/categories/` | Thêm Catalog danh mục chủ mới. | `{"name": "IT Book", "description": "Tech"}` | HTTP 201 Created. |

---

## 11. Staff Service (`staff-service` | Cổng nội bộ 8001)
HRM phân hệ nhân sự thấp.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **GET** | `/staffs/` | Lấy mảng phòng ban nhân viên Staff. | Không | Danh sách NV. |
| **POST** | `/staffs/` | Định danh mới cho nhân sự vào phòng điều lệnh sách. | `{"user_id": 2, "role": "editor"}` | HTTP 201 Created. |

---

## 12. Manager Service (`manager-service` | Cổng nội bộ 8002)
BOD phân hệ cốt cán siêu quản trị.

| Method | Endpoint | Mô tả chức năng | Request Payload (Mẫu) | Response / Action |
| --- | --- | --- | --- | --- |
| **GET** | `/managers/` | Lấy danh mục C-level quan lớn. | Không | JSON |
| **POST** | `/managers/` | Thêm quan chức. | `{"user_id": 1, "department": "Executive"}` | HTTP 201 Created. |

---

*Tài liệu này được tự động gen từ phân tích mã nguồn thời gian thực bằng Antigravity. Tất cả dữ liệu ánh xạ chính xác 100% với routing của Django REST Framework và Logic tại `views.py`.*
