# PHASE 1 — CAPABILITY INTELLIGENCE EXTRACTION
## Worked Example: Incidents Domain

**Status:** EVIDENCE-BACKED
**Date:** 2026-01-07
**Domain:** Incidents
**L2.1 Surfaces:**
- `INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS`
- `INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS`
- `INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS`

---

## OUTPUT 1 — DERIVED CAPABILITY INTELLIGENCE TABLE

### Capability: CAP-INC-LIST (List Incidents)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-INC-LIST` | Derived from adapter method |
| capability_name | List Incidents | `guard.py:494` |
| description | List incidents with pagination and filters | `customer_incidents_adapter.py:145-216` |
| mode | **READ** | No state mutation |
| scope | **BULK** | Returns paginated list |
| mutates_state | **NO** | Read-only service |
| bulk_support | **YES** | Pagination built-in (limit/offset) |
| latency_profile | **LOW** | DB query with index |
| execution_style | **SYNC** | `incident_read_service.py:56` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token only |
| adapters | `CustomerIncidentsAdapter` | `customer_incidents_adapter.py:127` |
| operators | `IncidentReadService.list_incidents()` | `incident_read_service.py:56` |
| input_contracts | `tenant_id (str, REQUIRED)`, `status`, `severity`, `from_date`, `to_date`, `limit (max 100)`, `offset` | Adapter signature |
| output_contracts | `CustomerIncidentListResponse` (items, total, page, page_size) | `customer_incidents_adapter.py:84-91` |
| side_effects | **NONE** | Pure read |
| failure_modes | `404 Tenant not found`, DB timeout | API error handling |
| observability | **YES** — API logs, DB query traces | FastAPI middleware |
| replay_feasible | **YES** | Deterministic query |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `guard.py:494-537`, `customer_incidents_adapter.py:145-216`, `incident_read_service.py:56-106` |
| risk_flags | None identified |

---

### Capability: CAP-INC-GET (Get Incident Detail)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-INC-GET` | Derived from adapter method |
| capability_name | Get Incident Detail | `guard.py:540` |
| description | Get incident detail with timeline events | `customer_incidents_adapter.py:218-277` |
| mode | **READ** | No state mutation |
| scope | **SINGLE** | Returns single incident |
| mutates_state | **NO** | Read-only |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | Two queries (incident + events) |
| execution_style | **SYNC** | Sequential DB reads |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token + tenant scope |
| adapters | `CustomerIncidentsAdapter` | `customer_incidents_adapter.py:218` |
| operators | `IncidentReadService.get_incident()`, `IncidentReadService.get_incident_events()` | `incident_read_service.py:108, 132` |
| input_contracts | `incident_id (str, REQUIRED)`, `tenant_id (str, REQUIRED)` | Adapter signature |
| output_contracts | `CustomerIncidentDetail` (incident, timeline) | `customer_incidents_adapter.py:76-82` |
| side_effects | **NONE** | Pure read |
| failure_modes | `404 Incident not found` (silent None return from adapter) | `guard.py:557-558` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `guard.py:540-591`, `customer_incidents_adapter.py:218-277`, `incident_read_service.py:108-147` |
| risk_flags | None identified |

---

