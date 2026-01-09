# Architecture Decision Record (ADR)

**Status:** PENDING_APPROVAL | APPROVED | REJECTED
**Date:** YYYY-MM-DD
**Decision ID:** ADR-XXXX
**Reference:** PIN-XXX (if applicable)

---

## 1. Context

**What is the problem or requirement?**

[Describe the architectural decision that needs to be made]

---

## 2. Proposed Change

**What structural change is being proposed?**

| Item | Value |
|------|-------|
| Change Type | NEW_TABLE / NEW_API / SCHEMA_MODIFICATION / NEW_SERVICE |
| Domain | [Domain name: Activity, Incidents, Policies, etc.] |
| Layer | L1-L8 |
| Files Affected | [List of files] |

---

## 3. Canonical Structure Check (MANDATORY)

**Does a canonical structure already exist for this domain concept?**

| Question | Answer |
|----------|--------|
| Existing table? | YES / NO - [table name if yes] |
| Existing model? | YES / NO - [model name if yes] |
| Existing API? | YES / NO - [endpoint if yes] |
| Existing engine? | YES / NO - [service if yes] |

**If YES to any above:**

Per ARCH-CANON-001, you MUST justify why extension is not possible.

| Extension Approach | Why Not Viable |
|-------------------|----------------|
| Add fields to existing table | [reason or N/A] |
| Add hooks to existing flow | [reason or N/A] |
| Add handlers to existing engine | [reason or N/A] |
| Add constraints/indexes | [reason or N/A] |

---

## 4. Fragmentation Risk Assessment

**What would break if this creates a parallel structure?**

| Risk | Impact |
|------|--------|
| Analytics queries | [Would require JOINs / aggregation across tables?] |
| Policy engine | [Would see incomplete data?] |
| Exports / compliance | [Would miss data?] |
| Backward compatibility | [Would break existing callers?] |

---

## 5. Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | Extend canonical structure | | |
| B | Create new structure | | |
| C | Transitional shim | | |

**Recommended Option:** [A/B/C]

**Justification:**

[Why this option is recommended]

---

## 6. Decision

**Approved by:** [Name/Role]
**Date:** YYYY-MM-DD
**Approval Notes:**

[Any conditions or follow-up required]

---

## 7. Consequences

**What will change as a result of this decision?**

- [ ] Migration required
- [ ] API changes
- [ ] Model changes
- [ ] Engine changes
- [ ] Documentation updates
- [ ] CI/CD updates

---

## Governance Reference

- **ARCH-CANON-001:** Canonical-First Fix Policy
- **ARCH-FRAG-ESCALATE-001:** Fragmentation Escalation Protocol
- **Reference:** `docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md` Sections 13-15
