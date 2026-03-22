# Phase 7 PR Split Plan

## PR 1 - Core UI Foundation
Scope:
- Shared design tokens and global layout polish
- Navbar/footer/base styles
- Global toast and loading overlay behavior

Files:
- `api-gateway/app/templates/base.html`

Why separate:
- Centralized impact across all pages; easy rollback if global style issue appears.

## PR 2 - User Journey Screens
Scope:
- Books page modernization + filtering/sorting UX
- Login/Register modernization
- Cart/Checkout modernization

Files:
- `api-gateway/app/templates/books.html`
- `api-gateway/app/templates/login.html`
- `api-gateway/app/templates/register.html`
- `api-gateway/app/templates/cart.html`

Why separate:
- Keeps customer-facing regression surface isolated from staff/admin flows.

## PR 3 - Staff CRUD + Accessibility Hardening
Scope:
- New staff list page
- Staff add/edit form modernization
- Staff route/view wiring
- Accessibility enhancements for keyboard and semantics

Files:
- `api-gateway/app/templates/staff_books.html`
- `api-gateway/app/templates/staff_book_form.html`
- `api-gateway/app/views.py`
- `api-gateway/app/urls.py`

Why separate:
- Staff-only scope and RBAC-related behavior can be reviewed independently.

## Validation Checklist Per PR
- [ ] `docker compose up -d`
- [ ] Open affected pages and verify no template errors
- [ ] Run `scripts/phase6/demo-acceptance.ps1 -Build:$false -WaitSeconds 15`
- [ ] Verify messages/loading behavior on changed forms only