### Capability: CAP-INC-ACK (Acknowledge Incident)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-INC-ACK` | Derived from adapter method |
| capability_name | Acknowledge Incident | `guard.py:594` |
| description | Mark incident as acknowledged, create timeline event | `customer_incidents_adapter.py:279-320` |
| mode | **WRITE** | State mutation |
| scope | **SINGLE** | Single entity |
| mutates_state | **YES** | Updates `status`, `acknowledged_at`, `acknowledged_by` |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | 1 read + 2 writes + commit |
| execution_style | **SYNC** | `incident_write_service.py:53` |
| reversibility | **UNKNOWN** | No explicit unacknowledge operation |
| authority_required | **HUMAN** | Console user action (GC_L routed) |
| adapters | `CustomerIncidentsAdapter` | `customer_incidents_adapter.py:279` |
| operators | `IncidentReadService.get_incident()`, `IncidentWriteService.acknowledge_incident()` | `incident_write_service.py:53-87` |
| input_contracts | `incident_id (str)`, `tenant_id (str)`, `acknowledged_by (str, default="customer")` | Adapter signature |
| output_contracts | `CustomerIncidentSummary` (status="acknowledged") | `customer_incidents_adapter.py:305-320` |
| side_effects | Creates `IncidentEvent(event_type="acknowledged")` | `incident_write_service.py:76-82` |
| failure_modes | `404 Incident not found` (None return) | Adapter check |
| observability | **YES** — Audit trail via IncidentEvent | DB persistence |
| replay_feasible | **PARTIAL** | Replay changes state, needs idempotency check |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `guard.py:594-612`, `customer_incidents_adapter.py:279-320`, `incident_write_service.py:53-87` |
| risk_flags | **REVERSIBILITY UNKNOWN** - no unacknowledge operation exists |

---

### Capability: CAP-INC-RESOLVE (Resolve Incident)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-INC-RESOLVE` | Derived from adapter method |
| capability_name | Resolve Incident | `guard.py:615` |
| description | Mark incident as resolved with optional notes | `customer_incidents_adapter.py:322-365` |
| mode | **WRITE** | State mutation |
| scope | **SINGLE** | Single entity |
| mutates_state | **YES** | Updates `status`, `resolved_at`, `resolved_by` |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | 1 read + 2 writes + commit |
| execution_style | **SYNC** | `incident_write_service.py:89` |
| reversibility | **UNKNOWN** | No explicit unresolve operation |
| authority_required | **HUMAN** | Console user action (GC_L routed) |
| adapters | `CustomerIncidentsAdapter` | `customer_incidents_adapter.py:322` |
| operators | `IncidentReadService.get_incident()`, `IncidentWriteService.resolve_incident()` | `incident_write_service.py:89-129` |
| input_contracts | `incident_id (str)`, `tenant_id (str)`, `resolved_by (str)`, `resolution_notes (Optional[str])` | Adapter signature |
| output_contracts | `CustomerIncidentSummary` (status="resolved") | `customer_incidents_adapter.py:350-365` |
| side_effects | Creates `IncidentEvent(event_type="resolved")` | `incident_write_service.py:118-124` |
| failure_modes | `404 Incident not found` (None return) | Adapter check |
| observability | **YES** — Audit trail via IncidentEvent | DB persistence |
| replay_feasible | **PARTIAL** | Replay changes state, needs idempotency |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `guard.py:615-633`, `customer_incidents_adapter.py:322-365`, `incident_write_service.py:89-129` |
| risk_flags | **REVERSIBILITY UNKNOWN** - no unresolve operation; resolution_notes could be lost if re-resolved |

---

## OUTPUT 2 — ADAPTER & OPERATOR CROSSWALK

| adapter_id | operator_name | capability_id | sync/async | side_effects | notes |
|------------|---------------|---------------|------------|--------------|-------|
| `CustomerIncidentsAdapter` | `list_incidents()` | `CAP-INC-LIST` | sync | None | Paginated list, max 100 |
| `CustomerIncidentsAdapter` | `get_incident()` | `CAP-INC-GET` | sync | None | Includes timeline events |
| `CustomerIncidentsAdapter` | `acknowledge_incident()` | `CAP-INC-ACK` | sync | Creates IncidentEvent | GC_L routed |
| `CustomerIncidentsAdapter` | `resolve_incident()` | `CAP-INC-RESOLVE` | sync | Creates IncidentEvent | GC_L routed |
| `IncidentReadService` | `list_incidents()` | `CAP-INC-LIST` | sync | None | L4 domain engine |
| `IncidentReadService` | `get_incident()` | `CAP-INC-GET` | sync | None | L4 domain engine |
| `IncidentReadService` | `get_incident_events()` | `CAP-INC-GET` | sync | None | L4 domain engine |
| `IncidentReadService` | `count_incidents_since()` | (internal) | sync | None | Used by status endpoint |
| `IncidentReadService` | `get_last_incident()` | (internal) | sync | None | Used by status endpoint |
| `IncidentWriteService` | `acknowledge_incident()` | `CAP-INC-ACK` | sync | DB commit + event | L4 domain engine |
| `IncidentWriteService` | `resolve_incident()` | `CAP-INC-RESOLVE` | sync | DB commit + event | L4 domain engine |

