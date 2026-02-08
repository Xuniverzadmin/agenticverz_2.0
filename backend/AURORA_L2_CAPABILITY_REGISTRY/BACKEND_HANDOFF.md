# AURORA_L2 Backend Capability Declaration Guide

**Status:** ACTIVE (v2.0 - 4-State Model)
**Audience:** Backend engineers implementing action handlers
**Time to read:** 3 minutes

---

## The Core Invariant

> **Capabilities are not real because backend says so.**
> **They are real only when the system demonstrates them.**

Backend YAML is a **claim**, not truth. Truth emerges only when SDSR verifies behavior.

---

## The 4-State Lifecycle

```
DISCOVERED  →  DECLARED  →  OBSERVED  →  TRUSTED
     ↑             ↑            ↑           ↑
   auto        backend       system     governance
```

| State | Who Sets It | UI Button | Meaning |
|-------|-------------|-----------|---------|
| DISCOVERED | System (auto-seeded) | Disabled | Action name exists |
| DECLARED | Backend team | **Still Disabled** | Backend claims implementation |
| OBSERVED | System (SDSR) | **Enabled** | System verified behavior |
| TRUSTED | Governance | Enabled + CI | Fully governed |

**Key point:** Backend can only move to DECLARED. Button stays disabled until OBSERVED.

---

## What Backend Does (and doesn't do)

### Backend CAN:
- Implement the handler code
- Fill in the capability YAML
- Move status from DISCOVERED → DECLARED

### Backend CANNOT:
- Enable the UI button (that's OBSERVED)
- Write observation metadata (that's system-only)
- Skip to OBSERVED or TRUSTED

---

## How to Declare a Capability

### Step 1: Implement your handler

Write your endpoint. Test it works.

### Step 2: Edit the capability YAML

```
backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_<ACTION>.yaml
```

### Step 3: Fill in required fields

```yaml
capability_id: APPROVE
status: DECLARED                 # ← Change from DISCOVERED

implementation:
  endpoint: /api/v1/policy-proposals/{id}/approve
  method: POST
  handler: app.hoc.api.cus.policies.policy_proposals.approve_proposal

auth:
  roles: [admin, policy_approver]
  permissions: [policy:approve]

side_effects:
  - "Changes proposal status to APPROVED"

metadata:
  generated_by: AURORA_L2_seed_capability_registry.py
  generated_on: 2026-01-10
  declared_by: your-name        # ← Add this
  declared_on: 2026-01-10       # ← Add this
```

### Step 4: Run pipeline

```bash
./scripts/tools/run_aurora_l2_pipeline.sh
```

### Step 5: Verify (button still disabled)

```bash
python3 scripts/ops/aurora_l2_binding_report.py
```

You should see the panel still in DRAFT. **This is correct.**

---

## What Happens Next (Not Your Job)

1. SDSR scenario exercises the action
2. UI invokes the endpoint
3. Expected state transition is observed
4. System writes observation metadata
5. Status becomes OBSERVED
6. Button enables

**You don't do this.** The system does.

---

## Current Capabilities

| Action | Status | Used By |
|--------|--------|---------|
| APPROVE | DISCOVERED | POL-PR-PP-O2 |
| REJECT | DISCOVERED | POL-PR-PP-O2 |
| ACKNOWLEDGE | DISCOVERED | INC-AI-ID-O3, INC-AI-OI-O2 |
| RESOLVE | DISCOVERED | INC-AI-ID-O3 |
| ACTIVATE | DISCOVERED | POL-AP-AR-O3, POL-AP-BP-O3, POL-AP-RL-O3 |
| DEACTIVATE | DISCOVERED | POL-AP-AR-O3, POL-AP-BP-O3, POL-AP-RL-O3 |
| ADD_NOTE | DISCOVERED | INC-AI-ID-O3 |
| UPDATE_RULE | DISCOVERED | POL-AP-AR-O3 |
| UPDATE_THRESHOLD | DISCOVERED | POL-AP-BP-O3 |
| UPDATE_LIMIT | DISCOVERED | POL-AP-RL-O3 |

---

## What NOT to Do

| Don't | Why |
|-------|-----|
| Set status to OBSERVED | Only system can do that |
| Write observed_by metadata | That's system-only |
| Expect button to enable after DECLARED | DECLARED ≠ OBSERVED |
| Edit intent YAMLs | Those are frozen |
| Edit projection files | Those are generated |

---

## Why This Matters

In a large, multi-team, partially-documented codebase:

- Backend claims are unreliable
- Code presence ≠ correct behavior
- Only system observation proves truth

This protects everyone:
- UI can't be gaslit by backend
- Backend can't be blamed for UI bugs
- Users never see broken buttons

---

## File Locations

| What | Where |
|------|-------|
| Capability files | `backend/AURORA_L2_CAPABILITY_REGISTRY/*.yaml` |
| Status model | `backend/AURORA_L2_CAPABILITY_REGISTRY/CAPABILITY_STATUS_MODEL.yaml` |
| Pipeline | `scripts/tools/run_aurora_l2_pipeline.sh` |
| Binding report | `scripts/ops/aurora_l2_binding_report.py` |

---

## Questions?

The capability registry is the contract. If something is unclear:
1. Read the capability file
2. Read `CAPABILITY_STATUS_MODEL.yaml`
3. Ask before guessing

**No silent assumptions. No "temporary" workarounds. No shortcuts.**
