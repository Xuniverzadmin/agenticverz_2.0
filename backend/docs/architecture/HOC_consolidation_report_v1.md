# HOC Customer Domains Consolidation Report v1

**Date:** 2026-01-22
**Scope:** `app/houseofcards/customer/`
**Status:** Phase 4 Analysis Complete

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Files** | 184 Python files |
| **Total LOC** | 71,018 LOC |
| **Domains** | 10 customer domains |
| **Critical Duplicates** | 2 (ValidatorService) |
| **Pattern Duplicates** | 38+ files affected |
| **Estimated Savings** | ~3,690 LOC |
| **Blast Radius (High)** | 5 files |
| **Blast Radius (Medium)** | 15 files |

---

## Domain Statistics

| Domain | Files | LOC | Primary Responsibility |
|--------|-------|-----|------------------------|
| **general** | 39 | 18,719 | Runtime orchestration, lifecycle, cross-domain |
| **policies** | 35 | 15,557 | Policy rules, limits, governance |
| **logs** | 20 | 8,459 | Traces, evidence, audit |
| **integrations** | 21 | 8,222 | Connectors, vault, external services |
| **account** | 16 | 6,746 | Users, tenants, notifications, CRM |
| **incidents** | 16 | 5,803 | Incident lifecycle, recovery |
| **analytics** | 12 | 4,171 | Cost analysis, anomaly detection |
| **activity** | 11 | 1,970 | Run activity, signals, patterns |
| **overview** | 6 | 801 | Dashboard aggregation |
| **api_keys** | 7 | 543 | API key management |

---

## Section 1: Critical Duplicates

### 1.1 ValidatorService (EXACT DUPLICATE)

**Severity:** CRITICAL
**LOC Wasted:** 1,460 (730 × 2)
**Consolidation Savings:** ~1,060 LOC

#### File Locations

| # | File Path | LOC |
|---|-----------|-----|
| 1 | `policies/engines/validator_service.py` | 730 |
| 2 | `account/support/CRM/engines/validator_service.py` | 730 |

#### Imports (Both Files - IDENTICAL)

```python
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID
```

#### Exports (Both Files - IDENTICAL)

| Export | Type | Description |
|--------|------|-------------|
| `VALIDATOR_VERSION` | Constant | `"1.0.0"` |
| `IssueType` | Enum | CAPABILITY_REQUEST, BUG_REPORT, CONFIGURATION_CHANGE, ESCALATION, UNKNOWN |
| `Severity` | Enum | CRITICAL, HIGH, MEDIUM, LOW |
| `RecommendedAction` | Enum | CREATE_CONTRACT, DEFER, REJECT, ESCALATE |
| `IssueSource` | Enum | OPS_ALERT, SUPPORT_TICKET, CRM_FEEDBACK, MANUAL, INTEGRATION |
| `ValidatorInput` | Dataclass | Input to validator |
| `ValidatorVerdict` | Dataclass | Output from validator |
| `ValidatorErrorType` | Enum | PARSE_ERROR, REGISTRY_UNAVAILABLE, TIMEOUT, UNKNOWN |
| `ValidatorError` | Dataclass | Error with fallback verdict |
| `ValidatorService` | Class | Main service class |

#### Functions (ValidatorService Class - IDENTICAL)

| Method | Signature | Lines |
|--------|-----------|-------|
| `__init__` | `(capability_registry: Optional[list[str]])` | 3 |
| `validate` | `(input: ValidatorInput) -> ValidatorVerdict` | 8 |
| `_do_validate` | `(input: ValidatorInput) -> ValidatorVerdict` | 50 |
| `_extract_text` | `(payload: dict) -> str` | 20 |
| `_classify_issue_type` | `(text: str) -> tuple[IssueType, Decimal, dict]` | 55 |
| `_classify_severity` | `(text: str, issue_type: IssueType) -> tuple[Severity, Decimal]` | 35 |
| `_find_severity_indicators` | `(text: str) -> dict` | 7 |
| `_extract_capabilities` | `(text: str, hints: Optional[list]) -> list[str]` | 20 |
| `_get_source_weight` | `(source: str) -> Decimal` | 12 |
| `_get_capability_confidence` | `(capabilities: list) -> Decimal` | 12 |
| `_calculate_confidence` | `(...) -> Decimal` | 15 |
| `_determine_action` | `(...) -> RecommendedAction` | 20 |
| `_build_reason` | `(...) -> str` | 15 |
| `_create_fallback_verdict` | `(...) -> ValidatorVerdict` | 15 |

#### Keyword Constants (IDENTICAL)

| Constant | Count | Purpose |
|----------|-------|---------|
| `CAPABILITY_REQUEST_KEYWORDS` | 10 | enable, disable, feature, etc. |
| `BUG_REPORT_KEYWORDS` | 10 | bug, broken, error, etc. |
| `CONFIGURATION_KEYWORDS` | 9 | configure, setting, etc. |
| `ESCALATION_KEYWORDS` | 9 | urgent, emergency, etc. |
| `CRITICAL_INDICATORS` | 7 | multiple tenants, security, etc. |
| `HIGH_INDICATORS` | 5 | severely impacted, blocked, etc. |
| `LOW_INDICATORS` | 6 | cosmetic, enhancement, etc. |

