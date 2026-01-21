# Cross-Domain Policy Contract

**Status:** ACTIVE (IMPLEMENTING)
**Version:** 1.1
**Effective:** 2026-01-19
**Last Updated:** 2026-01-19
**Scope:** Activity ↔ Policy ↔ Incidents
**Reference:** PIN-447, POLICY_DOMAIN_V2_DESIGN.md

---

## Implementation Status

| Binding | Status | Notes |
|---------|--------|-------|
| Activity → Policy (`policy_context`) | ✅ IMPLEMENTED | `facade_ref`, `threshold_ref`, `violation_ref` added |
| Policy V2 Facade | ✅ IMPLEMENTED | 9 endpoints in `/api/v1/policy/*` |
| Incidents → Policy (`policy_binding`) | ⏳ PENDING | Phase 4.2 |
| CI Enforcement | ⏳ PENDING | Phase 5 |
| SDSR Loop Assertions | ✅ CREATED | 4 scenarios awaiting execution |

---

## 0. Prime Invariant (LOCKED)

> **Domains interact only via artifacts and references, never via control flow.**

This contract codifies the allowed and forbidden couplings between Activity, Policy, and Incidents domains.

---

## 1. Artifact Ownership Matrix

| Artifact Type | Owner Domain | Created By | Consumed By |
|---------------|--------------|------------|-------------|
| Run | Activity | Activity Engine | Policy (eval), Incidents (source) |
| Policy | Policy | Human/System | Activity (context), Incidents (link) |
| Violation | Policy | Policy Engine | Incidents (trigger), Logs (audit) |
| Incident | Incidents | Incident Engine | Policy (lessons), Logs (audit) |
| Lesson | Policy | Incident Resolution | Policy (governance) |
| Draft | Policy | Lesson Promotion | Policy (human review) |

**Rule:** Only the owner domain may CREATE or MUTATE an artifact.

---

## 2. Allowed References (Cross-Domain)

### 2.1 Activity → Policy

| Activity May Reference | Via | Purpose |
|------------------------|-----|---------|
| Active policies | `policy_context.policy_id` | Show governance |
| Thresholds | `policy_context.threshold_id` | Show limits |
| Violations | `policy_context.violation_ref` | Link breaches |

**Allowed Operations:**
- ✅ READ policy_context at query time
- ✅ CACHE policy_context for resilience
- ✅ NAVIGATE to policy facade via `facade_ref`

**Forbidden Operations:**
- ❌ EVALUATE policy rules synchronously
- ❌ WRITE to any policy artifact
- ❌ IMPORT internal.policy.* capabilities

### 2.2 Policy → Activity

| Policy May Reference | Via | Purpose |
|----------------------|-----|---------|
| Run ID | `violation.run_id` | Attribution |
| Run metrics | READ from Activity facade | Threshold evaluation |

**Allowed Operations:**
- ✅ READ run data for threshold evaluation
- ✅ RECORD violations with run_id reference

**Forbidden Operations:**
- ❌ MODIFY run state
- ❌ BLOCK run execution synchronously
- ❌ CREATE incidents

### 2.3 Incidents → Policy

| Incidents May Reference | Via | Purpose |
|-------------------------|-----|---------|
| Violation ID | `incident.violation_id` | Causal link |
| Policy ID | `incident.policy_id` | Attribution |

**Allowed Operations:**
- ✅ READ violation from policy facade
- ✅ PROPOSE lesson on resolution
- ✅ NAVIGATE to policy via `violation_ref`

**Forbidden Operations:**
- ❌ CREATE violations
- ❌ MODIFY policy state
- ❌ ACTIVATE policies

### 2.4 Policy → Incidents

| Policy May Reference | Via | Purpose |
|----------------------|-----|---------|
| Incident ID | `lesson.source_incident_id` | Learning source |

**Allowed Operations:**
- ✅ READ incident data for lesson creation
- ✅ LINK lessons to source incidents