### Layer Architecture

```
L2 (guard.py API)
      ↓
L3 (CustomerIncidentsAdapter) — Translation + Tenant Isolation + Calm Vocabulary
      ↓
L4 (IncidentReadService / IncidentWriteService) — Domain Logic
      ↓
L6 (Incident, IncidentEvent models) — Database
```

### Calm Vocabulary Translation (L3)

| Internal Term | Customer-Safe Term | Reference |
|---------------|-------------------|-----------|
| critical | urgent | `_translate_severity()` |
| high | action | `_translate_severity()` |
| medium | attention | `_translate_severity()` |
| low | info | `_translate_severity()` |
| active | open | `_translate_status()` |
| closed | resolved | `_translate_status()` |

---

## OUTPUT 3 — CAPABILITY RISK & AMBIGUITY REPORT

### CAP-INC-LIST

**Risk Flags:** NONE

**Ambiguity:** NONE

**Confidence:** HIGH

Evidence is complete. Behavior is deterministic.

---

### CAP-INC-GET

**Risk Flags:** NONE

**Ambiguity:**
- API returns `trigger_value=None`, `duration_seconds=None`, `call_id=None` even though incident model may have these values
- L3 adapter intentionally redacts these (calm vocabulary)

**Confidence:** HIGH

Redaction is intentional per M29 governance.

---

### CAP-INC-ACK

**Risk Flags:**

1. **REVERSIBILITY UNKNOWN**
   - No `unacknowledge_incident()` method exists
   - Once acknowledged, cannot return to "open" status via customer API
   - May require Ops Console or direct DB intervention

2. **IDEMPOTENCY UNCLEAR**
   - Calling acknowledge on already-acknowledged incident: behavior undocumented
   - Does it create duplicate events? Does it update timestamp?
   - **STOP: Claude cannot determine without test evidence**

3. **REPLAY RISK**
   - Replay will change state (acknowledged_at timestamp)
   - Not idempotent without deduplication logic

**Ambiguity:**
- `acknowledged_by` defaults to "customer" but could be any string
- No validation on who can acknowledge

**Confidence:** MEDIUM

---

### CAP-INC-RESOLVE

**Risk Flags:**

1. **REVERSIBILITY UNKNOWN**
   - No `unresolve_incident()` method exists
   - Once resolved, cannot return to previous status via customer API
   - Resolution is terminal from customer perspective

2. **RESOLUTION NOTES PERSISTENCE**
   - Notes stored on incident model? Or only in event description?
   - Evidence shows event only: `description += f": {resolution_notes}"`
   - Original incident model doesn't show notes field
   - **Risk:** Notes may be lost if incident is re-resolved (though re-resolve unclear)

3. **IDEMPOTENCY UNCLEAR**
   - Same concern as CAP-INC-ACK
   - Resolving already-resolved incident: behavior undocumented

4. **REPLAY RISK**
   - Same as CAP-INC-ACK

**Ambiguity:**
- `resolution_notes` only visible in timeline event, not incident summary
- Customer may not see their own notes in the UI

**Confidence:** MEDIUM

---

## STOP CONDITIONS ENCOUNTERED

During Phase 1 extraction, the following STOP conditions were triggered:

| Condition | Capability | Resolution Required |
|-----------|------------|---------------------|
| Idempotency unclear | CAP-INC-ACK, CAP-INC-RESOLVE | Test evidence needed |
| Reversibility unclear | CAP-INC-ACK, CAP-INC-RESOLVE | Design decision required |
| Notes persistence | CAP-INC-RESOLVE | Schema verification needed |

