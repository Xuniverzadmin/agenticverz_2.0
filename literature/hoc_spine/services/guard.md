# guard.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/guard.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            guard.py
Lives in:        services/
Role:            Services
Inbound:         API routes, engines
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Guard Console Data Contracts - Customer-Facing API
Violations:      none
```

## Purpose

Guard Console Data Contracts - Customer-Facing API

DOMAIN: Customer Console (/guard/*)
AUDIENCE: Customers (tenant-scoped access)
AUTH: aud="console", requires org_id

These contracts are FROZEN as of M29. Changes require:
1. Deprecation annotation
2. 2-version grace period
3. PIN documentation

INVARIANTS:
- All responses are tenant-scoped (no cross-tenant data)
- No founder-only fields (those belong in ops.py)
- Times are ISO8601 strings
- IDs are prefixed strings (inc_, key_, etc.)

## Import Analysis

**External:**
- `pydantic`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `GuardStatusDTO(BaseModel)`

GET /guard/status response.

Tells customer if their traffic is protected.
Frozen: 2025-12-23 (M29)

### `TodaySnapshotDTO(BaseModel)`

GET /guard/snapshot/today response.

Today's metrics at a glance.
Frozen: 2025-12-23 (M29)

### `IncidentSummaryDTO(BaseModel)`

Incident list item.

Used in GET /guard/incidents (list) and detail views.
Frozen: 2025-12-23 (M29)

### `IncidentEventDTO(BaseModel)`

Timeline event within an incident.

### `IncidentDetailDTO(BaseModel)`

GET /guard/incidents/{id} response.

Full incident with timeline.
Frozen: 2025-12-23 (M29)

### `IncidentListDTO(BaseModel)`

GET /guard/incidents response (paginated).

Frozen: 2025-12-23 (M29)

### `CustomerIncidentImpactDTO(BaseModel)`

Impact assessment for customers - calm, explicit.

Frozen: 2025-12-24 (M29 Category 5)

### `CustomerIncidentResolutionDTO(BaseModel)`

Resolution status for customers - reassuring.

Frozen: 2025-12-24 (M29 Category 5)

### `CustomerIncidentActionDTO(BaseModel)`

Customer action item - only if necessary.

Frozen: 2025-12-24 (M29 Category 5)

### `CustomerIncidentNarrativeDTO(BaseModel)`

GET /guard/incidents/{id} enhanced response.

Customer-friendly incident detail with calm narrative.
Answers: What happened? Did it affect me? Is it fixed? Do I need to act?

Frozen: 2025-12-24 (M29 Category 5)

IMPORTANT: This is CUSTOMER-ONLY data.
- Uses calm vocabulary (normal, rising, protected, resolved)
- No internal terminology (no policy names, no thresholds)
- No cross-tenant data (no affected_tenants, no percentiles)

### `ApiKeyDTO(BaseModel)`

API key response (masked).

GET /guard/keys response item.
Frozen: 2025-12-23 (M29)

### `ApiKeyListDTO(BaseModel)`

GET /guard/keys response.

### `GuardrailConfigDTO(BaseModel)`

Individual guardrail configuration.

### `TenantSettingsDTO(BaseModel)`

GET /guard/settings response.

Read-only tenant configuration view.
Frozen: 2025-12-23 (M29)

### `ReplayCallSnapshotDTO(BaseModel)`

Original call context for replay.

### `ReplayCertificateDTO(BaseModel)`

Cryptographic proof of replay (M23).

### `ReplayResultDTO(BaseModel)`

POST /guard/replay/{call_id} response.

Result of replaying a call with determinism validation.
Frozen: 2025-12-23 (M29)

### `KillSwitchActionDTO(BaseModel)`

POST /guard/killswitch/activate and /deactivate response.

Frozen: 2025-12-23 (M29)

### `OnboardingVerifyResponseDTO(BaseModel)`

POST /guard/onboarding/verify response.

Frozen: 2025-12-23 (M29)

### `CustomerCostSummaryDTO(BaseModel)`

GET /guard/costs/summary response.

Customer cost summary with trend and projection.
Frozen: 2025-12-23 (M29 Category 4)

THE INVARIANT: All values derive from complete snapshots, never live data.
Customer sees their own tenant data only - no cross-tenant leakage.

### `CostBreakdownItemDTO(BaseModel)`

Individual cost breakdown item.

### `CustomerCostExplainedDTO(BaseModel)`

GET /guard/costs/explained response.

Explains WHY costs are what they are.
Frozen: 2025-12-23 (M29 Category 4)

IMPORTANT: Does not expose founder-only fields like churn_risk or affected_tenants.

### `CustomerCostIncidentDTO(BaseModel)`

Cost-related incident visible to customer.

Used in GET /guard/costs/incidents response.
Frozen: 2025-12-23 (M29 Category 4)

IMPORTANT: Uses calm vocabulary (protected, attention_needed).
Does not expose severity levels - maps internally.

### `CustomerCostIncidentListDTO(BaseModel)`

GET /guard/costs/incidents response.

## Domain Usage

**Callers:** API routes, engines

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: GuardStatusDTO
      methods: []
      consumers: ["orchestrator"]
    - name: TodaySnapshotDTO
      methods: []
      consumers: ["orchestrator"]
    - name: IncidentSummaryDTO
      methods: []
      consumers: ["orchestrator"]
    - name: IncidentEventDTO
      methods: []
      consumers: ["orchestrator"]
    - name: IncidentDetailDTO
      methods: []
      consumers: ["orchestrator"]
    - name: IncidentListDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CustomerIncidentImpactDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CustomerIncidentResolutionDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CustomerIncidentActionDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CustomerIncidentNarrativeDTO
      methods: []
      consumers: ["orchestrator"]
    - name: ApiKeyDTO
      methods: []
      consumers: ["orchestrator"]
    - name: ApiKeyListDTO
      methods: []
      consumers: ["orchestrator"]
    - name: GuardrailConfigDTO
      methods: []
      consumers: ["orchestrator"]
    - name: TenantSettingsDTO
      methods: []
      consumers: ["orchestrator"]
    - name: ReplayCallSnapshotDTO
      methods: []
      consumers: ["orchestrator"]
    - name: ReplayCertificateDTO
      methods: []
      consumers: ["orchestrator"]
    - name: ReplayResultDTO
      methods: []
      consumers: ["orchestrator"]
    - name: KillSwitchActionDTO
      methods: []
      consumers: ["orchestrator"]
    - name: OnboardingVerifyResponseDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CustomerCostSummaryDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CostBreakdownItemDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CustomerCostExplainedDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CustomerCostIncidentDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CustomerCostIncidentListDTO
      methods: []
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['pydantic']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