#### Invariants (Both Files)

| ID | Rule | Enforcement |
|----|------|-------------|
| VAL-001 | Validator is stateless (no writes) | Code inspection |
| VAL-002 | Verdicts include version | Required field |
| VAL-003 | Confidence in [0,1] | Clamping logic |
| VAL-004 | Unknown type defers | Action logic |
| VAL-005 | Escalation always escalates | Priority check |

#### Consolidation Path

```
1. Create: app/houseofcards/shared/validators/issue_validator.py
2. Move: ValidatorService + all enums/dataclasses
3. Update: policies/engines/__init__.py to re-export
4. Update: account/support/CRM/engines/__init__.py to re-export
5. Delete: Original files after validation
```

#### Blast Radius

| Impact Level | Files Affected |
|--------------|----------------|
| HIGH | 2 (original files) |
| MEDIUM | 4 (callers in L3 adapters) |
| LOW | 6 (downstream consumers) |

---

## Section 2: Read Service Pattern Duplicates

### 2.1 Pattern Overview

**Pattern Name:** Tenant-Scoped Read Service
**Files Affected:** 8
**LOC Duplicated:** ~1,300

### 2.2 File Inventory

| # | File | LOC | Domain | Methods |
|---|------|-----|--------|---------|
| 1 | `incidents/engines/incident_read_service.py` | 200 | Incidents | 5 |
| 2 | `logs/engines/logs_read_service.py` | 207 | Logs | 5 |
| 3 | `policies/engines/customer_policy_read_service.py` | ~200 | Policies | 4 |
| 4 | `policies/controls/engines/customer_killswitch_read_service.py` | ~200 | Policies | 4 |
| 5 | `analytics/engines/cost_read_service.py` | ~180 | Analytics | 4 |
| 6 | `integrations/engines/connector_read_service.py` | ~180 | Integrations | 4 |
| 7 | `account/engines/user_read_service.py` | ~180 | Account | 4 |
| 8 | `api_keys/engines/keys_read_service.py` | ~180 | API Keys | 4 |

### 2.3 Shared Pattern Analysis

#### Imports (All Read Services)

```python
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlmodel import Session

# L6 imports (domain-specific model)
from app.models.<domain> import <Model>
```

#### Common Methods (All Services)

| Method | Signature | Purpose |
|--------|-----------|---------|
| `__init__` | `(session: Session)` | Initialize with DB session |
| `list_<items>` | `(tenant_id, limit=50, offset=0, **filters) -> Tuple[List, int]` | Paginated list |
| `get_<item>` | `(item_id, tenant_id) -> Optional[Item]` | Single item lookup |
| `count_<items>` | `(tenant_id) -> int` | Count query |
| `search_<items>` | `(tenant_id, **filters) -> List[Item]` | Filtered search |

#### Tenant Isolation Pattern (IDENTICAL)

```python
def list_<items>(self, tenant_id: str, limit: int = 50, offset: int = 0, **filters):
    # Enforce pagination limits
    limit = min(limit, 100)

    # Build query with tenant isolation
    conditions = [<Model>.tenant_id == tenant_id]

    if status:
        conditions.append(<Model>.status == status)
    # ... more filters

    # Query items
    stmt = select(<Model>).where(and_(*conditions)).order_by(desc(<Model>.created_at)).offset(offset).limit(limit)
    rows = self._session.exec(stmt).all()

    # Get total count
    count_stmt = select(func.count(<Model>.id)).where(and_(*conditions))
    total = self._session.exec(count_stmt).first()[0]

    return items, total
```

### 2.4 Consolidation Opportunity: BaseTenantReadService

```python
# Proposed: app/houseofcards/shared/services/base_read_service.py

from typing import Generic, TypeVar, List, Optional, Tuple, Type
from sqlalchemy import and_, desc, func, select
from sqlmodel import Session

T = TypeVar('T')

class BaseTenantReadService(Generic[T]):
    """Base class for tenant-scoped read services."""

    model: Type[T]  # Set by subclass

    def __init__(self, session: Session):
        self._session = session

    def list_items(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
        **filters
    ) -> Tuple[List[T], int]:
        """Generic paginated list with tenant isolation."""
        limit = min(limit, 100)
        conditions = [self.model.tenant_id == tenant_id]
        # ... generic implementation

    def get_item(self, item_id: str, tenant_id: str) -> Optional[T]:
        """Generic single item lookup with tenant isolation."""
        # ... generic implementation

    def count_items(self, tenant_id: str) -> int:
        """Generic count with tenant isolation."""
        # ... generic implementation
```

### 2.5 Per-File Maturity Assessment