---

## L2.1 SURFACE MAPPING

Based on Phase 1 intelligence, the mapping to L2.1 surfaces is:

| Capability ID | L2.1 Surface | Action ID | Layer Route |
|---------------|--------------|-----------|-------------|
| CAP-INC-LIST | `INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS` | `ACT-INCIDENT-LIST-VIEW` | L2_1 |
| CAP-INC-LIST | `INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS` | `ACT-INCIDENT-LIST-DOWNLOAD` | L2_1 |
| CAP-INC-GET | `INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS` | `ACT-INCIDENT-DETAIL-VIEW` | L2_1 |
| CAP-INC-GET | `INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS` | `ACT-INCIDENT-DETAIL-DOWNLOAD` | L2_1 |
| CAP-INC-ACK | `INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS` | `ACT-INCIDENT-ACKNOWLEDGE` | GC_L |
| CAP-INC-RESOLVE | `INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS` | `ACT-INCIDENT-RESOLVE` | GC_L |
| CAP-INC-LIST (historical) | `INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS` | `ACT-INCIDENT-HISTORY-VIEW` | L2_1 |
| CAP-INC-LIST (historical) | `INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS` | `ACT-INCIDENT-HISTORY-DOWNLOAD` | L2_1 |

---

## ADDITIONAL CAPABILITIES DISCOVERED (Not in Seed)

During extraction, these capabilities were found but NOT in the L2.1 seed data:

| Capability | API Endpoint | Mode | Should Add? |
|------------|--------------|------|-------------|
| `CAP-INC-ESCALATE` | (referenced in seed but not in code) | WRITE | **GAP: Seed has action, code doesn't** |
| `CAP-INC-SEARCH` | `POST /guard/incidents/search` | READ | Yes - complex search |
| `CAP-INC-TIMELINE` | `GET /guard/incidents/{id}/timeline` | READ | Yes - decision timeline |
| `CAP-INC-NARRATIVE` | `GET /guard/incidents/{id}/narrative` | READ | Yes - M29 calm vocabulary |
| `CAP-INC-EXPORT` | `POST /guard/incidents/{id}/export` | READ | Yes - PDF evidence report |

**Critical Gap:** `ACT-INCIDENT-ESCALATE` is in seed but has NO backend implementation.

---

## PHASE 1 COMPLETION CHECKLIST

| Criterion | Status |
|-----------|--------|
| All capabilities present in intelligence table | ✅ 4 core + 4 additional found |
| All adapters/operators cross-referenced | ✅ 11 operator mappings |
| All UNKNOWNs explicit | ✅ Reversibility, Idempotency flagged |
| All risks surfaced | ✅ 4 risk categories identified |
| No UI or binding assumptions | ✅ Code-only evidence |

**Phase 1 Status:** COMPLETE (for Incidents domain)

---

## NEXT: Phase 2 Elicitation Required

The following questions must be answered before Phase 3 binding:

1. **Idempotency:** What happens when acknowledge/resolve is called twice?
2. **Reversibility:** Should incidents be reopenable after acknowledgment/resolution?
3. **Escalation:** Should `ACT-INCIDENT-ESCALATE` be removed from seed or implemented?
4. **Search/Timeline/Narrative:** Add to L2.1 surfaces?
5. **Export:** Add as GC_L action (write to generate) or L2.1 (read only)?

---

## References

- `backend/app/api/guard.py` — L2 API routes
- `backend/app/adapters/customer_incidents_adapter.py` — L3 adapter
- `backend/app/services/incident_read_service.py` — L4 read service
- `backend/app/services/incident_write_service.py` — L4 write service
- `design/l2_1/seeds/l2_1_action_capabilities.seed.sql` — L2.1 seed data
- PIN-280, PIN-281 — L2 Promotion Governance
- M29 — Calm Vocabulary per Customer Console v1 Constitution
