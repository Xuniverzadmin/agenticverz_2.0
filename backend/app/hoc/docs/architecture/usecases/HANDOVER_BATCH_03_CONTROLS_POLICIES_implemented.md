# HANDOVER_BATCH_03_CONTROLS_POLICIES — Implemented

**Date:** 2026-02-11
**Handover Source:** `HANDOVER_BATCH_03_CONTROLS_POLICIES.md`
**Status:** COMPLETE — all exit criteria met

---

## 1. Policy Proposal Canonical Accept Flow

**Status:** Already implemented (verified, no changes needed).

The `PolicyApprovalHandler` (`policy_approval_handler.py`, 350+ lines) implements the full lifecycle:

| Method | Flow |
|--------|------|
| `create_approval_request` | Initiate approval workflow |
| `review_proposal` | PB-S4 human-controlled acceptance |
| `update_approval_request_approved` | Record approval + activate policy |
| `reject` → `update_approval_request_status` | Reject with reason |
| `batch_escalate` | Escalate stalled approvals |
| `batch_update_expired` | Mark expired requests |

**Hard boundary (verified in Batch-01):**
- `authority.proposals_no_enforcement` — PASS (zero enforcement ops in policy_proposals.py)
- `authority.proposals_allowed_ops_only` — PASS (only `policies.proposals_query` + `policies.approval`)
- `authority.policies_no_direct_l5l6` — PASS (clean L4-only, no L5/L6 direct imports)

**Proposal state machine:** DRAFT → PENDING → APPROVED/REJECTED → ACTIVE (on activation).
`PolicyActivationBlockedError` prevents activation when conflicts exist.

---

## 2. Controls Override Lifecycle (Complete)

### L6 Driver: `override_driver.py` (UPDATED)

Added 3 lifecycle methods to `LimitOverrideService`:

| Method | Transition | Actor Lineage |
|--------|------------|---------------|
| `approve_override` | PENDING → APPROVED/ACTIVE | `approved_by` + `approved_at` |
| `reject_override` | PENDING → REJECTED | `rejected_by` + `rejection_reason` |
| `expire_overrides` | ACTIVE → EXPIRED (batch) | Automated, `expires_at <= now` |

**Full lifecycle states (OverrideStatus enum):**
```
PENDING → APPROVED → ACTIVE → EXPIRED
    ↓          ↓        ↓
 REJECTED   CANCELLED  CANCELLED
```

All methods require actor lineage and reasons. No override state transition without audit trail.

### L4 Handler: `controls_handler.py` (UPDATED)

Added `approve_override`, `reject_override`, `expire_overrides` to `ControlsOverrideHandler` dispatch map.

---

## 3. Per-Run Control Binding Fields (Evaluation Evidence)

### L6 Driver: `evaluation_evidence_driver.py` (CREATED)

**File:** `app/hoc/cus/controls/L6_drivers/evaluation_evidence_driver.py`

New L6 driver for `controls_evaluation_evidence` table (migration 130):

| Method | Purpose |
|--------|---------|
| `record_evidence` | INSERT per-run evaluation evidence with binding fields |
| `query_evidence` | Query evidence by tenant, run_id, control_set_version |

**Binding fields persisted:**
- `control_set_version` — Version of control set at evaluation time
- `override_ids_applied` — JSON array of active override IDs
- `resolver_version` — Algorithm version used for resolution
- `decision` — Evaluation outcome (ALLOWED, BLOCKED, etc.)

### L4 Handler: `ControlsEvaluationEvidenceHandler` (CREATED)

**Operation:** `controls.evaluation_evidence`

| Method | Transaction | Description |
|--------|-------------|-------------|
| `record` | `async with ctx.session.begin()` | Persist evidence + emit event |
| `query` | read-only | List evidence with filters |

---

## 4. Controls/Policies Events (Wired)

### Controls Events

Added `_emit_controls_event()` helper to `controls_handler.py` with `validate_event_payload`.

| Event Type | Trigger | Extension Fields |
|------------|---------|-----------------|
| `controls.EvaluationRecorded` | After evidence recording | `run_id`, `control_set_version`, `resolver_version`, `decision` |

### Policies Events

Policy approval events are already emitted via `onboarding_handler.py` event infrastructure (onboarding.state.transition covers policy activation states).

---

## Authority Boundary Proof

```bash
$ grep -n 'registry.execute' app/hoc/api/cus/controls/controls.py | head -10
# All ops: controls.query — canonical domain
```

```bash
$ grep -n 'registry.execute' app/hoc/api/cus/policies/policy_proposals.py | head -10
# All ops: policies.proposals_query, policies.approval — canonical domain
```

Zero non-canonical mutation paths found. Authority boundary verified by Batch-01 checks (6/6 PASS).

---

## Validation Command Outputs

### Event Contract Verifier
```
Total: 50 | PASS: 50 | FAIL: 0
```

### Storage Contract Verifier
```
Total: 64 | PASS: 64 | FAIL: 0
```

### Aggregator (Strict)
```
Total: 32 | PASS: 32 | WARN: 0 | FAIL: 0
Exit code: 0
```

---

## PASS/WARN/FAIL Matrix

| Verifier | PASS | WARN | FAIL |
|----------|------|------|------|
| Event contract | 50 | 0 | 0 |
| Storage contract | 64 | 0 | 0 |
| Aggregator (strict) | 32 | 0 | 0 |
| **Total** | **146** | **0** | **0** |

---

## Files Modified

| File | Change |
|------|--------|
| `controls/L6_drivers/override_driver.py` | Added approve_override, reject_override, expire_overrides |
| `controls/L6_drivers/evaluation_evidence_driver.py` | CREATED — L6 driver for controls_evaluation_evidence |
| `hoc_spine/orchestrator/handlers/controls_handler.py` | Updated — 3 new override methods, ControlsEvaluationEvidenceHandler, _emit_controls_event |
| `scripts/verification/uc_mon_event_contract_check.py` | Updated — controls_handler emitter |
| `scripts/verification/uc_mon_storage_contract_check.py` | Updated — evaluation evidence driver checks |

## Blockers

None. All exit criteria satisfied.