| File | Maturity | Tests | Documentation | Invariants |
|------|----------|-------|---------------|------------|
| `incident_read_service.py` | HIGH | Yes | Complete | 2 |
| `logs_read_service.py` | HIGH | Yes | Complete | 2 |
| `customer_policy_read_service.py` | MEDIUM | Partial | Basic | 1 |
| `customer_killswitch_read_service.py` | MEDIUM | Partial | Basic | 1 |
| Other services | LOW | None | Minimal | 0 |

---

## Section 3: Write Service Pattern Duplicates

### 3.1 Pattern Overview

**Pattern Name:** Tenant-Scoped Write Service
**Files Affected:** 5
**LOC Duplicated:** ~750

### 3.2 File Inventory

| # | File | LOC | Domain | Status |
|---|------|-----|--------|--------|
| 1 | `incidents/engines/incident_write_service.py` | 284 | Incidents | PRODUCTION |
| 2 | `general/controls/engines/guard_write_service.py` | 249 | General | TEMPORARY |
| 3 | `analytics/engines/cost_write_service.py` | 225 | Analytics | PRODUCTION |
| 4 | `account/engines/user_write_service.py` | ~200 | Account | PRODUCTION |
| 5 | `policies/engines/policy_write_service.py` | ~200 | Policies | PRODUCTION |

### 3.3 Incident Write Service Analysis

#### Imports

```python
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session
from app.models.killswitch import Incident, IncidentEvent, IncidentStatus
from app.models.audit_ledger import ActorType
from app.services.logs.audit_ledger_service import AuditLedgerService
```

#### Exports

| Export | Type | Description |
|--------|------|-------------|
| `IncidentWriteService` | Class | Main service |
| `get_incident_write_service` | Factory | Session-based factory |

#### Methods

| Method | Signature | Transaction | Audit |
|--------|-----------|-------------|-------|
| `acknowledge_incident` | `(incident, acknowledged_by, actor_type, reason)` | ATOMIC | Yes |
| `resolve_incident` | `(incident, resolved_by, resolution_notes, ...)` | ATOMIC | Yes |
| `manual_close_incident` | `(incident, closed_by, reason, actor_type)` | ATOMIC | Yes |

#### Transaction Contract

```
TRANSACTION CONTRACT:
- State change and audit event commit together (atomic)
- If audit emit fails, incident change rolls back
- No partial state is possible
```

### 3.4 Guard Write Service Analysis (TEMPORARY)

#### Header Warning

```python
# PHASE 2 NOTE:
# This is a TEMPORARY AGGREGATE service for Phase 2 structural extraction.
# It bundles KillSwitch, Incident, and IncidentEvent writes together.
# Post-alignment (Phase 3+), this may split into:
#   - KillSwitchWriteService
#   - IncidentWriteService
# Do NOT split during Phase 2.
```

#### Methods

| Method | Signature | Transaction |
|--------|-----------|-------------|
| `get_or_create_killswitch_state` | `(entity_type, entity_id, tenant_id)` | None |
| `freeze_killswitch` | `(state, by, reason, auto, trigger)` | COMMIT |
| `unfreeze_killswitch` | `(state, by)` | COMMIT |
| `acknowledge_incident` | `(incident)` | COMMIT |
| `resolve_incident` | `(incident)` | COMMIT |
| `create_demo_incident` | `(incident_id, tenant_id, ...)` | COMMIT |

#### Maturity Assessment

| Aspect | Status |
|--------|--------|
| Layer Compliance | L4 (correct) |
| Temporary Status | YES - Phase 3 deadline |
| Audit Integration | NO (missing) |
| Tests | Partial |
| Documentation | Complete |

### 3.5 Cost Write Service Analysis

#### Imports

```python
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session
from app.db import CostBudget, CostRecord, FeatureTag
```

#### Methods

| Method | Signature | Transaction |
|--------|-----------|-------------|
| `create_feature_tag` | `(tenant_id, tag, display_name, ...)` | COMMIT |
| `update_feature_tag` | `(feature_tag, display_name, ...)` | COMMIT |
| `create_cost_record` | `(tenant_id, user_id, ...)` | COMMIT |
| `create_or_update_budget` | `(existing_budget, tenant_id, ...)` | COMMIT |

### 3.6 Shared Write Pattern

```python
# Common structure across all write services
class <Domain>WriteService:
    def __init__(self, session: Session):
        self._session = session

    def create_<item>(self, **kwargs) -> <Item>:
        item = <Item>(**kwargs)
        self._session.add(item)
        self._session.commit()
        self._session.refresh(item)
        return item

    def update_<item>(self, item: <Item>, **updates) -> <Item>:
        for key, value in updates.items():
            if value is not None:
                setattr(item, key, value)
        item.updated_at = utc_now()
        self._session.add(item)
        self._session.commit()
        self._session.refresh(item)
        return item
```

---

## Section 4: Event Emission Duplicates

### 4.1 Pattern Overview

**Pattern Name:** Domain Event Emission
**Files Affected:** 11
**LOC Duplicated:** ~330

### 4.2 Files with Event Emission

