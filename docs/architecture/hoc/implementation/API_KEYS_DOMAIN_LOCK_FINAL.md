# API Keys Domain — LOCK FINAL
# Status: LOCKED
# Date: 2026-01-24
# BLCA Status: CLEAN (0 violations)
# Reference: API_KEYS_PHASE2.5_IMPLEMENTATION_PLAN.md

---

## Domain Certification

| Check | Status | Evidence |
|-------|--------|----------|
| BLCA Scan | ✅ CLEAN | 0 violations in api_keys domain |
| Facade Extraction | ✅ COMPLETE | `api_keys_facade.py` → `api_keys_facade_driver.py` |
| Engine Extraction | ✅ COMPLETE | `keys_service.py` → `keys_engine.py` + `keys_driver.py` |
| Service Naming | ✅ FIXED | `keys_service.py` deleted, replaced with `keys_engine.py` |
| Layer Reclassification | ✅ COMPLETE | `email_verification.py` L3 → L4 |
| Header Corrections | ✅ COMPLETE | `drivers/__init__.py` L4 → L6 |

---

## Final File Structure

```
backend/app/hoc/cus/api_keys/
├── __init__.py
├── adapters/
│   └── __init__.py
├── drivers/
│   ├── __init__.py                    # L6 — Platform Substrate
│   ├── api_keys_facade_driver.py      # L6 — Async driver for facade
│   └── keys_driver.py                 # L6 — Sync driver for engine
├── engines/
│   ├── __init__.py
│   ├── email_verification.py          # L4 — Domain Engine (reclassified)
│   └── keys_engine.py                 # L4 — Domain Engine (new)
├── facades/
│   ├── __init__.py
│   └── api_keys_facade.py             # L4 — Domain Facade
└── schemas/
    └── __init__.py
```

---

## Layer Distribution

| Layer | Files | Role |
|-------|-------|------|
| L4 (Domain Engine) | `api_keys_facade.py`, `keys_engine.py`, `email_verification.py` | Business logic, orchestration |
| L6 (Platform Substrate) | `api_keys_facade_driver.py`, `keys_driver.py`, `drivers/__init__.py` | Pure data access |

---

## Violations Remediated

| # | File | Violation | Resolution |
|---|------|-----------|------------|
| 1 | `api_keys_facade.py` | L4 with sqlalchemy runtime imports | ✅ Extracted to `api_keys_facade_driver.py` |
| 2 | `api_keys_facade.py` | L4→L7 model import | ✅ Moved to driver |
| 3 | `keys_service.py` | L4 with sqlalchemy runtime imports | ✅ Extracted to `keys_driver.py` |
| 4 | `keys_service.py` | L4→L7 model imports | ✅ Moved to driver |
| 5 | `keys_service.py` | BANNED_NAMING (`*_service.py`) | ✅ Renamed to `keys_engine.py` |
| 6 | `email_verification.py` | Layer/location mismatch (L3 in engines/) | ✅ Reclassified to L4 |
| 7 | `drivers/__init__.py` | Wrong layer header (L4) | ✅ Corrected to L6 |

---

## Governance Invariants (Enforced)

| ID | Rule | Status |
|----|------|--------|
| INV-KEY-001 | L4 cannot import sqlalchemy at runtime | ✅ ENFORCED |
| INV-KEY-002 | L4 cannot import from L7 models directly | ✅ ENFORCED |
| INV-KEY-003 | Facades delegate, never query directly | ✅ ENFORCED |
| INV-KEY-004 | Call flow: Facade → Engine → Driver | ✅ ENFORCED |
| INV-KEY-005 | Driver returns snapshots, not ORM models | ✅ ENFORCED |
| INV-KEY-006 | `*_service.py` naming banned | ✅ ENFORCED |

---

## Call Flow Verification

### Facade Path (Async, Customer Console)
```
L2 API (aos_api_key.py)
    ↓
L4 Facade (api_keys_facade.py)
    ↓
L6 Driver (api_keys_facade_driver.py)
    ↓
L7 Models (app.models.tenant.APIKey)
```

### Engine Path (Sync, Runtime/Gateway)
```
L3 Adapter (customer_keys_adapter.py)
    ↓
L4 Engine (keys_engine.py)
    ↓
L6 Driver (keys_driver.py)
    ↓
L7 Models (app.models.tenant.APIKey)
```

---

## Files Deleted

| File | Reason |
|------|--------|
| `engines/keys_service.py` | BANNED_NAMING, split into engine + driver |

---

## Domain Axiom (LOCKED)

> **API Keys is an ACCESS-PRIMITIVE domain, not an identity or governance domain.**

Consequences:
1. L4 may decide **key validity, expiry, freeze status, scope match**
2. L4 must NEVER decide **tenant status, account suspension, rate limits, kill-switches**
3. L6 may only **persist, query, or aggregate key data**
4. Call flow: **Facade → Engine → Driver** (mandatory)

---

## Post-Lock Constraints

Any future changes to the api_keys domain MUST:

1. Maintain 0 BLCA violations
2. Follow the established call flow patterns
3. Place all DB operations in L6 drivers
4. Keep business logic in L4 engines/facades
5. Use snapshot dataclasses for driver return types
6. Never use `*_service.py` naming

---

## Certification

```
DOMAIN: api_keys
STATUS: LOCKED
DATE: 2026-01-24
BLCA: CLEAN (0 violations)
PHASE: 2.5B COMPLETE
```

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial lock | Claude |
| 2026-01-24 | 1.1.0 | Phase 2.5E BLCA verification: 0 errors, 0 warnings across all 6 check types | Claude |

---

**END OF LOCK DOCUMENT**
