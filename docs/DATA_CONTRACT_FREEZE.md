# DATA_CONTRACT_FREEZE.md

**Version:** 1.0.0
**Frozen At:** 2025-12-23
**Status:** FROZEN

---

## Overview

This document defines the **FROZEN** API data contracts for AOS (Agentic Operating System).
Once frozen, these contracts are IMMUTABLE. Changes require the deprecation process below.

---

## Contract Invariants

### 1. Immutability Rules

| Rule | Description |
|------|-------------|
| **Field names NEVER change** | Use deprecation + new field instead |
| **Required fields NEVER become optional** | Would break existing clients |
| **Types NEVER widen** | `int` → `float` is FORBIDDEN |
| **New optional fields MAY be added** | Backward compatible |
| **Removal requires deprecation** | 2-version grace period |

### 2. Domain Separation

| Domain | URL Prefix | Audience | Auth |
|--------|------------|----------|------|
| Guard | `/guard/*` | Customers | `aud=console` |
| Ops | `/ops/*` | Founders | `aud=fops`, `mfa=true` |

**CRITICAL:** These domains MUST NOT share response models.

### 3. Vocabulary Separation

| Domain | Status Vocabulary | Tone |
|--------|------------------|------|
| Guard | `protected`, `attention_needed`, `action_required` | Calm, reassuring |
| Ops | `stable`, `elevated`, `degraded`, `critical` | Command, operational |

---

## Guard Console Contracts (`/guard/*`)

### GET /guard/status

**Response: `GuardStatusDTO`**

