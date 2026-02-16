# PR1_RUNS_FACADE_VERIFICATION_2026-02-16

## Status
- Date: 2026-02-16
- Scope: deterministic verification contract for PR-1 Runs facade hardening.

## Verification Goals
1. Confirm new Runs facade endpoint behavior and pagination stability.
2. Confirm route integrity (facade wiring present, no layer violations).
3. Confirm legacy dependence has a documented replacement path.

## Test Checklist

### A) Route and Contract Checks
- [ ] `GET /cus/activity/runs?topic=live&limit=50&offset=0` returns 200 with paginated shape.
- [ ] `GET /cus/activity/runs?topic=completed&limit=50&offset=0` returns 200 with paginated shape.
- [ ] `GET /cus/activity/runs?topic=signals&limit=20` returns 200 with signals shape.
- [ ] Invalid topic returns 4xx with actionable error.
- [ ] Response exposes request correlation (`X-Request-ID` and/or `meta.request_id`).

### B) Determinism and Pagination
- [ ] Repeated requests with same topic/filter/as_of produce stable ordering.
- [ ] `next_offset` logic consistent with `has_more` and `limit`.
- [ ] No client-side fallback pagination assumptions required.

### C) Governance/Layers
- [ ] L2.1 facade layer contains no business logic.
- [ ] L2 -> L4 path remains intact.
- [ ] No new `/api/v1/*` route introduced.

### D) Migration Safety
- [ ] PR-0 compatibility matrix updated with final mapping for runs.
- [ ] Frontend migration note references `/cus/activity/runs` as authoritative entry.

## Deterministic Commands

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
```

## Evidence Artifacts Required
- Route contract proof (curl/httpie output or integration test output)
- Gate outputs from deterministic commands above
- Updated compatibility mapping entry for runs

## Fail Conditions
- Facade endpoint missing or non-deterministic response order.
- Pagination shape mismatch or missing correlation ID.
- Any new layer-boundary violation or `/api/v1/*` reintroduction.
