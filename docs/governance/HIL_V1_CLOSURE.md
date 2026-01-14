# HIL v1 CLOSURE DOCUMENT

**Status:** FROZEN
**Effective:** 2026-01-14
**Reference:** PIN-417
**Authority:** Founder-ratified

---

## 1. CERTIFICATION

**HIL v1 (Human Interpretation Layer) is COMPLETE and FROZEN.**

No further development, extension, or "improvement" is permitted without opening a new PIN and explicit founder approval.

---

## 2. DELIVERED SCOPE

### Interpretation Panels

| Domain    | Panel ID       | Capability         | Status   | SDSR Scenario         |
|-----------|----------------|--------------------|---------|-----------------------|
| Activity  | ACT-EX-SUM-O1  | summary.activity   | OBSERVED | SDSR-HIL-ACT-SUM-001  |
| Incidents | INC-AI-SUM-O1  | summary.incidents  | OBSERVED | SDSR-HIL-INC-SUM-001  |

### Artifacts Delivered (Per Domain)

1. **JSON Schema** - Response contract locked
2. **Intent YAML** - Panel definition
3. **SDSR Scenario** - Invariant validation
4. **Backend Endpoint** - `/api/v1/{domain}/summary`
5. **Capability Registry** - AURORA L2 status tracking
6. **Frontend Renderer** - PanelContentRegistry component

### Invariants Validated

All panels passed 7 machine-enforced invariants:

| ID | Invariant | Rule |
|----|-----------|------|
| INV-001 | lifecycle_sum_reconciliation | sum(states) == total |
| INV-002 | attention_count_matches | attention.count == relevant_state_count |
| INV-003 | window_echo | response.window == request.window |
| INV-004 | attention_reasons_imply_count | reasons.length > 0 implies count > 0 |
| INV-004b | zero_count_zero_reasons | count == 0 implies reasons.length == 0 |
| INV-005 | provenance_present | derived_from is never empty |
| INV-007 | aggregation_type_locked | aggregation == domain-specific constant |

---

## 3. FROZEN CONSTRAINTS (NON-NEGOTIABLE)

### 3.1 Domain Scope

HIL v1 covers **exactly two domains**:
- Activity
- Incidents

**Forbidden:**
- Adding Policies summaries
- Adding Logs summaries
- Adding Overview synthesis
- Adding any new domain interpretation

### 3.2 Data Semantics

HIL v1 provides **counts only**:
- Total counts
- Counts by lifecycle state
- Attention count

**Forbidden:**
- Trends (up/down arrows)
- Deltas (change from previous period)
- Percentages
- Severity breakdowns beyond attention reasons
- Time-series data
- Comparisons between windows

### 3.3 Attention Semantics

Each domain has **separate attention registries**:

| Domain | Registry File | Valid Reasons |
|--------|--------------|---------------|
| Activity | `attention_reasons.yaml` | `active_runs`, `recent_failures` |
| Incidents | `incidents_attention_reasons.yaml` | `unresolved`, `high_severity` |

**Frozen rule:** Activity reasons ≠ Incidents reasons. No cross-domain meaning.

### 3.4 Frontend Behavior

UI is **purely observational**:
- Fetches data from endpoint
- Renders exactly what backend provides
- No computation, no fallback, no inference

**Forbidden:**
- Client-side aggregation
- "Best effort" display
- Fallback values when API fails
- Caching beyond React Query defaults

### 3.5 Provenance

Every response **must include provenance**:
```json
{
  "provenance": {
    "derived_from": ["capability.a", "capability.b"],
    "aggregation": "AGGREGATION_TYPE",
    "generated_at": "ISO_TIMESTAMP"
  }
}
```

**Frozen rule:** No interpretation without declared lineage.

---

## 4. ISSUES ENCOUNTERED & LESSONS LOCKED

### Issue 1: FastAPI Route Shadowing

**What happened:** `/summary` was captured by `/{incident_id}` due to route ordering.

**Lesson:** Execution order is part of the contract surface.

**Lock:** Static routes MUST be defined before variable routes in all API modules.

### Issue 2: Capability File Naming

**What happened:** Manual naming created `SUMMARY_INCIDENTS.yaml` but applier expected `summary.incidents.yaml`.

**Lesson:** Capability IDs are filesystem-addressed identifiers.

**Lock:** Capability filenames MUST be `AURORA_L2_CAPABILITY_{capability_id}.yaml` exactly.

### Issue 3: Intent Registry Miss

**What happened:** Intent YAML existed but wasn't in registry, so compiler skipped it.

**Lesson:** Existence ≠ Eligibility. Registration is a gate.

**Lock:** This is correct behavior. No change needed.

### Issue 4: Projection Diff Guard (PDG)

**What happened:** Manual copy was used to bypass PDG failures.

**Lesson:** Manual overrides weaken the guard.

**Lock for v2:** No manual projection copy. Always update allowlist explicitly.

### Issue 5: SDSR Observation Class

**What happened:** Missing `observation_class` field caused applier to reject.

**Lesson:** Observation metadata is causality, not decoration.

**Lock:** Add schema validation for observation files pre-apply.

---

## 5. WHAT IS EXPLICITLY FORBIDDEN

Until a new PIN is opened and approved:

| Action | Status | Reason |
|--------|--------|--------|
| Add third domain interpretation | FORBIDDEN | Scope creep |
| Add trends/deltas to summaries | FORBIDDEN | v2 feature |
| Add Overview synthesis | FORBIDDEN | Aggregation of aggregations is v2 |
| Modify attention registries | FORBIDDEN | Locked semantics |
| Add client-side computation | FORBIDDEN | UI observational only |
| Change invariant definitions | FORBIDDEN | Machine contract |
| Bypass PDG manually | FORBIDDEN | Guard integrity |

---

## 6. TRANSITION TO NEXT WORK

HIL v1 is now **stable infrastructure**. The system has:
- 2 interpretation panels (OBSERVED)
- 14 validated invariants (7 per domain)
- Machine-enforced provenance
- Registry-backed attention semantics

### Recommended Next Steps (Not HIL)

1. **Execution system work** - Core agent runtime
2. **Governance hardening** - Route linter, capability validator
3. **Onboarding flow** - New tenant experience
4. **SDK improvements** - Developer experience

### If HIL v2 is Desired Later

Open a new PIN with:
- Clear scope declaration
- New invariant definitions
- Approval before any implementation

---

## 7. ATTESTATION

```
HIL_V1_CLOSURE_ATTESTATION
- status: FROZEN
- domains_delivered: [Activity, Incidents]
- panels_delivered: [ACT-EX-SUM-O1, INC-AI-SUM-O1]
- capabilities_observed: [summary.activity, summary.incidents]
- invariants_validated: 14
- issues_encountered: 5
- lessons_locked: 5
- closure_date: 2026-01-14
- next_extension_requires: New PIN + Founder Approval
```

---

## 8. REFERENCES

- PIN-417: HIL v1 Implementation
- PIN-412: Incident Lifecycle States
- PIN-370: SDSR System Contract
- `design/l2_1/intents/ACT-EX-SUM-O1.yaml`
- `design/l2_1/intents/INC-AI-SUM-O1.yaml`
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_summary.activity.yaml`
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_summary.incidents.yaml`
- `sdsr/observations/SDSR_OBSERVATION_SDSR-HIL-ACT-SUM-001.json`
- `sdsr/observations/SDSR_OBSERVATION_SDSR-HIL-INC-SUM-001.json`