| # | File | Domain | Event Types |
|---|------|--------|-------------|
| 1 | `general/runtime/engines/transaction_coordinator.py` | General | incident_created, policy_evaluated |
| 2 | `general/runtime/engines/run_governance_facade.py` | General | lesson_emitted, threshold_warning |
| 3 | `incidents/engines/incident_write_service.py` | Incidents | acknowledged, resolved |
| 4 | `general/controls/engines/guard_write_service.py` | General | killswitch_toggled |
| 5 | `policies/facades/policies_facade.py` | Policies | policy_proposed, policy_approved |
| 6 | `incidents/facades/incidents_facade.py` | Incidents | incident_created |
| 7 | `account/engines/user_write_service.py` | Account | user_created |
| 8 | `analytics/engines/cost_anomaly_detector.py` | Analytics | anomaly_detected |
| 9 | `integrations/engines/connector_registry.py` | Integrations | connector_registered |
| 10 | `logs/engines/audit_evidence.py` | Logs | evidence_created |
| 11 | `api_keys/engines/keys_service.py` | API Keys | key_created |

### 4.3 Common Pattern

```python
# Pattern found in all 11 files
def emit_<event>(self, event_type: str, payload: dict):
    publisher = get_publisher()
    publisher.publish(event_type, payload)
    logger.info(f"{event_type}_emitted", extra={"tenant_id": ..., "event": event_type})
```

### 4.4 Consolidation Opportunity: EventEmitter

```python
# Proposed: app/houseofcards/shared/events/emitter.py

class DomainEventEmitter:
    """Centralized domain event emission."""

    def __init__(self, domain: str):
        self._domain = domain
        self._publisher = get_publisher()
        self._logger = logging.getLogger(f"nova.events.{domain}")

    def emit(self, event_type: str, payload: dict, tenant_id: str):
        """Emit a domain event with logging."""
        self._publisher.publish(event_type, payload)
        self._logger.info(
            f"{event_type}_emitted",
            extra={"tenant_id": tenant_id, "domain": self._domain}
        )
```

---

## Section 5: Tenant Query Builder Duplicates

### 5.1 Pattern Overview

**Pattern Name:** Tenant Isolation Query Building
**Files Affected:** 12
**LOC Duplicated:** ~600

### 5.2 Common Code Pattern

```python
# Found in 12+ read services
conditions = [<Model>.tenant_id == tenant_id]
if status:
    conditions.append(<Model>.status == status)
if severity:
    conditions.append(<Model>.severity == severity)
if from_date:
    conditions.append(<Model>.created_at >= from_date)
if to_date:
    conditions.append(<Model>.created_at <= to_date)

stmt = select(<Model>).where(and_(*conditions)).order_by(desc(<Model>.created_at))
```

### 5.3 Consolidation Opportunity: TenantQueryBuilder

```python
# Proposed: app/houseofcards/shared/queries/tenant_query_builder.py

class TenantQueryBuilder:
    """Build tenant-isolated queries with common filters."""

    def __init__(self, model: Type, tenant_id: str):
        self._model = model
        self._conditions = [model.tenant_id == tenant_id]

    def filter_status(self, status: Optional[str]):
        if status:
            self._conditions.append(self._model.status == status)
        return self

    def filter_date_range(self, from_date: Optional[datetime], to_date: Optional[datetime]):
        if from_date:
            self._conditions.append(self._model.created_at >= from_date)
        if to_date:
            self._conditions.append(self._model.created_at <= to_date)
        return self

    def build_select(self) -> Select:
        return select(self._model).where(and_(*self._conditions))

    def build_count(self) -> Select:
        return select(func.count(self._model.id)).where(and_(*self._conditions))
```

---

## Section 6: File Maturity Assessment

### 6.1 Maturity Levels

| Level | Criteria |
|-------|----------|
| **PRODUCTION** | Tests, docs, invariants, stable API |
| **HIGH** | Tests, docs, some invariants |
| **MEDIUM** | Partial tests, basic docs |
| **LOW** | No tests, minimal docs |
| **TEMPORARY** | Explicitly marked for refactoring |

### 6.2 Domain Maturity Summary

| Domain | PRODUCTION | HIGH | MEDIUM | LOW | TEMPORARY |
|--------|------------|------|--------|-----|-----------|
| general | 8 | 12 | 10 | 8 | 1 |
| policies | 10 | 15 | 8 | 2 | 0 |
| logs | 8 | 6 | 4 | 2 | 0 |
| integrations | 4 | 8 | 6 | 3 | 0 |
| incidents | 6 | 6 | 3 | 1 | 0 |
| account | 4 | 6 | 4 | 2 | 0 |
| analytics | 3 | 5 | 3 | 1 | 0 |
| activity | 2 | 4 | 3 | 2 | 0 |
| overview | 1 | 2 | 2 | 1 | 0 |
| api_keys | 1 | 3 | 2 | 1 | 0 |

### 6.3 Key File Maturity

