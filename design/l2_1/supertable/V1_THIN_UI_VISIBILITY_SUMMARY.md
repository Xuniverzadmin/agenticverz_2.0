# V1 Thin UI Visibility Summary

**Status:** PHASE 2.1 OUTPUT
**Created:** 2026-01-07
**Purpose:** Define what's visible in v1 thin/wireframe UI vs deferred

---

## V1 THIN UI — WHAT'S INCLUDED

### Control Catalog (v1)

```
FILTER          ← Existing (column-based filtering)
SORT            ← Existing (column sorting)
SELECT_SINGLE   ← Existing (single row selection)
SELECT_MULTI    ← Existing (bulk selection)
DOWNLOAD        ← Existing (JSON/CSV export)
NAVIGATE        ← Existing (drill-down navigation)
ACKNOWLEDGE     ← Existing (incident acknowledgment)
RESOLVE         ← Existing (incident resolution)
─────────────────────────────────────────────────
ACTIVATE_TOGGLE ← NEW (routine policy enable/disable)
ADD_NOTE        ← NEW (incident annotation)
SEARCH          ← NEW (free-text search)
```

**Total v1 Controls: 11** (8 existing + 3 new)

### Schema Columns (v1)

All base columns PLUS:

```
danger_level         ← NEW (NONE/LOW/MEDIUM/HIGH/CRITICAL)
requires_interpreter ← NEW (YES/NO)
```

**Total v1 Columns: 24** (22 base + 2 new)

---

## V1 DOMAIN COVERAGE

### Overview Domain (3 panels)

| Panel | Order | Controls | Actions | Status |
|-------|-------|----------|---------|--------|
| System Status Summary | O1 | — | READ | ✅ v1 |
| Health Metrics Summary | O1 | — | READ | ✅ v1 |
| Health Metrics List | O2 | FILTER, SORT, SEARCH, NAVIGATE | READ | ✅ v1 |

**Note:** Backend API gap (PIN-348) — UI intent documented but may show "Coming Soon" or placeholder.

### Activity Domain (10 panels)

| Panel | Order | Controls | Actions | Status |
|-------|-------|----------|---------|--------|
| Active Runs Summary | O1 | — | READ | ✅ v1 |
| Active Runs List | O2 | FILTER, SORT, SEARCH, NAVIGATE | READ | ✅ v1 |
| Completed Runs Summary | O1 | — | READ | ✅ v1 |
| Completed Runs List | O2 | FILTER, SORT, SEARCH, DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| Completed Run Detail | O3 | DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| Run Details Summary | O1 | — | READ | ✅ v1 |
| Run Steps List | O2 | FILTER, SORT, SEARCH, NAVIGATE | READ | ✅ v1 |
| Run Step Detail | O3 | DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| Run Context | O4 | NAVIGATE | READ | ✅ v1 |
| Run Proof | O5 | DOWNLOAD | READ, DOWNLOAD | ✅ v1 |

**Note:** CANCEL deferred — no action controls for active runs in v1.

### Incidents Domain (11 panels)

| Panel | Order | Controls | Actions | Status |
|-------|-------|----------|---------|--------|
| Open Incidents Summary | O1 | — | READ | ✅ v1 |
| Open Incidents List | O2 | FILTER, SORT, SEARCH, ACKNOWLEDGE, NAVIGATE | READ, ACKNOWLEDGE | ✅ v1 |
| Incident Summary | O1 | — | READ | ✅ v1 |
| Incident Timeline | O2 | SORT, NAVIGATE | READ | ✅ v1 |
| Incident Detail | O3 | DOWNLOAD, ACKNOWLEDGE, RESOLVE, ADD_NOTE, NAVIGATE | READ, WRITE, ACTIVATE | ✅ v1 |
| Incident Impact | O4 | NAVIGATE | READ | ✅ v1 |
| Resolved Incidents Summary | O1 | — | READ | ✅ v1 |
| Resolved Incidents List | O2 | FILTER, SORT, SEARCH, DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| Resolved Incident Detail | O3 | DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| Resolved Incident Context | O4 | NAVIGATE | READ | ✅ v1 |
| Resolved Incident Proof | O5 | DOWNLOAD | READ, DOWNLOAD | ✅ v1 |

**Note:** REOPEN deferred — resolved incidents are read-only in v1.

### Policies Domain (15 panels)

