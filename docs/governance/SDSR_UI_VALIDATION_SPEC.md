# SDSR UI Validation Spec

**Status:** ACTIVE
**Created:** 2026-01-10
**Reference:** PIN-381, PIN-384, L2.1 Projection Pipeline

---

## 1. UI Pipeline Reference Section

### Governance Artifacts Loaded

| Artifact | Location | Role |
|----------|----------|------|
| UI Projection Lock | `design/l2_1/ui_contract/ui_projection_lock.json` | Frozen projection schema |
| Panel Content Registry | `website/app-shell/src/components/panels/PanelContentRegistry.tsx` | Data binding (LAST step) |
| L2.1 Intent SuperTable | `design/l2_1/supertable/L2_1_UI_INTENT_SUPERTABLE.csv` | Source of truth |

### Projection Statistics (from ui_projection_lock.json)

```
domain_count: 5
panel_count: 54
control_count: 101
```

### Domains in Projection

| Domain | Panel Count | SDSR-Relevant |
|--------|-------------|---------------|
| Overview | 3 | No |
| Activity | 10 | Yes |
| Incidents | 11 | Yes |
| Policies | 17 | Yes |
| Logs | 13 | Yes |

---

## 2. SDSR → UI Coverage Matrix

### Panel Binding Status

| Panel ID | Panel Name | Registry Bound | Renderer Function |
|----------|------------|----------------|-------------------|
| **Activity Domain** |
| ACT-EX-AR-O1 | Active Runs Summary | YES | `ActiveRunsSummary` |
| ACT-EX-AR-O2 | Active Runs List | YES | `ActiveRunsList` |
| ACT-EX-CR-O1 | Completed Runs Summary | YES | `CompletedRunsSummary` |
| ACT-EX-CR-O2 | Completed Runs List | YES | `CompletedRunsList` |
| ACT-EX-RD-O1 | Run Details Summary | YES | `RunDetailsSummary` |
| **Incidents Domain** |
| INC-AI-OI-O1 | Open Incidents Summary | YES | `OpenIncidentsSummary` |
| INC-AI-OI-O2 | Open Incidents List | YES | `OpenIncidentsList` |
| INC-AI-ID-O1 | Incident Summary | YES | `IncidentSummaryPanel` |
| INC-HI-RI-O1 | Resolved Incidents Summary | YES | `ResolvedIncidentsSummary` |
| INC-HI-RI-O2 | Resolved Incidents List | YES | `ResolvedIncidentsList` |
| **Policies Domain** |
| POL-PR-PP-O1 | Pending Proposals Summary | YES | `PendingProposalsSummary` |
| POL-PR-PP-O2 | Pending Proposals List | YES | `ProposalsList` |
| POL-RU-O2 | Policy Rules List | **NO** | **NOT BOUND** |
| **Logs Domain** |
| LOG-ET-TD-O1 | Trace Summary | YES | `TraceSummary` |
| LOG-ET-TD-O2 | Trace List | YES | `TraceList` |
| LOG-ET-TD-O3 | Trace Detail | YES | `TraceDetail` |

### Scenario → Panel Mapping

| Scenario | Required Panels | All Bound? |
|----------|-----------------|------------|
| SDSR-E2E-001 | ACT-EX-AR-O2, INC-AI-OI-O2, POL-PR-PP-O2 | YES |
| SDSR-E2E-003 | ACT-EX-AR-O2, INC-AI-OI-O2, POL-PR-PP-O2 | YES |
| SDSR-E2E-004 | ACT-EX-AR-O2, INC-AI-OI-O2, POL-PR-PP-O2, **POL-RU-O2** | **NO** |

---

## 3. UI Validation Spec per Scenario

### SDSR-E2E-001: Failed Activity Propagation

**Scenario Class:** STATE_INJECTION
**UI Panels Required:** 3

#### Panel: ACT-EX-AR-O2 (Active Runs List)

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Panel exists in projection | exists | YES | ui_projection_lock.json |
| Panel bound in registry | exists | YES | PanelContentRegistry.tsx |
| Run visible | visible | YES | runs |
| Status displays "failed" | matches_backend | status=failed | runs.status |
| SDSR badge visible | visible | YES | runs.is_synthetic=true |

#### Panel: INC-AI-OI-O2 (Open Incidents List)

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Panel exists in projection | exists | YES | ui_projection_lock.json |
| Panel bound in registry | exists | YES | PanelContentRegistry.tsx |
| Incident visible | visible | YES | incidents |
| Severity displays HIGH | matches_backend | severity=HIGH | incidents.severity |
| SDSR badge visible | visible | YES | incidents.is_synthetic=true |

#### Panel: POL-PR-PP-O2 (Pending Proposals List)

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Panel exists in projection | exists | YES | ui_projection_lock.json |
| Panel bound in registry | exists | YES | PanelContentRegistry.tsx |
| Proposal visible | visible | YES | policy_proposals |
| Status displays "draft" | matches_backend | status=draft | policy_proposals.status |
| APPROVE control visible | visible | YES | ui_projection_lock.controls |
| REJECT control visible | visible | YES | ui_projection_lock.controls |
| SDSR badge visible | visible | YES | policy_proposals.is_synthetic=true |

