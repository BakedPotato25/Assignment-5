# 📚 Bookstore Microservices

A Django-based bookstore application built with a microservices architecture. Each service runs independently in Docker with its own SQLite database and communicates internally via REST APIs on port 8000.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     User (Browser)                              │
│                   localhost:8000                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                 ┌────────▼────────┐
                 │   api-gateway   │  ← Frontend (Bootstrap 5)
                 │   port: 8000    │     Login / Register / Cart
                 └────────┬────────┘
                          │ HTTP (internal :8000)
     ┌────────────────────┼─────────────────────┐
     │           │        │        │             │
┌────▼───┐ ┌────▼───┐ ┌──▼─────┐ ┌▼───────┐ ┌──▼──────────┐
│customer│ │  book  │ │  cart  │ │ order  │ │  pay/ship   │
│ :8003  │ │  :8005 │ │  :8006 │ │  :8007 │ │ :8009/:8008 │
└────────┘ └────────┘ └────────┘ └────────┘ └─────────────┘
```

---

## 🔧 Services

| Service | Host Port | Description |
|---|---|---|
| **api-gateway** | 8000 | Frontend web app (Bootstrap 5, Auth, Admin) |
| **staff-service** | 8001 | Staff management CRUD |
| **manager-service** | 8002 | Manager management CRUD |
| **customer-service** | 8003 | Customer registration (auto-creates cart) |
| **catalog-service** | 8004 | Book category management |
| **book-service** | 8005 | Book inventory (CRUD + Admin panel) |
| **cart-service** | 8006 | Shopping cart (add, update, view) |
| **order-service** | 8007 | Order processing (triggers pay + ship) |
| **ship-service** | 8008 | Shipment creation |
| **pay-service** | 8009 | Payment processing |
| **comment-rate-service** | 8010 | Book reviews and ratings |
| **recommender-ai-service** | 8011 | Book recommendations |

---

## 🚀 Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Step 1 — Clone and start

```bash
cd bookstore-microservice
docker-compose up -d --build
```

### Step 2 — Initialize databases (first time only)

```bash
# api-gateway (auth tables)
docker-compose exec api-gateway python manage.py migrate
docker-compose exec api-gateway python manage.py createsuperuser

# book-service
docker-compose exec book-service python manage.py makemigrations app
docker-compose exec book-service python manage.py migrate
docker-compose exec book-service python manage.py seed_books

# customer-service
docker-compose exec customer-service python manage.py makemigrations app
docker-compose exec customer-service python manage.py migrate
docker-compose exec customer-service python manage.py seed_customers

# remaining services
docker-compose exec cart-service python manage.py makemigrations app && docker-compose exec cart-service python manage.py migrate
docker-compose exec order-service python manage.py makemigrations app && docker-compose exec order-service python manage.py migrate
docker-compose exec pay-service python manage.py makemigrations app && docker-compose exec pay-service python manage.py migrate
docker-compose exec ship-service python manage.py makemigrations app && docker-compose exec ship-service python manage.py migrate
docker-compose exec staff-service python manage.py makemigrations app && docker-compose exec staff-service python manage.py migrate
docker-compose exec manager-service python manage.py makemigrations app && docker-compose exec manager-service python manage.py migrate
docker-compose exec catalog-service python manage.py makemigrations app && docker-compose exec catalog-service python manage.py migrate
docker-compose exec comment-rate-service python manage.py makemigrations app && docker-compose exec comment-rate-service python manage.py migrate
```

### Step 3 — Open in browser

| URL | Page |
|---|---|
| http://localhost:8000 | Home — Book list |
| http://localhost:8000/register/ | Register new account |
| http://localhost:8000/login/ | Login |
| http://localhost:8000/cart/ | Shopping cart |
| http://localhost:8000/admin/ | Django Admin (api-gateway) |
| http://localhost:8005/admin/ | Django Admin (book-service) |

---

## 🔄 Daily Workflow

### Starting the app (after shutdown)
```bash
docker-compose up -d
```
> No rebuild needed. Existing databases are preserved.

### Stopping the app
```bash
docker-compose down
```

### Full reset (clears all data)
```bash
docker-compose down -v
# Then repeat Step 2 above
```

---

## ✏️ Making Code Changes

| What you changed | What to do |
|---|---|
| `views.py`, `urls.py`, `templates/`, `serializers.py` | **Nothing** — Django auto-reloads |
| `models.py` | Rebuild + migrate (see below) |
| `Dockerfile`, `settings.py` | Rebuild the service |

**Rebuild a single service after model changes:**
```bash
docker-compose up -d --build <service-name>
docker-compose exec <service-name> python manage.py makemigrations app
docker-compose exec <service-name> python manage.py migrate
```

**Example — after editing `book-service/app/models.py`:**
```bash
docker-compose up -d --build book-service
docker-compose exec book-service python manage.py makemigrations app
docker-compose exec book-service python manage.py migrate
```

---

## 🧭 Key User Flows

```
Register → customer-service auto-creates Customer + Cart
    ↓
Browse Books (book-service) → Add to Cart (cart-service)
    ↓
Checkout → Order (order-service) → Payment (pay-service) + Shipment (ship-service)
    ↓
Rate Book → comment-rate-service
    ↓
Recommendations → recommender-ai-service (3 random book IDs)
```

### Staff Book Management
1. Log in as a user with **Staff** status (set via Django Admin → Users → `is_staff = True`)
2. Visit http://localhost:8000/books/ — **Thêm sách mới** button appears
3. Each book card shows **Sửa** / **Xóa** buttons for staff

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10 |
| Framework | Django 5 + Django REST Framework |
| Database | SQLite (one per service) |
| Container | Docker + Docker Compose |
| Frontend | Bootstrap 5 + Bootstrap Icons |
| Auth | Django built-in auth (session-based) |

---

## 📁 Project Structure

```
bookstore-microservice/
├── api-gateway/          ← Frontend + Auth
├── book-service/         ← Book inventory
├── cart-service/         ← Shopping cart
├── order-service/        ← Order management
├── pay-service/          ← Payments
├── ship-service/         ← Shipping
├── customer-service/     ← Customers
├── staff-service/        ← Staff
├── manager-service/      ← Managers
├── catalog-service/      ← Categories
├── comment-rate-service/ ← Reviews
├── recommender-ai-service/ ← Recommendations
└── docker-compose.yml
```

Each service follows this internal structure:
```
<service>/
├── Dockerfile
├── core/             ← Django project (settings, urls)
├── app/              ← Django app (models, views, urls, serializers)
│   └── management/commands/  ← Custom management commands (seed_*)
└── manage.py
```