**Forbidden Operations:**
- ❌ CREATE incidents
- ❌ RESOLVE incidents
- ❌ MODIFY incident state

---

## 3. Forbidden Couplings (HARD BLOCK)

### 3.1 Synchronous Control Flow

```
❌ Activity calls Policy to "decide" enforcement
❌ Policy calls Incidents to "create" failure record
❌ Incidents calls Policy to "activate" new rule
```

**Why forbidden:** Creates tight coupling, breaks resilience, violates domain sovereignty.

### 3.2 Shared Mutable State

```
❌ Activity and Policy share threshold cache
❌ Incidents and Policy share lesson queue
❌ Any domain writes to another's tables
```

**Why forbidden:** Race conditions, consistency violations, ownership ambiguity.

### 3.3 Bidirectional Dependencies

```
❌ Policy depends on Incidents AND Incidents depends on Policy (cycle)
❌ Activity depends on Policy AND Policy depends on Activity (cycle)
```

**Allowed direction:**
```
Activity → Policy (read only)
Policy → Incidents (read only, for lessons)
Incidents → Policy (read only, for attribution)
```

---

## 4. Facade-Only Access Rule

### Cross-Domain API Access

| Domain | May Call | Must NOT Call |
|--------|----------|---------------|
| Activity | `/api/v1/policy/*` | `/api/v1/policies/*`, `/api/v1/policy-layer/*` |
| Incidents | `/api/v1/policy/*` | `/api/v1/policies/*`, `/api/v1/policy-layer/*` |
| Policy | `/api/v1/activity/*` | Internal activity services |
| Policy | `/api/v1/incidents/*` | Internal incident services |

### Capability Import Rules

```python
# ALLOWED
from app.api.policy import PolicyContext  # Facade types only

# FORBIDDEN
from app.services.policy.engine import PolicyEvaluator  # Internal
from app.models.policy_control_plane import Limit  # Direct model
```

---

## 5. Reference Schema (Canonical)

### policy_context (Activity → Policy)

```python
class PolicyContext(BaseModel):
    """Embedded in every Activity response."""

    # Identity
    policy_id: str
    policy_name: str

    # Facade references (navigable)
    facade_ref: str          # "/policy/active/{policy_id}"
    threshold_ref: str | None    # "/policy/thresholds/{id}"
    violation_ref: str | None    # "/policy/violations/{id}"

    # Evaluation facts (read-only)
    evaluation_outcome: str  # OK, NEAR_THRESHOLD, BREACH
    proximity_pct: float | None
```

### incident_policy_binding (Incidents → Policy)

```python
class IncidentPolicyBinding(BaseModel):
    """Links incident to policy artifacts."""

    # Source
    source_run_id: str

    # Policy reference
    policy_id: str
    policy_ref: str          # "/policy/active/{id}"

    # Violation reference
    violation_id: str
    violation_ref: str       # "/policy/violations/{id}"

    # Lesson reference (if created)
    lesson_id: str | None
    lesson_ref: str | None   # "/policy/lessons/{id}"
```

---

## 6. Event Flow Contracts

### 6.1 Threshold Breach Event

```yaml
event: THRESHOLD_BREACH
producer: Activity
consumers: [Policy]

payload:
  run_id: string
  tenant_id: string
  threshold_id: string
  threshold_value: number
  actual_value: number
  breach_type: BREACH | NEAR_THRESHOLD

contract:
  - Policy MUST record violation within 5s
  - Policy MUST NOT block Activity completion
  - Activity MUST complete regardless of Policy response
```

### 6.2 Violation Recorded Event

```yaml
event: VIOLATION_RECORDED
producer: Policy
consumers: [Incidents]

payload:
  violation_id: string
  run_id: string
  policy_id: string
  breach_type: string

contract:
  - Incidents MAY create incident
  - Incidents MUST link violation_id if incident created
  - Policy MUST NOT wait for Incidents response
```