| File | Maturity | Tests | Invariants | Blast Radius |
|------|----------|-------|------------|--------------|
| `governance_orchestrator.py` | PRODUCTION | Yes | 3 | HIGH |
| `contract_service.py` | PRODUCTION | Yes | 7 | HIGH |
| `incident_engine.py` | PRODUCTION | Yes | 4 | HIGH |
| `policies_facade.py` | HIGH | Partial | 2 | HIGH |
| `logs_facade.py` | HIGH | Partial | 3 | MEDIUM |
| `validator_service.py` (x2) | HIGH | Yes | 5 | MEDIUM |
| `guard_write_service.py` | TEMPORARY | Partial | 0 | MEDIUM |
| `cost_anomaly_detector.py` | MEDIUM | None | 2 | LOW |
| `rollout_projection.py` | HIGH | Yes | 6 | MEDIUM |

---

## Section 7: Blast Radius Analysis

### 7.1 HIGH Blast Radius Files

Files where changes affect multiple domains or critical paths.

| File | LOC | Callers | Cross-Domain | Risk |
|------|-----|---------|--------------|------|
| `governance_orchestrator.py` | 799 | 8+ | Yes | CRITICAL |
| `transaction_coordinator.py` | 828 | 6+ | Yes | CRITICAL |
| `contract_service.py` | 707 | 5+ | Yes | HIGH |
| `incident_engine.py` | 1,011 | 7+ | Yes | HIGH |
| `cross_domain.py` | 497 | ALL | Yes | CRITICAL |

### 7.2 MEDIUM Blast Radius Files

Files where changes affect single domain but multiple services.

| File | LOC | Callers | Risk |
|------|-----|---------|------|
| `policies_facade.py` | 1,496 | 4 | MEDIUM |
| `logs_facade.py` | 1,591 | 5 | MEDIUM |
| `incidents_facade.py` | 1,103 | 4 | MEDIUM |
| `activity_facade.py` | 1,490 | 3 | MEDIUM |
| `accounts_facade.py` | 1,307 | 4 | MEDIUM |
| `analytics_facade.py` | 828 | 3 | MEDIUM |

### 7.3 LOW Blast Radius Files

Files with limited callers, safe to modify.

| File | LOC | Callers | Risk |
|------|-----|---------|------|
| `rollout_projection.py` | 716 | 1 | LOW |
| `keys_service.py` | 380 | 1 | LOW |
| `pdf_renderer.py` | 679 | 1 | LOW |
| `certificate.py` | 200 | 1 | LOW |

---

## Section 8: Consolidation Plan

### 8.1 Phase 1: Critical Duplicate (Week 1)

| Task | Files | Risk | Savings |
|------|-------|------|---------|
| Consolidate ValidatorService | 2 | MEDIUM | 1,060 LOC |
| Create shared validators module | 1 new | LOW | - |
| Update imports in callers | 4 | LOW | - |

### 8.2 Phase 2: Base Service Classes (Week 2-3)

| Task | Files | Risk | Savings |
|------|-------|------|---------|
| Create BaseTenantReadService | 1 new | MEDIUM | - |
| Migrate IncidentReadService | 1 | LOW | 150 LOC |
| Migrate LogsReadService | 1 | LOW | 150 LOC |
| Migrate remaining 6 read services | 6 | LOW | 1,000 LOC |
| Create BaseTenantWriteService | 1 new | MEDIUM | - |
| Migrate 5 write services | 5 | MEDIUM | 550 LOC |

### 8.3 Phase 3: Utilities (Week 4)

| Task | Files | Risk | Savings |
|------|-------|------|---------|
| Create EventEmitter utility | 1 new | LOW | - |
| Migrate 11 event emission locations | 11 | LOW | 230 LOC |
| Create TenantQueryBuilder | 1 new | LOW | - |
| Migrate 12 query locations | 12 | LOW | 550 LOC |

### 8.4 Total Consolidation Impact

| Phase | LOC Saved | Files Modified | New Files |
|-------|-----------|----------------|-----------|
| Phase 1 | 1,060 | 6 | 1 |
| Phase 2 | 1,850 | 14 | 2 |
| Phase 3 | 780 | 23 | 2 |
| **TOTAL** | **3,690** | **43** | **5** |

---

## Section 9: Recommended Shared Module Structure

```
backend/app/houseofcards/shared/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── base_read_service.py       # BaseTenantReadService<T>
│   ├── base_write_service.py      # BaseTenantWriteService<T>
│   └── transaction_mixin.py       # Atomic transaction support
├── validators/
│   ├── __init__.py
│   └── issue_validator.py         # Consolidated ValidatorService
├── events/
│   ├── __init__.py
│   └── emitter.py                 # DomainEventEmitter
├── queries/
│   ├── __init__.py
│   └── tenant_query_builder.py    # TenantQueryBuilder
└── utils/
    ├── __init__.py
    ├── pagination.py              # Bounded pagination helpers
    └── tenancy.py                 # Tenant isolation utilities
```

---

## Section 10: Risk Assessment

