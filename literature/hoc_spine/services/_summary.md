# Services — Folder Summary

**Path:** `backend/app/hoc/cus/hoc_spine/services/`  
**Layer:** L5  
**Scripts:** 24

---

## 1. Purpose

Spine-only shared utilities. Must be stateless, deterministic, and domain-agnostic. Time, IDs, audit, runtime flags, crypto verification.

## 2. What Belongs Here

- Time utilities
- ID generation
- Audit store
- Runtime flags and configuration
- Cryptographic verification
- Input sanitization
- Deterministic helpers

## 3. What Must NOT Be Here

- Import L5 engines
- Import L6 drivers
- Import schemas outside hoc_spine
- Contain domain-specific business logic

## 4. Script Inventory

| Script | Purpose | Transaction | Cross-domain | Verdict |
|--------|---------|-------------|--------------|---------|
| [alert_delivery.py](alert_delivery.md) | Alert Delivery Adapter (L2) | Forbidden | no | OK |
| [alerts_facade.py](alerts_facade.md) | Alerts Facade (L4 Domain Logic) | Forbidden | no | OK |
| [audit_durability.py](audit_durability.md) | Module: durability | Forbidden | no | OK |
| [audit_store.py](audit_store.md) | Audit Store | Forbidden | no | OK |
| [canonical_json.py](canonical_json.md) | Canonical JSON serialization for AOS. | Forbidden | no | OK |
| [compliance_facade.py](compliance_facade.md) | Compliance Facade (L4 Domain Logic) | Forbidden | no | OK |
| [control_registry.py](control_registry.md) | Module: control_registry | Forbidden | no | OK |
| [cus_credential_service.py](cus_credential_service.md) | Customer Credential Service | Forbidden | no | OK |
| [dag_sorter.py](dag_sorter.md) | DAG-based execution ordering for PLang v2.0. | Forbidden | no | OK |
| [db_helpers.py](db_helpers.md) | Database helper functions for SQLModel row extraction. | Flush only (no commit) | no | OK |
| [deterministic.py](deterministic.md) | Deterministic execution utilities (pure computation, no boun | Forbidden | no | OK |
| [fatigue_controller.py](fatigue_controller.md) | AlertFatigueController - Alert fatigue management service. | Forbidden | no | OK |
| [guard.py](guard.md) | Guard Console Data Contracts - Customer-Facing API | Forbidden | no | OK |
| [input_sanitizer.py](input_sanitizer.md) | Input sanitization for security (pure regex validation and U | Forbidden | no | OK |
| [lifecycle_facade.py](lifecycle_facade.md) | Lifecycle Facade (L4 Domain Logic) | Forbidden | no | OK |
| [lifecycle_stages_base.py](lifecycle_stages_base.md) | Stage Handler Protocol and Base Types | Forbidden | no | OK |
| [metrics_helpers.py](metrics_helpers.md) | Prometheus Metrics Helpers - Idempotent Registration | Forbidden | no | OK |
| [monitors_facade.py](monitors_facade.md) | Monitors Facade (L4 Domain Logic) | Forbidden | no | OK |
| [rate_limiter.py](rate_limiter.md) | Rate limiting utilities (Redis-backed) | Forbidden | no | OK |
| [retrieval_facade.py](retrieval_facade.md) | Retrieval Facade (L4 Domain Logic) | Forbidden | no | OK |
| [retrieval_mediator.py](retrieval_mediator.md) | Module: retrieval_mediator | Forbidden | no | OK |
| [scheduler_facade.py](scheduler_facade.md) | Scheduler Facade (L4 Domain Logic) | Forbidden | no | OK |
| [time.py](time.md) | Common time utilities for customer domain modules (pure date | Forbidden | no | OK |
| [webhook_verify.py](webhook_verify.md) | Webhook Signature Verification Utility | Forbidden | no | OK |

## 5. Assessment

**Correct:** 24/24 scripts pass all governance checks.

No violations or missing primitives detected.

## 6. L5 Pairing Aggregate

| Script | Serves Domains | Wired L5 Consumers | Gaps |
|--------|----------------|--------------------|------|
| alert_delivery.py | _none_ | 0 | 0 |
| alerts_facade.py | _none_ | 0 | 0 |
| audit_durability.py | _none_ | 0 | 0 |
| audit_store.py | _none_ | 0 | 0 |
| canonical_json.py | _none_ | 0 | 0 |
| compliance_facade.py | _none_ | 0 | 0 |
| control_registry.py | _none_ | 0 | 0 |
| cus_credential_service.py | _none_ | 0 | 0 |
| dag_sorter.py | _none_ | 0 | 0 |
| db_helpers.py | _none_ | 0 | 0 |
| deterministic.py | _none_ | 0 | 0 |
| fatigue_controller.py | _none_ | 0 | 0 |
| guard.py | _none_ | 0 | 0 |
| input_sanitizer.py | _none_ | 0 | 0 |
| lifecycle_facade.py | _none_ | 0 | 0 |
| lifecycle_stages_base.py | _none_ | 0 | 0 |
| metrics_helpers.py | _none_ | 0 | 0 |
| monitors_facade.py | _none_ | 0 | 0 |
| rate_limiter.py | _none_ | 0 | 0 |
| retrieval_facade.py | _none_ | 0 | 0 |
| retrieval_mediator.py | _none_ | 0 | 0 |
| scheduler_facade.py | _none_ | 0 | 0 |
| time.py | _none_ | 0 | 0 |
| webhook_verify.py | _none_ | 0 | 0 |