### 6.3 Incident Resolved Event

```yaml
event: INCIDENT_RESOLVED
producer: Incidents
consumers: [Policy]

payload:
  incident_id: string
  resolution_type: string
  learnings: string | null

contract:
  - Policy MAY create lesson DRAFT
  - Policy MUST link source_incident_id
  - Incidents MUST NOT wait for Policy response
```

---

## 7. Resilience Requirements

### 7.1 Activity Resilience

```yaml
scenario: Policy facade unavailable
requirement: Activity MUST continue with cached policy_context
behavior:
  - Use last known good policy_context
  - Log warning (not error)
  - Complete run normally
  - DO NOT fail run due to Policy unavailability
```

### 7.2 Policy Resilience

```yaml
scenario: Incidents facade unavailable
requirement: Policy MUST record violations regardless
behavior:
  - Record violation to local store
  - Queue incident creation for retry
  - DO NOT block violation recording
```

### 7.3 Incidents Resilience

```yaml
scenario: Policy facade unavailable
requirement: Incidents MUST proceed with incident lifecycle
behavior:
  - Create incident with null policy_ref
  - Backfill policy_ref when available
  - DO NOT block incident creation
```

---

## 8. CI Enforcement

### Guardrail: Cross-Domain Import Check

```yaml
# .github/workflows/cross-domain-guard.yml
name: Cross-Domain Contract Enforcement

checks:
  - name: "Activity cannot import internal Policy"
    files: "backend/app/api/activity.py"
    forbidden_patterns:
      - "from app.services.policy"
      - "from app.models.policy_control_plane"
      - "internal.policy"

  - name: "Incidents cannot import internal Policy"
    files: "backend/app/api/incidents.py"
    forbidden_patterns:
      - "from app.services.policy"
      - "from app.models.policy_control_plane"
      - "internal.policy"

  - name: "Policy cannot import internal Activity"
    files: "backend/app/api/policy.py"
    forbidden_patterns:
      - "from app.services.activity"
      - "from app.models.runs"
```

### Guardrail: Reference Validation

```yaml
checks:
  - name: "policy_context must use facade_ref"
    files: "backend/app/api/activity.py"
    required_patterns:
      - "facade_ref"
      - "/policy/"
```

---

## 9. Violation Handling

### Contract Violation Types

| Type | Severity | Response |
|------|----------|----------|
| Import violation | BLOCK | CI fails, PR cannot merge |
| Control flow violation | BLOCK | Code review rejects |
| Missing reference | WARN | Flagged for review |
| Resilience failure | BLOCK | Must handle unavailability |

### Escalation Path

```
1. CI detects violation
2. PR blocked
3. Architect review required
4. Contract exception requires:
   - Written justification
   - Time-bound exemption
   - Migration plan
```

---

## 10. Contract Evolution

### Amendment Process

1. Propose change via RFC
2. Impact analysis on all three domains
3. Architect approval required
4. Update this document
5. Update CI guards
6. Announce to all domain owners

### Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-01-19 | Initial contract |
| 1.1 | 2026-01-19 | Added implementation status; Activity binding complete |

---

## Appendix: Quick Reference

### Activity Developer

```
✅ Use policy_context from responses
✅ Navigate via facade_ref links
✅ Cache policy_context for resilience
❌ Import anything from app.services.policy
❌ Call policy endpoints synchronously to decide
❌ Write to policy artifacts
```

### Policy Developer

```
✅ Record violations with run_id
✅ Create lessons from incidents
✅ Read from Activity/Incidents facades
❌ Create incidents directly
❌ Modify run state
❌ Block Activity completion
```

### Incidents Developer

```
✅ Link to policy violations
✅ Propose lessons on resolution
✅ Navigate via policy_ref links
❌ Create violations
❌ Activate policies
❌ Import internal policy services
```
