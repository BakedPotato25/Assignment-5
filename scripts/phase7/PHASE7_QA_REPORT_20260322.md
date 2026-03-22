# Phase 7 QA Report (2026-03-22)

## Scope
- Browse books UI
- Login/Register flow
- Cart update + checkout flow
- Staff CRUD flow (add/edit/delete page accessibility and navigation)
- Health and metrics observability

## Execution Method
- Script: scripts/phase6/demo-acceptance.ps1
- Command used:
  - `./scripts/phase6/demo-acceptance.ps1 -Build:$false -WaitSeconds 15`
- Artifact:
  - `scripts/phase6/artifacts/acceptance-summary-20260322-190418.json`

## Regression Results
- JWT login + protected API: PASS
- Saga transition + compensation: PASS
- RabbitMQ event flow observable: PASS
- Health + metrics reachable: PASS
- Reproducible from clean build: NOT VERIFIED (run without build)

## Evidence Snapshot
- Cart protected endpoint status: 200
- Auth login status: 200
- Token validation: true
- Successful order final status: Confirmed
- Compensation scenario status: Compensated (ship-service stopped)
- Event markers in logs:
  - EVENT_PUBLISHED count: 20
  - EVENT_CONSUMED count: 7
- Health/metrics endpoints checked: gateway, auth, order, pay, ship (all 200)

## Risk Notes
- Full clean-build reproducibility remains unchecked in this run because script was executed with `-Build:$false` to reduce cycle time.
- UI screenshot evidence is tracked in a separate template and pending capture.

## Recommendation
- For release readiness, run one final acceptance cycle with:
  - `./scripts/phase6/demo-acceptance.ps1 -Build -WaitSeconds 20`
