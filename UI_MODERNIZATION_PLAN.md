# UI Modernization Plan (Bookstore Microservices)

## 1. Muc tieu
- Nang cap giao dien hien dai, de dung tren desktop va mobile.
- Giu nguyen logic backend/API hien tai.
- Cai thien trai nghiem mua hang, checkout, va staff CRUD.
- Dam bao hieu nang va kha nang truy cap (a11y) o muc co ban.

## 2. Pham vi
- Service ap dung: `api-gateway` (templates, static assets, interaction).
- Khong thay doi contract API giua gateway va cac service backend.

## 3. Nguyen tac thiet ke
- Nhat quan: 1 he token mau, spacing, typography.
- De mo rong: component co the tai su dung.
- Responsive truoc: uu tien mobile first.
- Nhanh va nhe: tranh animation qua muc, toi uu tai nguyen.

## 4. Ke hoach theo phase

### Phase 1 - UI Audit va Visual Direction (0.5-1 ngay)
- [x] Kiem ke tat ca trang UI hien co trong gateway.
- [x] Ghi nhan pain points ve UX/UI (readability, spacing, hierarchy).
- [x] Chot visual direction (mau, font, card style, button style).
- [x] Chot guideline ngan cho toan bo giao dien.

Deliverables:
- [x] Tai lieu danh sach van de UI hien tai.
- [x] Moodboard + guideline nhanh.

### Phase 2 - Design System Nen Tang (1-1.5 ngay)
- [x] Dinh nghia design tokens (color, radius, spacing, shadow).
- [x] Chuan hoa typography scale va breakpoints.
- [x] Xay dung component co ban: button, input, select, card, alert, badge.
- [x] Dong bo trang thai interaction: hover, active, disabled, error.

Deliverables:
- [x] Bo CSS/utility co the tai su dung.
- [x] Quy tac responsive va naming convention.

### Phase 3 - Layout va Navigation Tong The (1 ngay)
- [x] Refactor header, nav, footer theo layout thong nhat.
- [x] Toi uu grid + container cho man hinh nho.
- [x] Cai thien hierarchy trang home/books.

Deliverables:
- [x] Shared layout cho tat ca trang gateway.

### Phase 4 - Nang cap man hinh uu tien (2-3 ngay)
- [x] Books listing: card sach ro rang, CTA manh, bo cuc de scan.
- [x] Login/Register: form gon, feedback loi ro rang.
- [x] Cart/Checkout: tong tien ro, thao tac cap nhat so luong de thay.
- [x] Staff Book CRUD: table/form gon, de thao tac.

Deliverables:
- [x] User flow mua hang va staff flow hoan chinh tren UI moi.

### Phase 5 - Motion va Feedback (0.5-1 ngay)
- [x] Them transition nhe cho thao tac chinh.
- [x] Bo sung loading/skeleton cho danh sach.
- [x] Chuan hoa toast/alert thanh cong, canh bao, loi.

Deliverables:
- [x] Cam nhan UI muot hon, khong tang do tre dang ke.

### Phase 6 - Accessibility va Hieu nang (0.5-1 ngay)
- [x] Kiem tra contrast color.
- [x] Kiem tra keyboard focus va tab order.
- [x] Toi uu CSS/asset (image, icon, font).
- [x] Smoke test mobile + desktop.

Deliverables:
- [x] Checklist a11y co ban dat yeu cau.
- [x] Chi so tai trang cai thien.

### Phase 7 - QA va Rollout (0.5 ngay)
- [x] Test hoi quy cac luong chinh (browse, login, cart, checkout, staff CRUD).
- [x] Chup before/after cho demo.
- [x] Tach pull request nho de de review/rollback.

Deliverables:
- [x] Ban UI moi on dinh, san sang demo.

## 5. Backlog uu tien theo man hinh

### P0 (lam truoc)
- [x] Books page
- [x] Login page
- [x] Register page
- [x] Cart page
- [x] Checkout flow

### P1
- [x] Staff add/edit/delete book pages
- [x] Global alerts/messages
- [x] Shared header/footer polish

### P2
- [x] Nho animation polish
- [x] Empty states + richer loading states

## 6. Tieu chi hoan thanh (Definition of Done)
- [x] UI nhat quan tren toan bo man hinh chinh.
- [x] Responsive tot tren mobile va desktop.
- [x] Khong vo luong nghiep vu chinh.
- [x] Feedback trang thai ro rang (loading/success/error).
- [x] Checklist a11y co ban duoc dap ung.

## 7. De xuat cach theo doi
- Dung checkboxes trong file nay de cap nhat tien do hang ngay.
- Moi phase xong tao 1 commit/PR rieng de de review.
- Cuoi moi phase chup screenshot before/after de doi chieu.

## 8. Kanban Mini (cap nhat nhanh hang ngay)

Huong dan su dung:
- Khi bat dau task: chuyen task tu `Todo` sang `In Progress`.
- Khi xong task: chuyen task sang `Done` va them ngay hoan thanh.
- Moi luc chi nen co 1-3 task trong `In Progress`.

### Todo
- [x] Khong con task mo.

### In Progress
- [x] Khong con task dang lam.

### Done
- [x] UI audit toan bo trang gateway. (2026-03-17)
- [x] Chot visual direction (mau, font, card/button style). (2026-03-17)
- [x] Tao design tokens + typography scale. (2026-03-17)
- [x] Refactor shared layout (header/nav/footer). (2026-03-17)
- [x] Nang cap books page. (2026-03-17)
- [x] Nang cap login/register page. (2026-03-17)
- [x] Nang cap cart/checkout page. (2026-03-17)
- [x] Nang cap staff CRUD pages. (2026-03-22)
- [x] Bo sung loading, toast, va interaction feedback. (2026-03-22)
- [x] Hoan tat smoke test responsive mobile + desktop. (2026-03-22)
- [x] Hoan tat contrast + keyboard focus + tab order co ban. (2026-03-22)
- [x] Toi uu CSS/asset va hoan tat Phase 6 (a11y + performance). (2026-03-22)
- [x] Test hoi quy luong chinh bang acceptance script. (2026-03-22)
- [x] Hoan tat ke hoach tach PR nho cho review/rollback. (2026-03-22)
- [x] Hoan tat bo screenshot before/after cho demo (desktop + mobile). (2026-03-22)
- [x] Hoan tat polish header/footer, animation nho va richer empty/loading states. (2026-03-22)