| Panel | Order | Controls | Actions | Status |
|-------|-------|----------|---------|--------|
| Budget Policies Summary | O1 | — | READ | ✅ v1 |
| Budget Policies List | O2 | FILTER, SORT, SEARCH, ACTIVATE_TOGGLE, NAVIGATE | READ, ACTIVATE | ⚠️ v1* |
| Budget Policy Detail | O3 | ACTIVATE_TOGGLE, NAVIGATE | READ, ACTIVATE | ⚠️ v1* |
| Rate Limits Summary | O1 | — | READ | ✅ v1 |
| Rate Limits List | O2 | FILTER, SORT, SEARCH, ACTIVATE_TOGGLE, NAVIGATE | READ, ACTIVATE | ⚠️ v1* |
| Rate Limit Detail | O3 | ACTIVATE_TOGGLE, NAVIGATE | READ, ACTIVATE | ⚠️ v1* |
| Approval Rules Summary | O1 | — | READ | ✅ v1 |
| Approval Rules List | O2 | FILTER, SORT, SEARCH, ACTIVATE_TOGGLE, NAVIGATE | READ, ACTIVATE | ⚠️ v1* |
| Approval Rule Detail | O3 | ACTIVATE_TOGGLE, NAVIGATE | READ, ACTIVATE | ⚠️ v1* |
| Approval Rule Impact | O4 | NAVIGATE | READ | ✅ v1 |
| Policy Changes Summary | O1 | — | READ | ✅ v1 |
| Policy Changes List | O2 | FILTER, SORT, SEARCH, DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| Policy Change Detail | O3 | DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| Policy Change Context | O4 | NAVIGATE | READ | ✅ v1 |
| Policy Change Proof | O5 | DOWNLOAD | READ, DOWNLOAD | ✅ v1 |

**⚠️ v1*:** ACTIVATE_TOGGLE included in UI but GC_L backend NOT IMPLEMENTED (PIN-348). May show "Coming Soon" or disabled state.

### Logs Domain (13 panels)

| Panel | Order | Controls | Actions | Status |
|-------|-------|----------|---------|--------|
| System Audit Summary | O1 | — | READ | ✅ v1 |
| System Audit List | O2 | FILTER, SORT, SEARCH, DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| System Audit Detail | O3 | DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| System Audit Proof | O5 | DOWNLOAD | READ, DOWNLOAD | ✅ v1 |
| User Audit Summary | O1 | — | READ | ✅ v1 |
| User Audit List | O2 | FILTER, SORT, SEARCH, DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| User Audit Detail | O3 | DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| User Audit Proof | O5 | DOWNLOAD | READ, DOWNLOAD | ✅ v1 |
| Trace Summary | O1 | — | READ | ✅ v1 |
| Trace List | O2 | FILTER, SORT, SEARCH, DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| Trace Detail | O3 | DOWNLOAD, NAVIGATE | READ, DOWNLOAD | ✅ v1 |
| Trace Context | O4 | NAVIGATE | READ | ✅ v1 |
| Trace Proof | O5 | DOWNLOAD | READ, DOWNLOAD | ✅ v1 |

---

## V1 SUMMARY BY ACTION TYPE

| Action Type | v1 Panels | Notes |
|-------------|-----------|-------|
| **READ** | 52/52 | All panels support read |
| **DOWNLOAD** | 15/52 | O2 bulk + O3/O5 single-item export |
| **WRITE** | 1/52 | Incident Detail (ADD_NOTE) |
| **ACTIVATE** | 9/52 | 2 Incidents (ACK/RESOLVE) + 6 Policies (TOGGLE) + 1 Incidents O2 (bulk ACK) |

---

## DEFERRED TO POST-V1

### Controls Deferred

| Control | Reason | Customer Impact |
|---------|--------|-----------------|
| EXPORT_PDF | Backend PDF generation unconfirmed | Users export JSON/CSV, not legal-grade PDF |
| CANCEL | Backend capability unclear | Users cannot stop active runs |
| REOPEN | Backend reversibility unconfirmed | Acknowledged/resolved incidents stay closed |

### Columns Deferred

| Column | Reason | Workaround |
|--------|--------|------------|
| export_format_hint | Depends on EXPORT_PDF | DOWNLOAD button with manual format selection |

### Features Deferred

| Feature | Domain | Reason |
|---------|--------|--------|
| Run Cancellation | Activity | Backend CANCEL not confirmed |
| Incident Reopening | Incidents | Backend REOPEN not confirmed |
| PDF Evidence Export | Incidents | Backend PDF generation not confirmed |
| Policy Write Mutations | Policies | GC_L backend NOT IMPLEMENTED |

---

## V1 KNOWN LIMITATIONS (VISIBLE TO USER)

| Limitation | User-Facing Behavior |
|------------|---------------------|
| Overview API gap | "Overview" section may show placeholder or "Coming Soon" |
| GC_L not implemented | Policy ACTIVATE_TOGGLE may be disabled or show "Configuration required" |
| No CANCEL | Active runs list has no action buttons |
| No REOPEN | Resolved incidents are read-only |
| No PDF export | Download offers JSON/CSV only |

---

## V1 WIREFRAME PRIORITIES

### Must Have (P0)

1. All O1 summary panels (15) — entry points
2. All O2 list panels with FILTER/SORT/SEARCH (14)
3. DOWNLOAD on Logs and Activity O2/O3/O5
4. ACKNOWLEDGE/RESOLVE on Incidents O2/O3
5. NAVIGATE from O1 → O2 → O3 → O4 → O5

### Should Have (P1)

1. ADD_NOTE on Incident Detail
2. SEARCH on all O2 panels
3. danger_level visual indicators on action buttons

### Could Have (P2)

1. ACTIVATE_TOGGLE on Policies (depends on GC_L readiness)
2. Overview domain (depends on API readiness)

---

## Attestation

```
✔ 52 panels documented for v1
✔ 11 controls in v1 catalog
✔ 24 columns in v1 schema
✔ Deferred items explicitly listed
✔ Known limitations documented
✔ Wireframe priorities defined
```
