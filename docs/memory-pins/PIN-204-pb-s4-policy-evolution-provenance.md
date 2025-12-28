# PIN-204: PB-S4 Policy Evolution With Provenance

**Status:** FROZEN
**Date:** 2025-12-27
**Phase:** B (Resilience & Recovery)
**Frozen:** 2025-12-27

---

## PB-S4 Truth Objective

> **The system may propose policy changes based on observed feedback, but must NEVER auto-enforce, auto-modify, or retroactively affect executions.**

PB-S4 is **recommendation with provenance**, not automation.
Key rule: **Derive, don't decide.**

---

## Inheritance Chain

| Prerequisite | Guarantee | Status |
|--------------|-----------|--------|
| PB-S1 | Retry creates NEW execution (immutability) | FROZEN |
| PB-S2 | Crashed runs are never silently lost | FROZEN |
| PB-S3 | Feedback observes but never mutates | FROZEN |
| PB-S4 | Policies proposed, never auto-enforced | FROZEN |

---

## Non-Negotiables

- Execution history is immutable
- Feedback is inert
- Policies are versioned artifacts
- **Human approval is mandatory**
- No policy affects past runs

**If any policy auto-applies → PB-S4 FAIL**

---

## Test Scenarios

### PB-S4-S1: Policy Proposal From Repeated Feedback

| Step | Action | Verification |
|------|--------|--------------|
| 1 | Confirm eligible feedback (≥N entries, same category) | Feedback unchanged |
| 2 | Policy draft created with provenance | Status = DRAFT |
| 3 | Verify no enforcement logic attached | No hooks into execution |

**Acceptance Checks:**
- [x] New table: policy_proposals (verified: table exists)
- [x] No FK to execution tables (verified: 0 FK to worker_runs)
- [x] Feedback untouched (verified: 2 records unchanged)
- [x] No policy referenced by runtime (verified: proposals are inert)

### PB-S4-S2: Human Approval/Rejection Flow

| Step | Action | Verification |
|------|--------|--------------|
| 1 | Human approves policy proposal | Manual action only |
| 2 | New policy version created | effective_from timestamp |
| 3 | Human rejects policy proposal | Status = REJECTED |
| 4 | Proposal remains auditable | No deletion |

**Acceptance Checks:**
- [x] Policy versions are append-only (verified: 1 version created)
- [x] Approval does NOT mutate history (verified: 11 runs, 2 feedback unchanged)
- [x] Rejection does NOT delete proposal (verified: rejected proposal preserved)
- [x] Executions remain unchanged (verified: 11 runs, 100 total cost)

---

## Forbidden Outcomes (Instant FAIL)

- Policy auto-enforced
- Policy modifies runtime behavior
- Policy rewrites historical executions
- Policy created without provenance
- Approval inferred automatically
- Feedback deleted or altered

---

## Implementation Requirements

### Policy Proposals Table (Separate from Execution)

```
Table: policy_proposals
- id: UUID
- tenant_id: VARCHAR(255)
- proposal_name: str
- proposal_type: str (rate_limit, cost_cap, retry_policy, etc.)
- rationale: str
- proposed_rule: JSONB
- triggering_feedback_ids: JSONB (list of feedback IDs - provenance)
- status: str (draft, approved, rejected)
- created_at: timestamp
- reviewed_at: timestamp (nullable)
- reviewed_by: str (nullable)
- effective_from: timestamp (nullable, only if approved)
```

### Policy Versions Table (Append-Only)

```
Table: policy_versions
- id: UUID
- proposal_id: UUID (FK to policy_proposals)
- version: int
- rule_snapshot: JSONB
- created_at: timestamp
- created_by: str
```

---

## Acceptance Criteria

PB-S4 is **ACCEPTED** only if:

1. PB-S4-S1 passes all checks
2. PB-S4-S2 passes all checks
3. Policies are inert until approved
4. Provenance is complete and immutable
5. UI makes human control explicit

---

## Verification Results (2025-12-27)

### PB-S4-S1: Policy Proposal From Feedback
```
Proposal created: retry_policy_c0a96db8
Status: draft (INERT until approval)
Provenance: Links to feedback ID 7f56761c-6e37-4fd6-aebe-80ebc1357f9b
No FK to worker_runs: VERIFIED
Feedback unchanged: 2 records
Execution tables: UNCHANGED (11 runs)
```

### PB-S4-S2: Human Approval/Rejection Flow
```
Approval test:
- Status changed: draft → approved
- Version created: v1 (append-only)
- effective_from set: 2025-12-28
- History unchanged: 11 runs, 2 feedback

Rejection test:
- Status changed: draft → rejected
- Proposal preserved: YES (auditable)
- Version created: NO (correct behavior)
- Executions: UNCHANGED
```

### CI Test Results
```
11 tests passed in 1.81s
- TestPBS4ProposalSeparation: 4/4 passed
- TestPBS4ProposalFromFeedback: 1/1 passed
- TestPBS4ApprovalRejectionFlow: 2/2 passed
- TestPBS4ImmutabilityGuarantee: 2/2 passed
- TestPBS4ServiceExists: 2/2 passed
```

---

## Web Propagation Verification (O1-O4)

**Date:** 2025-12-27 (Observability Gap Fix)

| Check | Requirement | Status |
|-------|-------------|--------|
| O1 | API endpoint exists | ✓ `/api/v1/policy-proposals` |
| O2 | List visible with pagination | ✓ `GET /api/v1/policy-proposals?limit=50&offset=0` |
| O3 | Detail accessible | ✓ `GET /api/v1/policy-proposals/{id}` |
| O4 | Execution unchanged | ✓ Read-only (GET only) |

**Endpoints:**
- `GET /api/v1/policy-proposals` - List with pagination, filters by status/type
- `GET /api/v1/policy-proposals/{id}` - Detail view with versions
- `GET /api/v1/policy-proposals/{id}/versions` - Version history
- `GET /api/v1/policy-proposals/stats/summary` - Aggregated statistics

**File:** `app/api/policy_proposals.py`

---

## Implementation Artifacts

| Artifact | Location |
|----------|----------|
| Migration | `alembic/versions/057_pb_s4_policy_proposals.py` |
| Model | `app/models/policy.py` |
| Service | `app/services/policy_proposal.py` |
| API | `app/api/policy_proposals.py` |
| Tests | `tests/test_pb_s4_policy_evolution.py` |

---

## Related Artifacts

| Artifact | Location |
|----------|----------|
| PIN-199 | PB-S1 Retry Immutability (FROZEN) |
| PIN-202 | PB-S2 Crash Recovery (FROZEN) |
| PIN-203 | PB-S3 Controlled Feedback Loops (FROZEN) |

---

*Generated: 2025-12-27*
*Frozen: 2025-12-27*
*Reference: Phase B Resilience*
