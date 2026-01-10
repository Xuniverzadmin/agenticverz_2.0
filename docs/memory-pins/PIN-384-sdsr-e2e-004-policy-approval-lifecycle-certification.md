# PIN-384: SDSR-E2E-004 Policy Approval Lifecycle Certification

**Status:** ✅ COMPLETE
**Created:** 2026-01-10
**Category:** SDSR / E2E Testing
**Milestone:** SDSR-E2E-004

---

## Summary

E2E-004 validates human-in-the-loop policy approval: approve → enforce, reject → no enforcement. Includes structural fixes for post-approval hook and suppression logic.

---

## Details

## Overview

SDSR-E2E-004 validates the complete policy lifecycle with human-in-the-loop decision making:
- Approve path: proposal → policy_rule → suppression
- Reject path: proposal → no policy_rule → no suppression

This scenario revealed and fixed TWO structural gaps in the system.

---

## Tasks Completed

### Structural Fixes Applied

| Task | Status | File | Description |
|------|--------|------|-------------|
| Post-approval hook | ✅ COMPLETE | `policy_proposal.py` | Creates policy_rule when proposal is approved |
| Suppression check | ✅ COMPLETE | `incident_engine.py` | Checks active policy_rules before creating incidents |
| Prevention record writing | ✅ COMPLETE | `incident_engine.py` | Documents suppression with prevention_record |
| Synthetic flag propagation | ✅ COMPLETE | `policy.py` | Added is_synthetic columns to PolicyProposal model |
| E2E-004 YAML spec | ✅ COMPLETE | `scenarios/SDSR-E2E-004.yaml` | Full spec with approve/reject paths |

### CASE-A (Approve Path) Execution

| Step | Status | Result |
|------|--------|--------|
| Create failed run | ✅ | run-e2e-004-case-a-run1 |
| IncidentEngine fires | ✅ | Incident + proposal created |
| Human approves | ✅ | Proposal status → approved |
| Policy_rule created | ✅ | rule_56a48a9bbbb24245 (is_active=true) |
| Create second run | ✅ | run-e2e-004-case-a-run2 |
| Suppression check | ✅ | Run suppressed, no new incident |
| Prevention record | ✅ | prev_00ea7d9f9b2345dc (outcome=prevented) |

### CASE-B (Reject Path) Execution

| Step | Status | Result |
|------|--------|--------|
| Create failed run | ✅ | run-e2e-004-case-b-run1 |
| IncidentEngine fires | ✅ | Incident + proposal created |
| Human rejects | ✅ | Proposal status → rejected |
| NO policy_rule | ✅ | policy_rules.count = 0 |
| Create second run | ✅ | run-e2e-004-case-b-run2 |
| NO suppression | ✅ | Second incident created |
| NO prevention record | ✅ | prevention_records.count = 0 |

---

## Acceptance Criteria Results

### CASE-A (Approve)

| AC | Criterion | Expected | Actual | Status |
|----|-----------|----------|--------|--------|
| AC-001 | Approval creates 1 policy_rule | 1 | 1 | ✅ |
| AC-002 | Rule is_active=true, mode=active | true/active | true/active | ✅ |
| AC-003 | 0 new incidents after second run | 0 | 0 | ✅ |
| AC-004 | Prevention record written | 1 | 1 | ✅ |
| AC-008 | reviewed_by NOT NULL | NOT NULL | sdsr-human-approver | ✅ |

### CASE-B (Reject)

| AC | Criterion | Expected | Actual | Status |
|----|-----------|----------|--------|--------|
| AC-005 | Rejection creates 0 policy_rules | 0 | 0 | ✅ |
| AC-006 | Both runs create incidents | 2 | 2 | ✅ |
| AC-007 | No prevention records | 0 | 0 | ✅ |
| AC-008 | reviewed_by NOT NULL | NOT NULL | sdsr-human-rejector | ✅ |

---

## Key Code Changes

### 1. Post-Approval Hook (policy_proposal.py)

```python
async def _create_policy_rule_from_proposal(
    session: AsyncSession,
    proposal: PolicyProposal,
    version_id: Optional[UUID],
    approved_by: str,
) -> str:
    # Creates policy_rule from approved proposal
    # Idempotent via deterministic rule_id
    # Propagates synthetic flags
```

### 2. Suppression Check (incident_engine.py)

```python
def _check_policy_suppression(
    self,
    tenant_id: str,
    error_code: Optional[str],
    category: str,
) -> Optional[dict]:
    # Checks active policy_rules before creating incident
    # Returns matching policy if suppression applies
```

### 3. Prevention Record Writer (incident_engine.py)

```python
def _write_prevention_record(
    self,
    policy_id: str,
    run_id: str,
    ...
) -> str:
    # Writes prevention_record when run is suppressed
    # Exactly one side effect: incident OR prevention_record
```

---

## Causal Chains Validated

### Approve Path
```
Run (failed) → Incident → policy_proposal (draft)
→ Human APPROVES via API
→ policy_rule (is_active=true, mode=active)
→ Second run → SUPPRESSED
→ prevention_record written
```

### Reject Path
```
Run (failed) → Incident → policy_proposal (draft)
→ Human REJECTS via API
→ NO policy_rule
→ Second run → NOT suppressed
→ Second incident created
```

---

## Files Modified

| File | Change Type | Purpose |
|------|-------------|---------|
| `backend/app/services/policy_proposal.py` | Feature | Post-approval hook |
| `backend/app/services/incident_engine.py` | Feature | Suppression + prevention |
| `backend/app/models/policy.py` | Schema | Synthetic columns |
| `backend/scripts/sdsr/scenarios/SDSR-E2E-004.yaml` | New | Scenario spec |

---

## Certification

**SDSR-E2E-004: CERTIFIED**

The complete policy lifecycle is now validated:
- Proposals are NEVER auto-approved
- Only human action creates policy_rules
- Active policy_rules enforce suppression
- Rejected proposals have no enforcement effect
- All flows work identically for real and synthetic runs

---

## Related PINs

- [PIN-381](PIN-381-.md)
- [PIN-370](PIN-370-.md)
- [PIN-379](PIN-379-.md)
