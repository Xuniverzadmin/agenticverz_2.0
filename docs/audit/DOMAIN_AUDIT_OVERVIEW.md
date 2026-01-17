# OVERVIEW Domain API Audit

**Created:** 2026-01-16
**Domain:** OVERVIEW
**Subdomain:** SUMMARY
**Topics:** HIGHLIGHTS, DECISIONS, COST_INTELLIGENCE

---

## Available Endpoints (Customer-Facing)

| Endpoint | File | Full Path | Auth |
|----------|------|-----------|------|
| `/overview/highlights` | `runtime_projections/overview/router.py:157` | `/api/v1/runtime/overview/highlights` | Tenant Auth |
| `/overview/decisions` | `runtime_projections/overview/router.py:271` | `/api/v1/runtime/overview/decisions` | Tenant Auth |
| `/overview/costs` | `runtime_projections/overview/router.py:394` | `/api/v1/runtime/overview/costs` | Tenant Auth |
| `/api/v1/activity/summary` | `activity.py:231` | `/api/v1/activity/summary` | No explicit auth |

**Note:** The Overview router (`router.py`) uses `prefix="/overview"` and is mounted under `/api/v1/runtime` in main.py, giving full paths `/api/v1/runtime/overview/*`.

---

## Architectural Note

**Overview is a PROJECTION-ONLY domain:**
- Overview DOES NOT own any tables
- Overview aggregates/projects from existing domains (incidents, policy_proposals, limit_breaches, audit_ledger, worker_runs)
- All endpoints are READ-ONLY
- No write paths, no queues, no state transitions

---

## Panel → Endpoint Mapping

### Topic: HIGHLIGHTS (OVR-SUM-HL-*)

| Panel | Expected Endpoint | Status | Issue |
|-------|-------------------|--------|-------|
| OVR-SUM-HL-O1 | `/api/v1/activity/summary` | ⚠️ WRONG ENDPOINT | Should use `/api/v1/runtime/overview/highlights` |
| OVR-SUM-HL-O2 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/highlights` |
| OVR-SUM-HL-O4 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/highlights` |

### Topic: DECISIONS (OVR-SUM-DC-*)

| Panel | Expected Endpoint | Status | Issue |
|-------|-------------------|--------|-------|
| OVR-SUM-DC-O1 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/decisions` |
| OVR-SUM-DC-O2 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/decisions` |
| OVR-SUM-DC-O3 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/decisions` |
| OVR-SUM-DC-O4 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/decisions` |

### Topic: COST_INTELLIGENCE (OVR-SUM-CI-*)

| Panel | Expected Endpoint | Status | Issue |
|-------|-------------------|--------|-------|
| OVR-SUM-CI-O1 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/costs` |
| OVR-SUM-CI-O2 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/costs` |
| OVR-SUM-CI-O3 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/costs` |
| OVR-SUM-CI-O4 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/overview/costs` |

---

## Summary

| Category | Count | Details |
|----------|-------|---------|
| ✅ Correct | 0 | None |
| ⚠️ Wrong Endpoint | 1 | OVR-SUM-HL-O1 (points to activity.py, not overview projection) |
| ⚠️ Needs Binding | 10 | All panels have `null` endpoint except OVR-SUM-HL-O1 |
| ⛔ Scope Violation | 0 | None (Overview router is properly customer-facing) |

**Total Panels:** 11
**Issues:** 11 (all need endpoint fixes)

---

## Key Finding: Overview Runtime Projection Not Wired

The Overview domain has a proper runtime projection router at `/api/v1/runtime/overview/*` with three endpoints:

| Endpoint | Response Model | Purpose |
|----------|---------------|---------|
| `/api/v1/runtime/overview/highlights` | `CrossDomainHighlightsResponse` | System pulse + domain counts |
| `/api/v1/runtime/overview/decisions` | `DecisionsQueueResponse` | Pending decisions queue |
| `/api/v1/runtime/overview/costs` | `CostIntelligenceResponse` | Cost intelligence snapshot |

**But no intent YAMLs point to these endpoints.**

---

## Response Models (From router.py)

### CrossDomainHighlightsResponse (for HIGHLIGHTS panels)

```python
class CrossDomainHighlightsResponse(BaseModel):
    pulse: SystemPulse        # status, active_incidents, pending_decisions, recent_breaches
    domain_counts: List[DomainCount]  # per-domain counts
    last_activity_at: Optional[datetime]
```

### DecisionsQueueResponse (for DECISIONS panels)

```python
class DecisionsQueueResponse(BaseModel):
    items: List[DecisionItem]  # source_domain, entity_type, entity_id, decision_type, priority, summary
    total: int
    has_more: bool
```

### CostIntelligenceResponse (for COST_INTELLIGENCE panels)

```python
class CostIntelligenceResponse(BaseModel):
    currency: str            # Always "USD"
    period: CostPeriod       # start, end
    actuals: CostActuals     # llm_run_cost
    limits: List[LimitCostItem]  # budget limits with status
    violations: CostViolations   # breach_count, total_overage
```

---

## Recommended Actions

### 1. Fix OVR-SUM-HL-O1 (Wrong Endpoint)

| Panel | Current | Fix To |
|-------|---------|--------|
| OVR-SUM-HL-O1 | `/api/v1/activity/summary` | `/api/v1/runtime/overview/highlights` |

### 2. Bind All HIGHLIGHTS Panels

```yaml
capability:
  assumed_endpoint: /api/v1/runtime/overview/highlights
  assumed_method: GET
```

Affected panels: OVR-SUM-HL-O1, O2, O4

### 3. Bind All DECISIONS Panels

```yaml
capability:
  assumed_endpoint: /api/v1/runtime/overview/decisions
  assumed_method: GET
```

Affected panels: OVR-SUM-DC-O1, O2, O3, O4

### 4. Bind All COST_INTELLIGENCE Panels

```yaml
capability:
  assumed_endpoint: /api/v1/runtime/overview/costs
  assumed_method: GET
```

Affected panels: OVR-SUM-CI-O1, O2, O3, O4

---

## Affected Intent YAMLs (11 total)

```
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-DC-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-DC-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-DC-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-DC-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-CI-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-CI-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-CI-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-CI-O4.yaml
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial audit created |
