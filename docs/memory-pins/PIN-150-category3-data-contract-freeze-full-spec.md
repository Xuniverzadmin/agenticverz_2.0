# PIN-150: Category 3 Data Contract Freeze - Full Spec Implementation

**Status:** ✅ COMPLETE
**Category:** API / Contracts
**Created:** 2025-12-23
**Milestone:** M29 Transition
**Related:** [PIN-148](PIN-148-m29-categorical-next-steps.md), [PIN-149](PIN-149-category2-auth-boundary-full-spec.md)

---

## Overview

This PIN documents the full implementation of Category 3: Data Contract Freeze per the M29 transition spec. The implementation establishes frozen API contracts with explicit DTOs, namespace separation, and CI enforcement.

---

## The Invariants

1. **Field names NEVER change** (use deprecation instead)
2. **Required fields NEVER become optional** (would break clients)
3. **Types NEVER widen** (`int` → `float` is FORBIDDEN)
4. **New optional fields MAY be added** (backward compatible)
5. **Removal requires 2-version deprecation cycle**

---

## Contract Version

```python
CONTRACT_VERSION = "1.0.0"
CONTRACT_FROZEN_AT = "2025-12-23"
```

---

## Domain Separation

| Domain | URL Prefix | Audience | Auth | Vocabulary |
|--------|------------|----------|------|------------|
| Guard | `/guard/*` | Customers | `aud=console` | Calm: `protected`, `attention_needed`, `action_required` |
| Ops | `/ops/*` | Founders | `aud=fops`, `mfa=true` | Command: `stable`, `elevated`, `degraded`, `critical` |

**CRITICAL:** These domains MUST NOT share response models.

---

## Guard Console DTOs (8 Models)