### 10.1 Consolidation Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Import path breaks | HIGH | MEDIUM | Comprehensive grep before migration |
| Type hint incompatibility | MEDIUM | LOW | Test with mypy |
| Runtime behavior change | LOW | HIGH | Unit test coverage before migration |
| Circular imports | MEDIUM | MEDIUM | Careful module placement |

### 10.2 Recommended Safeguards

1. **Before Each Migration:**
   - Run full test suite
   - Document all callers with `grep -r`
   - Create rollback branch

2. **During Migration:**
   - Migrate one file at a time
   - Run tests after each file
   - Keep old imports as deprecation aliases

3. **After Migration:**
   - Remove deprecation aliases after 1 sprint
   - Update documentation
   - Add linting rules to prevent re-duplication

---

## Section 11: Appendices

### Appendix A: Complete File Inventory

```
app/houseofcards/customer/
├── __init__.py                                    (10 LOC)
├── activity/
│   ├── __init__.py                                (12 LOC)
│   ├── drivers/__init__.py                        (10 LOC)
│   ├── facades/
│   │   ├── __init__.py                            (10 LOC)
│   │   └── activity_facade.py                     (1,490 LOC)
│   ├── engines/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── signal_feedback_service.py             (~150 LOC)
│   │   ├── pattern_detection_service.py           (~150 LOC)
│   │   ├── cost_analysis_service.py               (~100 LOC)
│   │   ├── attention_ranking_service.py           (~100 LOC)
│   │   └── signal_identity.py                     (~100 LOC)
│   └── schemas/__init__.py                        (10 LOC)
├── incidents/
│   ├── __init__.py                                (12 LOC)
│   ├── drivers/__init__.py                        (10 LOC)
│   ├── facades/
│   │   ├── __init__.py                            (10 LOC)
│   │   └── incidents_facade.py                    (1,103 LOC)
│   ├── engines/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── incident_engine.py                     (1,011 LOC)
│   │   ├── recovery_rule_engine.py                (789 LOC)
│   │   ├── postmortem_service.py                  (~300 LOC)
│   │   ├── incident_write_service.py              (284 LOC)
│   │   ├── incident_read_service.py               (200 LOC)
│   │   ├── incident_aggregator.py                 (~250 LOC)
│   │   ├── llm_failure_service.py                 (~200 LOC)
│   │   ├── recurrence_analysis_service.py         (~200 LOC)
│   │   ├── recovery_evaluation_engine.py          (~200 LOC)
│   │   └── incident_pattern_service.py            (~200 LOC)
│   └── schemas/__init__.py                        (10 LOC)
├── policies/
│   ├── __init__.py                                (12 LOC)
│   ├── drivers/__init__.py                        (10 LOC)
│   ├── facades/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── policies_facade.py                     (1,496 LOC)
│   │   ├── run_governance_facade.py               (~500 LOC)
│   │   ├── governance_facade.py                   (~400 LOC)
│   │   ├── limits_facade.py                       (~300 LOC)
│   │   └── controls_facade.py                     (~300 LOC)
│   ├── engines/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── lessons_engine.py                      (1,209 LOC)
│   │   ├── policy_graph_engine.py                 (895 LOC)
│   │   ├── eligibility_engine.py                  (828 LOC)
│   │   ├── policy_violation_service.py            (819 LOC)
│   │   ├── llm_threshold_service.py               (812 LOC)
│   │   ├── validator_service.py                   (730 LOC) ← DUPLICATE
│   │   ├── policy_proposal.py                     (693 LOC)
│   │   ├── snapshot_service.py                    (~300 LOC)
│   │   ├── budget_enforcement_engine.py           (~300 LOC)
│   │   ├── policy_mapper.py                       (~200 LOC)
│   │   ├── authority_checker.py                   (~200 LOC)
│   │   ├── claim_decision_engine.py               (~200 LOC)
│   │   ├── customer_policy_read_service.py        (~200 LOC)
│   │   ├── policy_rules_service.py                (~200 LOC)
│   │   ├── hallucination_detector.py              (~200 LOC)
│   │   ├── policy_limits_service.py               (~200 LOC)
│   │   ├── mapper.py                              (~150 LOC)
│   │   ├── simulation_service.py                  (~150 LOC)
│   │   ├── llm_policy_engine.py                   (~150 LOC)
│   │   ├── override_service.py                    (~150 LOC)
│   │   └── control_registry.py                    (~100 LOC)
│   ├── controls/
│   │   └── engines/
│   │       ├── customer_killswitch_read_service.py (~200 LOC)
│   │       ├── degraded_mode_checker.py           (675 LOC)
│   │       └── runtime_switch.py                  (~200 LOC)
│   └── schemas/__init__.py                        (10 LOC)
├── account/
│   ├── __init__.py                                (12 LOC)
│   ├── drivers/__init__.py                        (10 LOC)
│   ├── facades/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── accounts_facade.py                     (1,307 LOC)
│   │   └── notifications_facade.py                (~300 LOC)
│   ├── engines/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── profile.py                             (~200 LOC)
│   │   ├── identity_resolver.py                   (~200 LOC)
│   │   ├── user_write_service.py                  (~200 LOC)
│   │   ├── email_verification.py                  (~150 LOC)
│   │   └── tenant_service.py                      (~200 LOC)
│   ├── notifications/engines/
│   │   └── channel_service.py                     (1,097 LOC)
│   ├── support/CRM/engines/
│   │   ├── validator_service.py                   (730 LOC) ← DUPLICATE
│   │   ├── job_executor.py                        (~300 LOC)
│   │   └── audit_service.py                       (885 LOC)
│   └── schemas/__init__.py                        (10 LOC)
├── logs/
│   ├── __init__.py                                (12 LOC)
│   ├── drivers/__init__.py                        (10 LOC)
│   ├── facades/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── logs_facade.py                         (1,591 LOC)
│   │   ├── trace_facade.py                        (~400 LOC)
│   │   └── evidence_facade.py                     (~300 LOC)
│   ├── engines/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── evidence_report.py                     (1,151 LOC)
│   │   ├── pdf_renderer.py                        (679 LOC)
│   │   ├── audit_evidence.py                      (663 LOC)
│   │   ├── logs_read_service.py                   (207 LOC)
│   │   ├── reconciler.py                          (~300 LOC)
│   │   ├── export_bundle_service.py               (~300 LOC)
│   │   ├── certificate.py                         (~200 LOC)
│   │   ├── replay_determinism.py                  (~200 LOC)
│   │   ├── store.py                               (~300 LOC)
│   │   ├── completeness_checker.py                (~200 LOC)
│   │   └── durability.py                          (~200 LOC)
│   └── schemas/
│       ├── __init__.py                            (10 LOC)
│       └── models.py                              (~100 LOC)
├── integrations/
│   ├── __init__.py                                (12 LOC)
│   ├── drivers/__init__.py                        (10 LOC)
│   ├── facades/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── integrations_facade.py                 (~500 LOC)
│   │   ├── datasources_facade.py                  (~300 LOC)
│   │   ├── retrieval_facade.py                    (~300 LOC)
│   │   └── connectors_facade.py                   (~300 LOC)
│   ├── engines/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── connector_registry.py                  (822 LOC)
│   │   ├── http_connector.py                      (~400 LOC)
│   │   ├── server_registry.py                     (~300 LOC)
│   │   ├── retrieval_mediator.py                  (~300 LOC)
│   │   ├── external_response_service.py           (~200 LOC)
│   │   ├── mcp_connector.py                       (~300 LOC)
│   │   ├── sql_gateway.py                         (~300 LOC)
│   │   └── cus_integration_service.py             (~200 LOC)
│   ├── vault/engines/
│   │   ├── cus_credential_service.py              (~300 LOC)
│   │   ├── service.py                             (~200 LOC)
│   │   └── vault.py                               (742 LOC)
│   └── schemas/
│       ├── __init__.py                            (10 LOC)
│       └── datasource_model.py                    (~100 LOC)
├── analytics/
│   ├── __init__.py                                (12 LOC)
│   ├── drivers/__init__.py                        (10 LOC)
│   ├── facades/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── analytics_facade.py                    (828 LOC)
│   │   └── detection_facade.py                    (~300 LOC)
│   ├── engines/
│   │   ├── __init__.py                            (10 LOC)
│   │   ├── cost_anomaly_detector.py               (1,183 LOC)
│   │   ├── cost_write_service.py                  (225 LOC)
│   │   ├── cost_model_engine.py                   (~300 LOC)
│   │   ├── pattern_detection.py                   (~200 LOC)
│   │   └── prediction.py                          (~200 LOC)
│   └── schemas/__init__.py                        (10 LOC)
├── api_keys/
│   ├── __init__.py                                (12 LOC)
│   ├── drivers/__init__.py                        (10 LOC)
│   ├── facades/
│   │   ├── __init__.py                            (10 LOC)
│   │   └── api_keys_facade.py                     (~300 LOC)
│   ├── engines/
│   │   ├── __init__.py                            (10 LOC)
│   │   └── keys_service.py                        (~200 LOC)
│   └── schemas/__init__.py                        (10 LOC)
├── overview/
│   ├── __init__.py                                (12 LOC)
│   ├── drivers/__init__.py                        (10 LOC)
│   ├── facades/
│   │   ├── __init__.py                            (10 LOC)
│   │   └── overview_facade.py                     (715 LOC)
│   ├── engines/__init__.py                        (10 LOC)
│   └── schemas/__init__.py                        (10 LOC)
└── general/
    ├── __init__.py                                (57 LOC)
    ├── drivers/__init__.py                        (10 LOC)
    ├── facades/
    │   ├── __init__.py                            (10 LOC)
    │   ├── lifecycle_facade.py                    (700 LOC)
    │   ├── alerts_facade.py                       (670 LOC)
    │   ├── scheduler_facade.py                    (~550 LOC)
    │   ├── monitors_facade.py                     (~540 LOC)
    │   └── compliance_facade.py                   (~510 LOC)
    ├── engines/
    │   ├── __init__.py                            (10 LOC)
    │   ├── knowledge_sdk.py                       (971 LOC) ← LAYER VIOLATION
    │   ├── knowledge_lifecycle_manager.py         (908 LOC)
    │   ├── alert_log_linker.py                    (751 LOC)
    │   ├── fatigue_controller.py                  (734 LOC)
    │   ├── cus_enforcement_service.py             (667 LOC)
    │   ├── panel_invariant_monitor.py             (~450 LOC)
    │   ├── alert_emitter.py                       (~300 LOC)
    │   ├── alert_fatigue.py                       (~250 LOC)
    │   ├── cus_health_service.py                  (~300 LOC)
    │   └── cus_telemetry_service.py               (~300 LOC)
    ├── schemas/__init__.py                        (10 LOC)
    ├── runtime/engines/
    │   ├── __init__.py                            (10 LOC)
    │   ├── transaction_coordinator.py             (828 LOC)
    │   ├── governance_orchestrator.py             (799 LOC)
    │   ├── run_governance_facade.py               (~500 LOC)
    │   ├── phase_status_invariants.py             (~300 LOC)
    │   ├── plan_generation_engine.py              (~350 LOC)
    │   └── constraint_checker.py                  (~300 LOC)
    ├── lifecycle/engines/
    │   ├── execution.py                           (1,312 LOC)
    │   ├── onboarding.py                          (695 LOC)
    │   ├── pool_manager.py                        (599 LOC)
    │   ├── knowledge_plane.py                     (468 LOC)
    │   ├── offboarding.py                         (~350 LOC)
    │   └── base.py                                (310 LOC)
    ├── controls/engines/
    │   ├── __init__.py                            (10 LOC)
    │   └── guard_write_service.py                 (249 LOC) ← TEMPORARY
    ├── ui/engines/
    │   └── rollout_projection.py                  (716 LOC)
    ├── workflow/contracts/engines/
    │   └── contract_service.py                    (707 LOC)
    └── cross-domain/engines/
        └── cross_domain.py                        (497 LOC)
```

