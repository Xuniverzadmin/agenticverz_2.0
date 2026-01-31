# Drivers — Folder Summary

**Path:** `backend/app/hoc/hoc_spine/drivers/`  
**Layer:** L6  
**Scripts:** 13

---

## 1. Purpose

Cross-domain DB boundary. Reads/writes across domain tables. Participates in transactions owned by orchestrator. Only transaction_coordinator may commit.

## 2. What Belongs Here

- Transaction coordinator (sole commit authority)
- Cross-domain read/write operations
- Alert queue management
- Decision record sink
- Schema parity checks

## 3. What Must NOT Be Here

- Commit (except transaction_coordinator)
- Orchestrate execution
- Import L5 engines

## 4. Script Inventory

| Script | Purpose | Transaction | Cross-domain | Verdict |
|--------|---------|-------------|--------------|---------|
| [alert_driver.py](alert_driver.md) | Alert Driver (L6) | Flush only (no commit) | no | OK |
| [alert_emitter.py](alert_emitter.md) | Alert Emitter Service | Forbidden | no | OK |
| [cross_domain.py](cross_domain.md) | Cross-Domain Governance Functions (Mandatory) | Flush only (no commit) | no | OK |
| [dag_executor.py](dag_executor.md) | DAG-based executor for PLang v2.0. | Forbidden | no | OK |
| [decisions.py](decisions.md) | Phase 4B: Decision Record Models and Service | OWNS COMMIT | no | VIOLATION |
| [governance_signal_driver.py](governance_signal_driver.md) | Governance Signal Service (Phase E FIX-03) | Flush only (no commit) | no | OK |
| [guard_cache.py](guard_cache.md) | Redis-based cache for Guard Console endpoints. | Forbidden | no | OK |
| [guard_write_driver.py](guard_write_driver.md) | Guard Write Driver (L6) | Forbidden | no | OK |
| [idempotency.py](idempotency.md) | Idempotency key utilities | Forbidden | no | OK |
| [ledger.py](ledger.md) | Discovery Ledger - signal recording helpers. | OWNS COMMIT | no | VIOLATION |
| [schema_parity.py](schema_parity.md) | M26 Prevention Mechanism #2: Startup Schema Parity Guard | Forbidden | no | OK |
| [transaction_coordinator.py](transaction_coordinator.md) | Transaction Coordinator for Cross-Domain Writes | OWNS COMMIT | no | OK |
| [worker_write_service_async.py](worker_write_service_async.md) | Worker Write Service (Async) - DB write operations for Worke | Forbidden | no | OK |

## 5. Assessment

**Correct:** 11/13 scripts pass all governance checks.

**Violations (2):**

- `decisions.py` — Driver calls commit (only transaction_coordinator allowed)
- `ledger.py` — Driver calls commit (only transaction_coordinator allowed)

**Missing (from reconciliation artifact):**

- Runtime enforcement: block commit() in non-coordinator drivers
- Clear READ vs WRITE driver naming distinction

## 6. L5 Pairing Aggregate

| Script | Serves Domains | Wired L5 Consumers | Gaps |
|--------|----------------|--------------------|------|
| alert_driver.py | _none_ | 0 | 0 |
| alert_emitter.py | _none_ | 0 | 0 |
| cross_domain.py | _none_ | 0 | 0 |
| dag_executor.py | _none_ | 0 | 0 |
| decisions.py | _none_ | 0 | 0 |
| governance_signal_driver.py | _none_ | 0 | 0 |
| guard_cache.py | _none_ | 0 | 0 |
| guard_write_driver.py | _none_ | 0 | 0 |
| idempotency.py | _none_ | 0 | 0 |
| ledger.py | _none_ | 0 | 0 |
| schema_parity.py | _none_ | 0 | 0 |
| transaction_coordinator.py | _none_ | 0 | 0 |
| worker_write_service_async.py | _none_ | 0 | 0 |