#### Logs Panel: NOT APPLICABLE

STATE_INJECTION mode does not create traces. Logs panel validation not applicable for E2E-001.

---

### SDSR-E2E-003: Incident Severity Thresholds

**Scenario Class:** STATE_INJECTION
**UI Panels Required:** 3
**Sub-Scenarios:** CASE-A-MEDIUM, CASE-B-HIGH

#### Case A (MEDIUM Severity)

##### Panel: ACT-EX-AR-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Run visible | visible | YES | runs |
| Status displays "failed" | matches_backend | status=failed | runs.status |
| SDSR badge visible | visible | YES | runs.is_synthetic=true |

##### Panel: INC-AI-OI-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Incident visible | visible | YES | incidents |
| Severity displays MEDIUM | matches_backend | severity=MEDIUM | incidents.severity |
| Incident count | matches_backend | count=1 | incidents |

##### Panel: POL-PR-PP-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Proposal visible | visible | **NO** | policy_proposals |
| Proposal count | matches_backend | count=0 | policy_proposals |

#### Case B (HIGH Severity)

##### Panel: ACT-EX-AR-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Run visible | visible | YES | runs |
| Status displays "failed" | matches_backend | status=failed | runs.status |
| SDSR badge visible | visible | YES | runs.is_synthetic=true |

##### Panel: INC-AI-OI-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Incident visible | visible | YES | incidents |
| Severity displays HIGH | matches_backend | severity=HIGH | incidents.severity |
| Incident count | matches_backend | count=1 | incidents |

##### Panel: POL-PR-PP-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Proposal visible | visible | YES | policy_proposals |
| Status displays "draft" | matches_backend | status=draft | policy_proposals.status |
| Proposal count | matches_backend | count=1 | policy_proposals |
| APPROVE control visible | visible | YES | ui_projection_lock.controls |
| REJECT control visible | visible | YES | ui_projection_lock.controls |

---

### SDSR-E2E-004: Policy Approval Lifecycle

**Scenario Class:** STATE_INJECTION
**UI Panels Required:** 4 (includes POL-RU-O2)
**Sub-Scenarios:** CASE-A-APPROVE, CASE-B-REJECT

#### Case A (Approve Path)

##### Panel: ACT-EX-AR-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Runs visible | visible | YES | runs |
| Run count | matches_backend | count=2 | runs |
| Status displays "failed" | matches_backend | status=failed | runs.status |
| SDSR badge visible | visible | YES | runs.is_synthetic=true |

##### Panel: INC-AI-OI-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Incident visible | visible | YES | incidents |
| Severity displays HIGH | matches_backend | severity=HIGH | incidents.severity |
| Incident count | matches_backend | count=1 | incidents |

##### Panel: POL-PR-PP-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Proposal visible | visible | YES | policy_proposals |
| Status displays "approved" | matches_backend | status=approved | policy_proposals.status |

##### Panel: POL-RU-O2 (POLICY RULES)

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Panel exists in projection | exists | **UNKNOWN** | ui_projection_lock.json |
| Panel bound in registry | exists | **NO** | PanelContentRegistry.tsx |
| Policy rule visible | visible | **CANNOT VERIFY** | policy_rules |
| Rule is_active | matches_backend | is_active=true | policy_rules.is_active |
| Rule count | matches_backend | count=1 | policy_rules |

**GAP IDENTIFIED:** POL-RU-O2 not bound in PanelContentRegistry

#### Case B (Reject Path)

##### Panel: ACT-EX-AR-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Runs visible | visible | YES | runs |
| Run count | matches_backend | count=2 | runs |
| Status displays "failed" | matches_backend | status=failed | runs.status |

##### Panel: INC-AI-OI-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Incidents visible | visible | YES | incidents |
| Incident count | matches_backend | count=2 | incidents |

##### Panel: POL-PR-PP-O2

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Proposal visible | visible | YES | policy_proposals |
| Status displays "rejected" | matches_backend | status=rejected | policy_proposals.status |

##### Panel: POL-RU-O2 (POLICY RULES)

| Criterion | Type | Expected | Source Table |
|-----------|------|----------|--------------|
| Panel visible | visible | **NO** | policy_rules |
| Rule count | matches_backend | count=0 | policy_rules |

---

## 4. Explicit Gaps

### GAP-001: POL-RU-O2 Not Bound

**Severity:** BLOCKING for E2E-004 UI validation
**Location:** PanelContentRegistry.tsx
**Required By:** SDSR-E2E-004 (CASE-A-APPROVE)

**Description:**
SDSR-E2E-004 expects `POL-RU-O2` panel to display active policy_rules after approval.
This panel is referenced in the scenario YAML but has no renderer in PanelContentRegistry.

**Evidence:**
- E2E-004 YAML line 284-288: `policy_rules: panel_id: POL-RU-O2`
- PanelContentRegistry.tsx: No entry for `POL-RU-O2`

**Impact:**
- UI cannot display policy_rules created from approved proposals
- CASE-A approve path cannot be visually validated

