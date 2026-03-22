# Assignment 06 Implementation Plan (Bookstore Microservices)

## Scope (from tutor requirements)
- JWT Authentication Service:
  - Central `auth-service`
  - Role-based access control (RBAC)
  - Token validation at API Gateway
- Saga Pattern for distributed order transaction:
  - Create order (Pending)
  - Reserve payment
  - Reserve shipping
  - Confirm order
  - Compensate if failure
- Event Bus integration:
  - Replace direct coupling where possible with async messaging
  - Use RabbitMQ
- API Gateway responsibilities:
  - Routing
  - Auth validation
  - Logging
  - Rate limiting
- Observability:
  - Health endpoints
  - Metrics endpoint
  - Centralized logging baseline
- Advanced deliverables:
  - Fault simulation
  - Load testing result snapshot
  - Architecture justification update

## Phase Plan

### Phase 1: Auth Foundation (start now)
- Add `auth-service` (Django + DRF + JWT)
- APIs:
  - `POST /auth/register/`
  - `POST /auth/login/`
  - `POST /auth/validate/`
  - `GET /health/`
- Add RBAC role profile (`customer`, `staff`, `manager`, `admin`)
- Integrate `api-gateway` to use central auth for login/register and validate token on protected routes

### Phase 2: Saga Upgrade in order-service
- Add explicit saga states (`Pending`, `Payment Reserved`, `Shipping Reserved`, `Confirmed`, `Payment Failed`, `Shipping Failed`, `Compensated`)
- Add compensation path when shipping fails after payment reservation
- Persist saga step log for debugging/demo

### Phase 3: Event Bus (RabbitMQ)
- Add RabbitMQ service in compose
- Publish order lifecycle events from `order-service`
- Consume events in `pay-service` and `ship-service` (or hybrid REST + event transition)
- Keep API compatibility while moving to async flow

### Phase 4: Gateway Hardening + Observability
- Add auth middleware for token validation + role checks
- Add basic rate limiting in gateway
- Add health endpoint for each service (`/health/`)
- Add simple metrics endpoint (`/metrics/`) with counters
- Add correlation-id logging in gateway and pass downstream

### Phase 5: Validation Deliverables
- Fault simulations:
  - `pay-service` failure
  - `ship-service` failure
  - RabbitMQ unavailable
- Load test smoke (k6 or locust minimal script)
- Update architecture report and API docs for Assignment 06

### Phase 6: Release Gate and Demo Pack
- [x] Add a reproducible acceptance script from clean `docker compose up -d --build`
- [x] Verify all "Done" criteria in one run and save machine-readable artifact
- [x] Refresh API and architecture docs with Assignment 06 updates
- [x] Prepare final commit-ready summary for delivery

### Release Status (2026-03-22)
- Release gate: PASSED
- Latest clean-build acceptance artifact: `scripts/phase6/artifacts/acceptance-summary-20260322-192158.json`
- Result: `done = true` with all 5 done criteria = `true`
- Documentation refreshed:
  - `API_DOCUMENTATION.md` (Assignment 06 Addendum + validation scripts)
  - `Bao_Cao_Kien_Truc_Microservices.md` (Assignment 06 architecture update)
  - `scripts/phase7/PHASE7_QA_REPORT_20260322.md` (UI QA/regression evidence)
  - `scripts/phase7/PHASE7_BEFORE_AFTER_TEMPLATE.md` (before/after checklist)

## Acceptance Criteria for "Done"
- End-to-end JWT login + protected APIs pass
- Order saga transitions visible and compensates correctly
- RabbitMQ-based event flow observable in logs
- Health/metrics endpoints reachable for all key services
- Demo script reproducible from clean `docker compose up -d --build`