```json
{
  "status": "protected | attention_needed | action_required",
  "is_frozen": false,
  "frozen_at": null,
  "frozen_by": null,
  "incidents_blocked_24h": 3,
  "active_guardrails": ["cost_limit", "rate_limit"],
  "last_incident_time": "2025-12-23T10:15:00Z"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| status | Literal | ✅ | Customer-facing status |
| is_frozen | bool | ✅ | Killswitch state |
| frozen_at | string? | | ISO8601 |
| frozen_by | string? | | user_id or "system" |
| incidents_blocked_24h | int | ✅ | ≥0 |
| active_guardrails | List[str] | ✅ | |
| last_incident_time | string? | | ISO8601 |

---

### GET /guard/snapshot/today

**Response: `TodaySnapshotDTO`**

```json
{
  "requests_today": 1500,
  "spend_today_cents": 2340,
  "incidents_prevented": 2,
  "last_incident_time": "2025-12-23T09:30:00Z",
  "cost_avoided_cents": 15000
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| requests_today | int | ✅ | ≥0 |
| spend_today_cents | int | ✅ | ≥0 |
| incidents_prevented | int | ✅ | ≥0 |
| last_incident_time | string? | | ISO8601 |
| cost_avoided_cents | int | ✅ | ≥0 |

---

### GET /guard/incidents

**Response: `IncidentListDTO`**

```json
{
  "incidents": [
    {
      "id": "inc_abc123",
      "title": "Cost spike detected",
      "severity": "high",
      "status": "active",
      "trigger_type": "cost_spike",
      "trigger_value": "$50",
      "action_taken": "blocked",
      "cost_avoided_cents": 5000,
      "calls_affected": 12,
      "started_at": "2025-12-23T10:00:00Z",
      "ended_at": null,
      "duration_seconds": null,
      "call_id": "call_xyz789"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

---

### GET /guard/incidents/{id}

**Response: `IncidentDetailDTO`**

```json
{
  "incident": { /* IncidentSummaryDTO */ },
  "timeline": [
    {
      "id": "evt_001",
      "event_type": "detection",
      "description": "Cost spike detected",
      "created_at": "2025-12-23T10:00:00Z",
      "data": {}
    }
  ]
}
```

---

### POST /guard/killswitch/activate

**Response: `KillSwitchActionDTO`**

```json
{
  "success": true,
  "action": "activated",
  "frozen_at": "2025-12-23T10:30:00Z",
  "message": "All traffic blocked"
}
```

---

### POST /guard/killswitch/deactivate

**Response: `KillSwitchActionDTO`**

```json
{
  "success": true,
  "action": "deactivated",
  "frozen_at": null,
  "message": "Traffic resumed"
}
```

---

### POST /guard/replay/{call_id}

**Response: `ReplayResultDTO`**

```json
{
  "success": true,
  "determinism_level": "exact | semantic | divergent",
  "original_call": {
    "call_id": "call_xyz",
    "agent_id": "agent_abc",
    "input_payload": {},
    "original_output": {},
    "timestamp": "2025-12-23T10:00:00Z"
  },
  "replay_output": {},
  "differences": [],
  "certificate": {
    "certificate_id": "cert_123",
    "algorithm": "sha256",
    "original_hash": "abc...",
    "replay_hash": "abc...",
    "match": true,
    "issued_at": "2025-12-23T10:35:00Z",
    "issuer": "agenticverz"
  }
}
```

---

### GET /guard/keys

**Response: `ApiKeyListDTO`**

```json
{
  "keys": [
    {
      "id": "key_abc",
      "name": "Production",
      "prefix": "edf7eeb8",
      "is_frozen": false,
      "frozen_at": null,
      "frozen_by": null,
      "created_at": "2025-12-01T00:00:00Z",
      "last_used_at": "2025-12-23T10:00:00Z",
      "scopes": ["read", "write"]
    }
  ],
  "total": 2
}
```

---

### GET /guard/settings

**Response: `TenantSettingsDTO`**

```json
{
  "tenant_id": "tenant_abc",
  "tenant_name": "Acme Corp",
  "guardrails": [
    {
      "name": "cost_limit",
      "enabled": true,
      "threshold": "$100/day",
      "action": "block"
    }
  ],
  "notification_email": "admin@acme.com",
  "notification_slack_webhook": "https://hooks.slack.com/...(masked)",
  "daily_budget_cents": 10000,
  "rate_limit_rpm": 1000
}
```

---

## Ops Console Contracts (`/ops/*`)

### GET /ops/pulse

**Response: `SystemPulseDTO`**

```json
{
  "status": "stable | elevated | degraded | critical",
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

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| status | Literal | ✅ | Command vocabulary |
| active_customers | int | ✅ | ≥0 |
| incidents_24h | int | ✅ | ≥0 |
| incidents_7d | int | ✅ | ≥0 |
| revenue_today_cents | int | ✅ | ≥0 |
| revenue_7d_cents | int | ✅ | ≥0 |
| error_rate_percent | float | ✅ | 0-100 |
| p99_latency_ms | int | ✅ | ≥0 |
| customers_at_risk | int | ✅ | ≥0 |
| last_updated | string | ✅ | ISO8601 |

---

### GET /ops/customers

**Response: `List[CustomerSegmentDTO]`**

```json
[
  {
    "tenant_id": "tenant_abc",
    "tenant_name": "Acme Corp",
    "segment": "enterprise",
    "status": "healthy",
    "stickiness_7d": 0.85,
    "stickiness_30d": 0.80,
    "stickiness_delta": 1.06,
    "api_calls_7d": 5000,
    "incidents_7d": 1,
    "last_activity": "2025-12-23T10:00:00Z",
    "days_since_last_login": 0,
    "mrr_cents": 50000,
    "ltv_cents": 600000,
    "churn_risk_score": 0.05,
    "top_features_used": ["replay", "guardrails"]
  }
]
```

---

### GET /ops/customers/at-risk

**Response: `List[CustomerAtRiskDTO]`**

```json
[
  {
    "tenant_id": "tenant_xyz",
    "tenant_name": "Startup Inc",
    "risk_level": "high",
    "risk_signals": ["No login in 7 days", "Stickiness declining"],
    "days_at_risk": 5,
    "last_activity": "2025-12-18T10:00:00Z",
    "suggested_action": "call",
    "mrr_cents": 5000,
    "stickiness_delta": 0.6
  }
]
```

---

### GET /ops/incidents/patterns

**Response: `List[IncidentPatternDTO]`**

```json
[
  {
    "pattern_type": "cost_spike",
    "occurrence_count": 15,
    "affected_tenants": 8,
    "first_seen": "2025-12-20T00:00:00Z",
    "last_seen": "2025-12-23T10:00:00Z",
    "is_systemic": false,
    "severity": "medium",
    "trend": "stable",
    "total_cost_impact_cents": 45000,
    "suggested_fix": "Increase default cost limit"
  }
]
```

**CRITICAL:** This is founder-only cross-tenant aggregation. NEVER expose to Guard Console.

---

### GET /ops/stickiness

**Response: `List[StickinessByFeatureDTO]`**

```json
[
  {
    "feature_name": "replay",
    "usage_count_7d": 250,
    "unique_tenants": 35,
    "retention_correlation": 0.72,
    "avg_session_depth": 3.5,
    "is_sticky": true
  }
]
```

---

### GET /ops/revenue

**Response: `RevenueRiskDTO`**

```json
{
  "mrr_cents": 500000,
  "arr_cents": 6000000,
  "revenue_7d_cents": 125000,
  "revenue_30d_cents": 500000,
  "top_customer_percent": 15.5,
  "top_3_customers_percent": 35.0,
  "concentration_risk": "medium",
  "at_risk_mrr_cents": 25000,
  "churn_rate_30d": 2.5,
  "net_revenue_retention": 105.0,
  "new_mrr_cents": 15000
}
```

---

### GET /ops/infra

**Response: `InfraLimitsDTO`**

```json
{
  "db_connections_used": 45,
  "db_connections_max": 200,
  "db_connections_percent": 22.5,
  "redis_memory_used_mb": 128,
  "redis_memory_max_mb": 512,
  "redis_memory_percent": 25.0,
  "worker_queue_depth": 12,
  "worker_concurrency": 4,
  "worker_utilization_percent": 35.0,
  "api_rate_current_rpm": 850,
  "api_rate_limit_rpm": 10000,
  "api_rate_percent": 8.5,
  "bottleneck": null,
  "headroom_percent": 65.0,
  "scale_trigger": null
}
```

---

### GET /ops/playbooks

**Response: `List[PlaybookDTO]`**

```json
[
  {
    "id": "playbook_silent_churn",
    "name": "Silent Churn Recovery",
    "trigger_conditions": [
      "API_CALL_RECEIVED in last 48h",
      "NO INCIDENT_VIEWED in 7+ days"
    ],
    "risk_level": "high",
    "applicable_count": 3,
    "actions": [
      {
        "step": 1,
        "action_type": "call",
        "description": "Direct founder call",
        "timing": "within 24h",
        "talk_track": "Hey, noticed you're still integrating..."
      }
    ]
  }
]
```

---

## Change Process

### Adding New Optional Fields

✅ **ALLOWED** - Backward compatible

1. Add field with `Optional[T] = None`
2. Update DATA_CONTRACT_FREEZE.md
3. Bump patch version (1.0.0 → 1.0.1)
4. Create PIN documenting change

### Adding New Endpoints

✅ **ALLOWED** - Backward compatible

1. Add endpoint with new DTO
2. Update DATA_CONTRACT_FREEZE.md
3. Bump minor version (1.0.0 → 1.1.0)
4. Create PIN documenting change

### Changing Field Types (FORBIDDEN)

❌ **FORBIDDEN** - Breaking change

1. Cannot change `int` to `float`
2. Cannot change `str` to `int`
3. Cannot widen type bounds

**Alternative:** Add new field with new type, deprecate old.

### Removing Fields

⚠️ **REQUIRES DEPRECATION**

1. Mark field as `deprecated=True` in schema
2. Keep for 2 versions (e.g., 1.0 → 1.1 → 1.2)
3. Remove in version 1.2
4. Create PIN for each step

### Making Required Fields Optional

❌ **FORBIDDEN** - Breaking change

**Alternative:** Field must remain required. Add new optional field if needed.

---

## Absence Constraints

The following patterns are FORBIDDEN:

### Cross-Domain Imports

```python
# FORBIDDEN in guard.py:
from app.contracts.ops import CustomerSegmentDTO

# FORBIDDEN in ops.py:
from app.contracts.guard import IncidentSummaryDTO
```

### Founder-Only Fields in Guard

```python
# FORBIDDEN in any Guard DTO:
class GuardStatusDTO:
    churn_risk_score: float  # FORBIDDEN - founder only
    stickiness_delta: float  # FORBIDDEN - founder only
    affected_tenants: int    # FORBIDDEN - cross-tenant
```

### Customer Data in Ops Aggregations

```python
# FORBIDDEN - exposes individual customer data:
class IncidentPatternDTO:
    affected_tenant_ids: List[str]  # FORBIDDEN
```

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2025-12-23 | Initial freeze (M29) |

---

## Related Documents

- [PIN-148](memory-pins/PIN-148-m29-categorical-next-steps.md) - M29 Categorical Next Steps
- [backend/app/contracts/](../backend/app/contracts/) - Contract implementations
- [tests/test_category3_data_contracts.py](../backend/tests/test_category3_data_contracts.py) - Contract tests
