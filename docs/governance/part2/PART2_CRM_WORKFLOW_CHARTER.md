# Part-2 CRM Workflow Charter

**Status:** CONSTITUTIONAL DESIGN
**Effective:** 2026-01-04
**Reference:** PIN-284 (Platform Monitoring System), Phase-1 Closure
**Scope:** Governed Change Workflow System

---

## Prime Directive

> **Part-2 is a governed workflow system with human-in-the-loop authority.**
>
> CRM is a workflow **initiator**, not an authority **source**.
> Authority is explicitly staged: machine validation → eligibility gating → human approval → governance automation.

---

## What Part-2 Is NOT

| Misconception | Reality |
|---------------|---------|
| CRM is authority | CRM is a proposal channel only |
| Signals become contracts | Signals become validated proposals |
| Automation replaces judgment | Automation serves approved decisions |
| Phase-1 is extended | Phase-1 is preserved, Part-2 is layered |

---

## The 10-Step Canonical Workflow

### Step 1: Issue Receipt (L8 → DB)

CRM feedback enters the system as an **Issue** (not a signal, not a contract).

```
CRM Event → L8 Ingestion → issue_events table
```

**Fields captured:**
- `issue_id` (UUID)
- `source` (crm_feedback, support_ticket, ops_alert)
- `raw_payload` (JSON)
- `received_at` (timestamp)
- `status` = RECEIVED

---

### Step 2: Validator Analysis (L4)

The **Validator** (L4 domain service) analyzes the issue:

```
Issue → Validator → ValidatedProposal
```

**Validator outputs:**
- `issue_type` (capability_request, bug_report, configuration_change, escalation)
- `severity` (critical, high, medium, low)
- `affected_capabilities` (list of capability names)
- `recommended_action` (create_contract, defer, reject, escalate)
- `confidence_score` (0.0 - 1.0)
- `reason` (human-readable explanation)

**Validator must NOT:**
- Create contracts directly
- Modify system state
- Make eligibility decisions
- Approve anything

---

### Step 3: Eligibility Check (L4)

The **Eligibility Engine** (L4) applies deterministic rules:

```
ValidatedProposal → EligibilityEngine → EligibilityVerdict
```

**Eligibility is binary:** MAY or MAY_NOT.

**MAY become contract if:**
- Validator confidence ≥ threshold (0.7 default)
- Affected capabilities exist in registry
- No blocking governance signals
- Issue type is actionable

**MAY_NOT become contract if:**
- Confidence below threshold
- Unknown capability reference
- Active blocking signal for scope
- Issue type requires manual triage

---

### Step 4: Contract Draft Creation (L4)

If eligible, a **draft contract** is created:

```
EligibleProposal → ContractDraftService → system_contracts (DRAFT)
```

**Draft contract contains:**
- `contract_id` (UUID)
- `status` = DRAFT
- `issue_id` (FK to original issue)
- `proposed_changes` (JSON schema)
- `affected_capabilities` (array)
- `risk_level` (derived from validator)
- `created_at`, `expires_at`

**Draft contracts expire** if not approved within TTL (default: 7 days).

---

### Step 5: Founder Review Gate (Human)

The **Founder Review** is the human-in-the-loop authority gate:

```
DRAFT contract → Founder Dashboard → APPROVED | REJECTED
```

**Founder can:**
- Approve (advances to APPROVED)
- Reject (terminates to REJECTED)
- Request clarification (remains DRAFT)
- Modify scope (creates new draft version)

**Founder CANNOT:**
- Skip validation
- Override eligibility
- Bypass audit after execution
- Create contracts without proposals

---

### Step 6: Contract Activation (L4)

Upon approval, the contract activates:

```
APPROVED contract → ActivationService → ACTIVE
```

**Activation records:**
- `approved_by` (founder_id)
- `approved_at` (timestamp)
- `activation_window` (start, end)
- `execution_constraints` (rate limits, etc.)

---

### Step 7: Governance Job Execution (L5)

The **Governance Job Executor** (L5) executes the contract:

```
ACTIVE contract → JobExecutor → governance_jobs
```

**Job execution:**
- Creates `governance_job` record
- Executes steps in order
- Records each step outcome
- Cannot modify health signals
- Cannot override platform health

**Job states:**
- PENDING → RUNNING → COMPLETED | FAILED

---

### Step 8: Health Evaluation (L4)

After execution, **PlatformHealthService** evaluates impact:

```
Job completion → PlatformHealthService → health signals
```

**Health evaluates:**
- Did capabilities remain healthy?
- Did any invariants break?
- Did execution match proposal?

**Health is authority.** Jobs cannot override health verdicts.

---

### Step 9: Audit Verification (L8)

The **Governance Auditor** (L8) verifies execution:

```
Completed job → Auditor → AuditVerdict
```

**Audit checks:**
- Execution matched contract scope
- No unauthorized mutations
- Health signals consistent
- Timing within window

**Audit verdicts:**
- PASS: Clean execution
- FAIL: Contract violation detected
- INCONCLUSIVE: Manual review required

---

### Step 10: Rollout or Rollback

Based on audit, the system proceeds:

```
PASS → Rollout (contract COMPLETED)
FAIL → Rollback (contract FAILED)
INCONCLUSIVE → Human escalation
```

**Rollout:**
- Contract marked COMPLETED
- Capability state updated
- Audit trail preserved

**Rollback:**
- Contract marked FAILED
- Rollback job created
- Incident created
- Human notification

---

## Authority Chain (Explicit)

```
CRM Event (no authority)
    ↓
Validator (machine, advisory)
    ↓
Eligibility (machine, deterministic gate)
    ↓
Founder Review (human, approval authority)
    ↓
Job Executor (machine, execution authority)
    ↓
Health Service (machine, truth authority)
    ↓
Auditor (machine, verification authority)
```

**No node may skip levels. No node may assume authority it wasn't granted.**

---

## Constitutional Constraints

| ID | Constraint | Enforcement |
|----|------------|-------------|
| PART2-001 | CRM cannot create contracts directly | Validator gate |
| PART2-002 | Contracts require founder approval | Review gate |
| PART2-003 | Jobs cannot override health | Health supremacy |
| PART2-004 | Audit cannot be bypassed | Rollout gate |
| PART2-005 | Phase-1 invariants preserved | Health contracts |

---

## Relationship to Phase-1

Part-2 is **layered on top of** Phase-1, not replacing it:

- **PlatformHealthService** remains the health authority
- **Governance signals** remain the truth source
- **Frozen files** remain frozen
- **HEALTH-IS-AUTHORITY** invariant preserved

Part-2 adds:
- Structured change proposals
- Human approval gates
- Execution auditing
- Controlled automation

---

## Attestation

This charter defines the canonical workflow for Part-2 CRM-driven changes.
All implementation must conform to these 10 steps.
Deviations require explicit amendment to this charter.