**Status:** NOT FIXED (gap exposure only)

---

### GAP-002: Prevention Records Panel Missing

**Severity:** INFORMATIONAL
**Location:** ui_projection_lock.json / PanelContentRegistry.tsx
**Required By:** SDSR-E2E-004 (implicit)

**Description:**
E2E-004 verifies prevention_records are written when runs are suppressed by policy_rules.
No UI panel exists to observe prevention_records.

**Evidence:**
- E2E-004 YAML acceptance criteria AC-004: `prevention_records.count == 1`
- No prevention_records panel in projection or registry

**Impact:**
- Suppression outcomes not visible in UI
- Operational debugging limited

**Status:** NOT FIXED (gap exposure only)

---

### GAP-003: POL-RU-O2 Not In Projection

**Severity:** HIGH
**Location:** ui_projection_lock.json / L2_1_UI_INTENT_SUPERTABLE.csv

**Description:**
POL-RU-O2 is referenced in SDSR-E2E-004.yaml but DOES NOT EXIST in ui_projection_lock.json.
Grep search confirmed: No matches for `POL-RU` in projection lock.

**Evidence:**
```
$ grep "POL-RU" ui_projection_lock.json
No matches found
```

**Root Cause:**
The scenario author referenced a panel_id that was never defined in the L2.1 intent pipeline.
This violates SDSR-UI-001: UI references must exist in projection before scenario use.

**Impact:**
- E2E-004 cannot be UI-validated for policy_rules display
- Intent row must be added to L2_1_UI_INTENT_SUPERTABLE.csv first
- Full pipeline must run before binding can be added

**Required Fix (in order):**
1. Add intent row to `L2_1_UI_INTENT_SUPERTABLE.csv` for POLICIES.RULES.ACTIVE_RULES topic
2. Run `python3 scripts/tools/l2_pipeline.py generate vN`
3. Run full pipeline: `./scripts/tools/run_l2_pipeline.sh`
4. Copy projection to public/
5. Add POL-RU-O2 renderer to PanelContentRegistry.tsx
6. Update E2E-004 scenario if panel_id changes

**Status:** CONFIRMED GAP (projection missing)

---

## 5. Control Binding Verification

### POL-PR-PP-O2 Controls (from ui_projection_lock.json)

| Control | Type | Bound in Registry |
|---------|------|-------------------|
| FILTER | filter | YES (implicit via query) |
| SORT | sort | YES (implicit via query) |
| SELECT_SINGLE | select | YES (row selection) |
| APPROVE | action | YES (`approveMutation`) |
| REJECT | action | YES (`rejectMutation`) |
| NAVIGATE | navigate | YES (link navigation) |

**Verification:** All POL-PR-PP-O2 controls are bound. APPROVE and REJECT mutations confirmed in ProposalsList component (lines 898-916).

### INC-AI-OI-O2 Controls (from ui_projection_lock.json)

| Control | Type | Bound in Registry |
|---------|------|-------------------|
| FILTER | filter | YES (implicit via query) |
| SORT | sort | YES (implicit via query) |
| SELECT_MULTI | select | Partial (no multi-select UI) |
| ACKNOWLEDGE | action | **NO** (no mutation) |
| NAVIGATE | navigate | YES (link navigation) |

**Gap:** ACKNOWLEDGE control not implemented in OpenIncidentsList.

---

## 6. SDSR Badge Rendering Verification

### Badge Implementation (PanelContentRegistry.tsx)

All list components check `is_synthetic` and render SDSR badge:

```typescript
{run.is_synthetic && (
  <span className="px-2 py-0.5 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
    SDSR
  </span>
)}
```

**Verified in:**
- `RunListItem` (line 249-252)
- `IncidentListItem` (line 517-520)
- `TraceListItem` (line 733-737)

**Missing in:**
- `ProposalListItem` - No `is_synthetic` check for proposals

**Status:** ProposalsList does not render SDSR badge for synthetic proposals.

---

## Summary

| Category | Count |
|----------|-------|
| Scenarios Mapped | 3 |
| Panels Required | 4 unique |
| Panels Bound | 3 of 4 |
| Critical Gaps | 2 (POL-RU-O2 not in projection, not bound) |
| Informational Gaps | 1 (prevention_records) |
| Control Gaps | 2 (ACKNOWLEDGE, proposal SDSR badge) |

**Overall Status:** PARTIAL COVERAGE

### Validation Readiness

| Scenario | UI Validatable | Blocking Gaps |
|----------|----------------|---------------|
| SDSR-E2E-001 | YES | None |
| SDSR-E2E-003 | YES | None |
| SDSR-E2E-004 | PARTIAL | GAP-001, GAP-003 (POL-RU-O2) |

### Gap Priority

| Gap | Severity | Fix Required |
|-----|----------|--------------|
| GAP-003 | HIGH | Add intent row + run pipeline |
| GAP-001 | HIGH | Add renderer after GAP-003 |
| GAP-002 | INFO | Optional (prevention_records panel) |

E2E-001 and E2E-003 can be fully UI-validated with current bindings.
E2E-004 requires L2.1 pipeline update before full UI validation.
