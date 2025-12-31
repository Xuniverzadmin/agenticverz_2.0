# CI Signal Ownership Assignment Framework

**Status:** DRAFT — Awaiting Human Ratification
**Date:** 2025-12-31
**Purpose:** Mechanical framework for depoliticized CI signal owner assignment
**Reference:** TASK-GOV-014, PIN-262, PRODUCT_DEVELOPMENT_CONTRACT_V3.md

---

## 1. Why This Framework Exists

**The Problem:**

> 18 of 22 CI signals have no documented owner.
> This is a P0 governance defect blocking Phase 1 exit.

**Why Ownership Matters:**

Ownership defines **who absorbs pain when CI fails**.

Without ownership:
- Failures have no responder
- CI green has no accountability
- Enforcement is accidental
- The system becomes a noise generator, not a control system

**Why Mechanical Assignment:**

Political ownership assignment produces:
- Opinion-based owners (loudest voice wins)
- Seniority-based owners (tenure, not competence)
- Convenience-based owners (whoever is available)

These produce **fake owners** and **silent failures**.

A mechanical framework prevents that.

---

## 2. Ownership Definition (Non-Negotiable)

### What an Owner IS

An owner is a **named entity** (human or role) who:

1. **Is notified** when the signal fails
2. **Is expected to respond** within a defined SLA
3. **Has authority** to triage, escalate, or resolve
4. **Bears accountability** for chronic failures

### What an Owner is NOT