| DTO | Endpoint | Key Fields |
|-----|----------|------------|
| `GuardStatusDTO` | GET /guard/status | status, is_frozen, incidents_blocked_24h, active_guardrails |
| `TodaySnapshotDTO` | GET /guard/snapshot/today | requests_today, spend_today_cents, incidents_prevented |
| `IncidentSummaryDTO` | GET /guard/incidents | id, title, severity, status, trigger_type, calls_affected |
| `IncidentDetailDTO` | GET /guard/incidents/{id} | incident, timeline |
| `ApiKeyDTO` | GET /guard/keys | id, name, prefix, is_frozen, scopes |
| `TenantSettingsDTO` | GET /guard/settings | tenant_id, guardrails, notification_email |
| `ReplayResultDTO` | POST /guard/replay/{call_id} | success, determinism_level, certificate |
| `KillSwitchActionDTO` | POST /guard/killswitch/* | success, action, message |

### Example: GuardStatusDTO

```json
{
  "status": "protected",
  "is_frozen": false,
  "frozen_at": null,
  "frozen_by": null,
  "incidents_blocked_24h": 3,
  "active_guardrails": ["cost_limit", "rate_limit"],
  "last_incident_time": "2025-12-23T10:15:00Z"
}
```

---

## Ops Console DTOs (8 Models)

| DTO | Endpoint | Key Fields |
|-----|----------|------------|
| `SystemPulseDTO` | GET /ops/pulse | status, active_customers, incidents_24h, revenue_today_cents |
| `CustomerSegmentDTO` | GET /ops/customers | tenant_id, stickiness_delta, mrr_cents, churn_risk_score |
| `CustomerAtRiskDTO` | GET /ops/customers/at-risk | tenant_id, risk_level, risk_signals, suggested_action |
| `IncidentPatternDTO` | GET /ops/incidents/patterns | pattern_type, affected_tenants, is_systemic |
| `StickinessByFeatureDTO` | GET /ops/stickiness | feature_name, retention_correlation, is_sticky |
| `RevenueRiskDTO` | GET /ops/revenue | mrr_cents, concentration_risk, at_risk_mrr_cents |
| `InfraLimitsDTO` | GET /ops/infra | db_connections_percent, bottleneck, headroom_percent |
| `PlaybookDTO` | GET /ops/playbooks | id, name, trigger_conditions, actions |

### Example: SystemPulseDTO

```json
{
  "status": "stable",
  "active_customers": 42,
  "incidents_24h": 3,
  "incidents_7d": 15,
  "revenue_today_cents": 125000,
  "revenue_7d_cents": 875000,
  "error_rate_percent": 0.02,
  "p99_latency_ms": 145,
  "customers_at_risk": 2,
  "last_updated": "2025-12-23T10:15:00Z"
}
```

---

## Absence Tests

### Cross-Domain Import Prevention

```python
# FORBIDDEN in guard.py:
from app.contracts.ops import CustomerSegmentDTO  # ❌

# FORBIDDEN in ops.py:
from app.contracts.guard import IncidentSummaryDTO  # ❌
```

### Founder-Only Fields in Guard

```python
# FORBIDDEN in any Guard DTO:
class GuardStatusDTO:
    churn_risk_score: float  # ❌ founder only
    stickiness_delta: float  # ❌ founder only
    affected_tenants: int    # ❌ cross-tenant
```

### Customer Data in Ops Aggregations

```python
# FORBIDDEN - exposes individual customer data:
class IncidentPatternDTO:
    affected_tenant_ids: List[str]  # ❌
```

---

## CI Guardrails

18 tests in `test_category3_data_contracts.py`:

```
TestContractNamespaceSeparation:
  - test_guard_does_not_import_ops ✅
  - test_ops_does_not_import_guard ✅
  - test_common_has_no_domain_types ✅

TestGuardContractInvariants:
  - test_guard_status_has_required_fields ✅
  - test_guard_status_types_are_strict ✅
  - test_incident_summary_has_id_prefix_constraint ✅
  - test_guard_no_founder_only_fields ✅

TestOpsContractInvariants:
  - test_system_pulse_has_required_fields ✅
  - test_system_pulse_status_is_command_vocabulary ✅
  - test_customer_segment_has_global_metrics ✅
  - test_incident_pattern_has_cross_tenant_fields ✅

TestNoSharedResponseModels:
  - test_guard_api_uses_guard_contracts ✅
  - test_ops_api_uses_ops_contracts ✅

TestVocabularySeparation:
  - test_guard_uses_calm_status_vocabulary ✅
  - test_ops_uses_command_status_vocabulary ✅

TestContractVersioning:
  - test_contract_version_exists ✅
  - test_contract_version_is_semver ✅
  - test_frozen_date_is_iso ✅
```

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/app/contracts/__init__.py` | Contract module with version 1.0.0 |
| `backend/app/contracts/guard.py` | Guard console DTOs (8 models) |
| `backend/app/contracts/ops.py` | Ops console DTOs (8 models) |
| `backend/app/contracts/common.py` | Shared infrastructure types (HealthDTO, ErrorDTO) |
| `backend/tests/test_category3_data_contracts.py` | CI guardrails (18 tests) |
| `docs/DATA_CONTRACT_FREEZE.md` | Complete contract documentation |

---

## DATA_CONTRACT_FREEZE.md

Created comprehensive documentation including:
- All frozen contracts with JSON examples
- Field type constraints
- Change process (add optional, deprecation cycle)
- Forbidden patterns (cross-domain imports, type widening)
- Version history

---

## Change Process

### Adding New Optional Fields ✅

```python
class GuardStatusDTO(BaseModel):
    # Existing fields...
    new_field: Optional[str] = None  # ✅ OK - backward compatible
```

### Changing Field Types ❌

```python
# FORBIDDEN
incidents_blocked_24h: float  # Was int, now float ❌
```

### Removing Fields

1. Mark as `deprecated=True`
2. Keep for 2 versions
3. Remove after deprecation cycle

---

## Exit Criteria (ALL MET)

| Criterion | Status |
|-----------|--------|
| Explicit DTOs for /guard/* | ✅ (8 DTOs) |
| Explicit DTOs for /ops/* | ✅ (8 DTOs) |
| API namespace separation | ✅ (calm vs command vocabulary) |
| Absence tests (no cross-pollution) | ✅ (6 tests) |
| DATA_CONTRACT_FREEZE.md created | ✅ |
| CI guardrails for violations | ✅ (18 tests) |
| Contract version tracking | ✅ (1.0.0) |

---

## Database Contract Status

```bash
$ alembic current
047_m27_snapshots (head)

$ alembic heads
047_m27_snapshots (head)

$ alembic branches
(empty - no branches)
```

- 48 migration files total (001-047 + initial)
- Single linear history (no merge conflicts)
- Database in sync with codebase

---

## Related Documents

- [PIN-148](PIN-148-m29-categorical-next-steps.md) - M29 Categorical Next Steps
- [PIN-149](PIN-149-category2-auth-boundary-full-spec.md) - Category 2 Auth Boundary
- [DATA_CONTRACT_FREEZE.md](../DATA_CONTRACT_FREEZE.md) - Contract documentation
- [backend/app/contracts/](../../backend/app/contracts/) - Contract implementations
- [backend/tests/test_category3_data_contracts.py](../../backend/tests/test_category3_data_contracts.py) - Tests
