# CONTROLS DOMAIN LOCK — INITIAL

**Status:** DRAFT
**Created:** 2026-01-26
**Reference:** docs/architecture/hoc/CONTROLS_DOMAIN.md

---

## 1. Domain Purpose

The Controls domain provides customer-facing configuration for:

| Control Type | Description |
|--------------|-------------|
| **Token Limits** | Maximum tokens per request/day/month |
| **Cost Limits** | Budget caps and spending thresholds |
| **Credit Usage** | Pre-paid credit tracking and alerts |
| **RAG Auditing** | Verify LLM accessed RAG before inference |

---

## 2. Layer Inventory

### L3 Adapters (Cross-Domain)
| File | Purpose | Status |
|------|---------|--------|
| `policies_adapter.py` | Connect to policy enforcement | PLANNED |
| `analytics_adapter.py` | Pull usage metrics | PLANNED |
| `activity_adapter.py` | Run-level control checks | PLANNED |

### L5 Engines (Business Logic)
| File | Purpose | Status |
|------|---------|--------|
| `token_limit_engine.py` | Token usage evaluation | PLANNED |
| `cost_limit_engine.py` | Cost/budget evaluation | PLANNED |
| `credit_engine.py` | Credit balance tracking | PLANNED |
| `rag_audit_engine.py` | RAG access verification | PLANNED |
| `threshold_engine.py` | Alert threshold logic | PLANNED |
| `controls_facade.py` | Unified interface | PLANNED |

### L5 Schemas
| File | Purpose | Status |
|------|---------|--------|
| `limits.py` | Limit configuration models | PLANNED |
| `thresholds.py` | Threshold definitions | PLANNED |
| `audit_records.py` | RAG audit trail schemas | PLANNED |
| `control_events.py` | Control violation events | PLANNED |

### L6 Drivers (Database)
| File | Purpose | Status |
|------|---------|--------|
| `limits_driver.py` | CRUD for limit configs | PLANNED |
| `usage_driver.py` | Usage tracking persistence | PLANNED |
| `credit_driver.py` | Credit balance operations | PLANNED |
| `audit_driver.py` | RAG audit trail storage | PLANNED |

---

## 3. Engine Authority (L5)

Engines own all control reasoning:

- Token limit threshold evaluation
- Cost budget decision logic
- Credit balance calculations
- RAG access verification from traces
- Alert threshold triggering

**No SQL. No persistence. No direct DB access.**

---

## 4. Driver Responsibility (L6)

Drivers own all persistence:

| Table | Driver | Operations |
|-------|--------|------------|
| `control_limits` | limits_driver | CRUD |
| `control_usage_snapshots` | usage_driver | read/write |
| `control_alerts` | usage_driver | read/write |
| `rag_audit_records` | audit_driver | read/write |

---

## 5. Cross-Domain Dependencies

| Domain | Direction | Purpose |
|--------|-----------|---------|
| analytics | IN | Usage metrics |
| policies | OUT | Enforcement rules |
| activity | BOTH | Per-run checks |
| account | IN | Credit state |
| incidents | OUT | Limit violations |

---

## 6. Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Foundation (schemas, drivers) | NOT STARTED |
| Phase 2 | Token & Cost Limits | NOT STARTED |
| Phase 3 | Credit System | NOT STARTED |
| Phase 4 | RAG Auditing | NOT STARTED |

---

## 7. Governance Rules

1. **L5/L6 Boundary**: Engines decide, Drivers persist
2. **Naming**: `*_engine.py` (L5), `*_driver.py` (L6)
3. **No Service Files**: `*_service.py` is BANNED
4. **BLCA Compliance**: Must pass layer validation

---

*Lock Status: DRAFT — Will be LOCKED after Phase 1 completion*