An owner is NOT:
- A team (teams don't respond; individuals do)
- A fallback (no "if unavailable, then...")
- Optional (every blocking signal requires an owner)
- Ceremonial (owner must have actual authority)

### Ownership Contract

Every assigned owner implicitly accepts:

```
I accept responsibility for this CI signal.
If it fails:
  - I will be notified
  - I will respond within SLA
  - I will either fix, triage, or escalate
  - I accept that chronic failures reflect on my stewardship
```

---

## 3. Owner Eligibility Criteria (Mechanical)

An entity is eligible to own a signal if ALL of the following are true:

| Criterion | Test | Pass/Fail |
|-----------|------|-----------|
| **C1: Contact Reachable** | Owner has valid notification channel (email, Slack, PagerDuty) | Required |
| **C2: Response Capable** | Owner can respond within 24h (blocking) or 72h (advisory) | Required |
| **C3: Domain Competent** | Owner understands what the signal tests | Required |
| **C4: Authority Present** | Owner can merge fixes or escalate to someone who can | Required |
| **C5: Single Point** | Exactly one owner per signal (no "co-owners") | Required |

**If any criterion fails, the candidate is ineligible.**

---

## 4. Signal Classification (Determines Owner Type)

Signals fall into three accountability tiers:

### Tier 1: CRITICAL (Governance Owned)

Signals that protect **system invariants** or **governance rules**.

| Signal | Current Owner | Rationale |
|--------|---------------|-----------|
| SIG-003 (truth-preflight) | Governance | Protects truth-grade system |
| SIG-006 (c1-guard) | Governance | Protects C1 invariants |
| SIG-007 (c2-guard) | Governance | Protects C2 invariants |

**Rule:** These cannot be reassigned without governance ratification.

### Tier 2: BLOCKING (Individual Owned)

Signals that **block merge** and require human response.

| Signal | Required Owner Type |
|--------|---------------------|
| SIG-001 (ci) | Individual with backend authority |
| SIG-002 (ci-preflight) | Individual with CI authority |
| SIG-004 (import-hygiene) | Individual with backend authority |
| SIG-005 (integration) | Individual with full-stack authority |
| SIG-008 (determinism) | Individual with SDK authority |
| SIG-012 (mypy) | Individual with backend authority |
| SIG-013 (m4-ci) | Individual with workflow authority |
| SIG-014 (m4-signoff) | Individual with workflow authority |
| SIG-018 (prom-rules) | Individual with ops authority |
| SIG-020 (deploy) | Individual with deployment authority |
| SIG-021 (m9-prod) | Individual with production authority |
| SIG-022 (webhook-build) | Individual with build authority |

### Tier 3: ADVISORY (Role Owned)

Signals that **do not block merge** and produce informational output.

| Signal | Acceptable Owner Type |
|--------|----------------------|
| SIG-009 (e2e-parity) | Role (SDK Team) |
| SIG-015 (k6-load) | Role (Performance) |
| SIG-016 (nightly) | Role (Performance) |
| SIG-017 (m7-smoke) | Role (QA/Ops) |
| SIG-019 (failure-agg) | Role (Ops) |

**Rule:** Advisory signals may have role owners, but roles must have a designated primary contact.

---

## 5. Assignment Process (Step-by-Step)

### Step 1: Signal Inventory Verification

Confirm the signal inventory is complete:

```
Total signals: 22
Already owned: 4 (SIG-003, SIG-006, SIG-007, SIG-010, SIG-011)
Requiring assignment: 17
```

### Step 2: Candidate Identification

For each unowned signal, identify candidates:

| Signal | Domain | Candidate Pool |
|--------|--------|----------------|
| SIG-001 | Backend/CI | Humans with backend merge authority |
| SIG-002 | CI | Humans with CI merge authority |
| SIG-004 | Backend | Humans with backend merge authority |
| ... | ... | ... |

### Step 3: Eligibility Screening

For each candidate, verify against C1-C5 criteria:

```
Candidate: [Name]
Signal: SIG-XXX
C1 (Contact): YES/NO
C2 (Response): YES/NO
C3 (Domain): YES/NO
C4 (Authority): YES/NO
C5 (Single): YES/NO
Result: ELIGIBLE / INELIGIBLE
```

### Step 4: Assignment Decision

The human with governance authority selects from eligible candidates.

**Selection heuristics (in order of priority):**

1. **Domain proximity** — Who is closest to the code this signal tests?
2. **Historical involvement** — Who has fixed failures in this signal before?
3. **Authority alignment** — Whose existing authority most overlaps?

**Anti-heuristics (explicitly forbidden):**

- Seniority (tenure ≠ accountability)
- Availability (busy ≠ incapable)
- Volunteering (willingness ≠ competence)
- Rotation (accountability ≠ shared)

### Step 5: Registration

Update `CI_SIGNAL_REGISTRY.md` with assignment:

```yaml
Signal ID: SIG-XXX
Owner: [Name or Role]
Owner Type: Individual / Role
Notification Channel: [email/slack/pagerduty]
Response SLA: 24h (BLOCKING) / 72h (ADVISORY)
Assignment Date: YYYY-MM-DD
Rationale: [Brief justification]
```

### Step 6: Acknowledgment

Owner must explicitly acknowledge:

```
I acknowledge ownership of SIG-XXX.
I accept the ownership contract defined in CI_SIGNAL_OWNERSHIP_FRAMEWORK.md.
Date: YYYY-MM-DD
Signature: [Name]
```

**Without acknowledgment, assignment is invalid.**

---

## 6. Owner Responsibilities (Post-Assignment)

| Responsibility | SLA | Enforcement |
|----------------|-----|-------------|
| Respond to failure notification | 24h (BLOCKING) / 72h (ADVISORY) | Escalation |
| Triage failure cause | Within response window | Escalation |
| Fix or delegate fix | Best effort | Tracking |
| Escalate if blocked | Immediately | Tracking |
| Report chronic failures | Weekly | Governance review |

### Escalation Path

If owner cannot respond:

1. Owner notifies backup contact
2. Backup assumes temporary ownership
3. Governance records the gap
4. Post-incident review assesses need for reassignment

---

## 7. Ownership Transfer (When Needed)

Ownership transfer is permitted when:

- Owner leaves organization
- Owner's domain changes
- Owner becomes chronically unavailable
- Owner requests transfer (with replacement)

Transfer process:

1. Current owner nominates replacement
2. Replacement passes eligibility screening (C1-C5)
3. Replacement acknowledges ownership contract
4. Registry updated with new owner
5. Old owner's acknowledgment archived

**Transfer is NOT permitted:**

- Without replacement
- Without acknowledgment
- By governance alone (owner must participate)

---

## 8. Validation Rules (Prevents Gaming)

| Rule | Test | Violation Response |
|------|------|-------------------|
| No co-owners | Count(owners) == 1 | Reject assignment |
| No team owners for blocking signals | Owner is individual | Reject assignment |
| No unacknowledged owners | Acknowledgment exists | Assignment invalid |
| No orphan signals | All blocking signals owned | Phase 1 blocked |
| No fake owners | Owner has responded to >=1 failure | Flagged for review |

---

## 9. Unowned Signal List (Current State)

| Signal | Classification | Required Owner Type | Status |
|--------|---------------|---------------------|--------|
| SIG-001 | CRITICAL_UNOWNED | Individual (backend) | **P0** |
| SIG-002 | NEEDS_OWNER | Individual (CI) | Pending |
| SIG-004 | NEEDS_OWNER | Individual (backend) | Pending |
| SIG-005 | NEEDS_OWNER | Individual (full-stack) | Pending |
| SIG-008 | NEEDS_OWNER | Individual (SDK) | Pending |
| SIG-009 | NEEDS_OWNER | Role (SDK Team) | Pending |
| SIG-012 | NEEDS_OWNER | Individual (backend) | Pending |
| SIG-013 | NEEDS_OWNER | Individual (workflow) | Pending |
| SIG-014 | NEEDS_OWNER | Individual (workflow) | Pending |
| SIG-015 | NEEDS_OWNER | Role (Performance) | Pending |
| SIG-016 | NEEDS_OWNER | Role (Performance) | Pending |
| SIG-017 | NEEDS_OWNER | Role (QA/Ops) | Pending |
| SIG-018 | NEEDS_OWNER | Individual (ops) | Pending |
| SIG-019 | NEEDS_OWNER | Role (Ops) | Pending |
| SIG-020 | NEEDS_OWNER | Individual (deployment) | Pending |
| SIG-021 | NEEDS_OWNER | Individual (production) | Pending |
| SIG-022 | NEEDS_OWNER | Individual (build) | Pending |

**Total unowned: 17**
**P0 (critical): 1 (SIG-001)**

---

## 10. Phase 1 Exit Condition (Ownership)

Phase 1 **cannot close** until:

- [ ] All 17 unowned signals have assigned owners
- [ ] All assignments have acknowledgments
- [ ] SIG-001 (Main CI) has individual owner (not role)
- [ ] CI_SIGNAL_REGISTRY.md updated with all assignments
- [ ] This framework document is ratified

**Human action required. Claude cannot perform this work.**

---

## 11. Anti-Patterns (Explicitly Forbidden)

| Anti-Pattern | Description | Why Forbidden |
|--------------|-------------|---------------|
| **The Volunteer Trap** | Assigning to whoever volunteers | Willingness ≠ competence |
| **The Senior Dump** | Assigning to most senior person | Tenure ≠ accountability |
| **The Team Spread** | "The team owns it" | Teams don't respond; individuals do |
| **The Rotation Fantasy** | "We'll rotate ownership" | Accountability cannot be shared |
| **The Ghost Owner** | Assign and forget | Ownership without engagement is fake |
| **The Convenience Assignment** | Assign to whoever is free | Availability ≠ authority |

---

## 12. Governance Tasks

| Task ID | Description | Status |
|---------|-------------|--------|
| TASK-GOV-014 | Produce this framework | DRAFT (awaiting ratification) |
| TASK-GOV-015 | Assign all 17 unowned signals | PENDING (requires human action) |
| TASK-GOV-016 | Collect acknowledgments | PENDING (follows TASK-GOV-015) |
| TASK-GOV-017 | Update CI_SIGNAL_REGISTRY.md | PENDING (follows TASK-GOV-016) |

---

## 13. Related Documents

| Document | Relationship |
|----------|--------------|
| CI_SIGNAL_REGISTRY.md | Signal inventory |
| PRODUCT_DEVELOPMENT_CONTRACT_V3.md | Phase 1 requirements |
| docs/ci/scd/INDEX.md | SCD gap index |
| docs/ci/scd/SCD-L8-ALL-BOUNDARY.md | L8↔All boundary discovery |
| PIN-262 | SCD governance clarification |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | Initial framework draft |

---

## Ratification

This framework requires human ratification before use.

**Ratification Statement:**

> "I have reviewed the CI Signal Ownership Assignment Framework.
> I accept it as the authoritative process for signal ownership assignment.
> I understand that ownership assignment is a human responsibility that cannot be delegated to automation."

**Ratified by:** ________________
**Date:** ________________