### Appendix B: Cross-Domain Import Matrix

| From Domain | Imports From |
|-------------|--------------|
| activity | models.runs, models.traces |
| incidents | models.killswitch, services.logs |
| policies | models.policies, models.contract |
| account | models.users, models.tenants |
| logs | models.traces, traces.pg_store |
| integrations | models.integrations, connectors |
| analytics | db.cost_models |
| api_keys | models.api_keys |
| overview | facades.* (all domains) |
| general | models.contract, services.governance, ALL |

### Appendix C: Invariant Registry

| Domain | Invariant ID | Rule |
|--------|--------------|------|
| general | GOV-001 | MAY_NOT is un-overridable |
| general | GOV-002 | Governance must throw |
| general | SEP-001 | Orchestrators decide, never execute |
| general | SEP-002 | Executors execute, never decide |
| general | SEP-003 | Projections read, never mutate |
| general | LCY-001 | Stage handlers are dumb plugins |
| general | CON-001 | Status transitions follow state machine |
| general | CON-002 | APPROVED requires approved_by |
| general | CON-003 | ACTIVE requires job exists |
| general | CON-004 | COMPLETED requires audit_verdict = PASS |
| general | CON-005 | Terminal states are immutable |
| general | CON-006 | proposed_changes must validate schema |
| general | CON-007 | confidence_score range [0,1] |
| general | ROLLOUT-001 | Projection is read-only |
| general | ROLLOUT-002 | Stage advancement requires audit PASS |
| policies | VAL-001 | Validator is stateless (no writes) |
| policies | VAL-002 | Verdicts include version |
| policies | VAL-003 | Confidence in [0,1] |
| policies | VAL-004 | Unknown type defers |
| policies | VAL-005 | Escalation always escalates |
| incidents | INC-001 | Incidents are tenant-isolated |
| incidents | INC-002 | Status transitions are audited |
| logs | LOG-001 | Traces are immutable |
| logs | LOG-002 | Evidence is tamper-evident |

---

## Changes Log

| Date | Change |
|------|--------|
| 2026-01-22 | Initial consolidation report created |
| 2026-01-22 | Documented 2 critical duplicates (ValidatorService) |
| 2026-01-22 | Documented 8 read service pattern duplicates |
| 2026-01-22 | Documented 5 write service pattern duplicates |
| 2026-01-22 | Documented 11 event emission duplicates |
| 2026-01-22 | Created consolidation plan (3 phases) |
| 2026-01-22 | Estimated savings: 3,690 LOC across 43 files |

---

## References

| Reference | Document |
|-----------|----------|
| PIN-250 | Phase 2B Extraction |
| PIN-281 | L3 Adapter Closure |
| PIN-287 | Validator Logic |
| PIN-413 | Logs Domain Audit Ledger |
| HOC_general_domain_constitution_v1.md | General Domain Constitution |
| HOC_general_detailed_report_v1.md | General Domain Detailed Report |
| HOC_general_analysis_v1.md | General Domain Analysis |
