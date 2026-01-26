# Policy Domain V2 — Canonical Design

**Status:** APPROVED → IMPLEMENTING
**Version:** 2.1
**Effective:** 2026-01-19
**Last Updated:** 2026-01-19
**Authors:** Claude Opus 4.5 + GPT-4 Architecture Review
**Reference:** PIN-447

---

## Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | V2 Facade Endpoints | ✅ COMPLETE |
| Phase 2 | Detail Endpoints (O3) | ✅ COMPLETE |
| Phase 3 | Capability Registry | ✅ COMPLETE |
| Phase 4.1 | Activity Cross-Domain Binding | ✅ COMPLETE |
| Phase 4.2 | Incidents Cross-Domain Binding | ✅ COMPLETE |
| Phase 5 | CI Enforcement | ✅ COMPLETE |
| SDSR | Loop Assertion Scenarios | ✅ CREATED (awaiting execution) |
| Constitution | Cross-Domain Invariants | ✅ LOCKED |

---

## 0. Design Position (LOCKED)

### Prime Directive

> **Policy participates in feedback loops only via *artifacts*, never via control flow.**

This is the load-bearing invariant. Everything else flows from this.

### Domain Identity

| Domain | Role | NOT |
|--------|------|-----|
| **Activity** | Execution facts | Interpretation |
| **Incidents** | Failure manifestation | Cause analysis |
| **Policy** | Governance artifacts | Orchestration |

**Policy governs Activity and explains Incidents — it does not control them.**

---

## 1. Three-Domain Loop Architecture (LOCKED)

### 1.1 Activity → Policy (Read-Only, Continuous)

**Nature:** 📥 Consumption

```
Activity:
  - Executes runs
  - Evaluates against ALREADY MATERIALIZED policy_context
  - Emits facts, not interpretations

Policy:
  - Is NEVER invoked to decide
  - Is NEVER mutated by Activity
  - Is NEVER consulted synchronously
```

**Critical Rule:**
> Activity may only embed `policy_context` **by reference**, never by re-evaluation.

### 1.2 Activity → Policy → Incidents (Eventual, Mandatory)

**Nature:** 📜 Recording → Manifestation

```
Flow:
  1. Activity detects threshold breach
  2. Policy RECORDS a violation (append-only)
  3. Incidents MATERIALIZES failure

Key constraints:
  - Policy does NOT create incidents
  - Incidents do NOT evaluate policy
  - The link is THE VIOLATION ARTIFACT
```

**This keeps:**
- Policy = audit truth
- Incidents = failure lifecycle

### 1.3 Incidents → Policy (Learning Loop, Human-Gated)

**Nature:** 🧠 Governance feedback

```
Flow:
  1. Incident resolution PROPOSES learning
  2. Policy records DRAFT lesson
  3. Humans decide promotion
  4. Only THEN does Policy affect future Activity
```

**Hard Invariant (LOCKED):**
> **No policy change is allowed without passing through a human-visible DRAFT state.**

This includes SYSTEM defaults. No exceptions.

---

## 2. Domain Structure (PRESERVED)

### Subdomain Architecture

```
Policy Domain
├── GOVERNANCE (Human decisions)
│   ├── ACTIVE      → What governs now (enforced)
│   ├── DRAFTS      → What awaits decision (pre-approval)
│   ├── LESSONS     → What we learned (post-analysis)
│   └── LIBRARY     → What's available (catalog)
└── LIMITS (Machine enforcement)
    ├── THRESHOLDS  → What limits exist (config)
    └── VIOLATIONS  → What was enforced (audit)
```

**Why subdomains are preserved:**
- GOVERNANCE = Human authority (approve, reject, learn)
- LIMITS = Machine authority (enforce, record, audit)

Collapsing these would lose the governance/enforcement boundary.

### DRAFTS vs LESSONS (DISTINCT)

| Topic | Lifecycle | Owner | Purpose |
|-------|-----------|-------|---------|
| **DRAFTS** | Pre-approval | Human decision | Proposed policies awaiting review |
| **LESSONS** | Post-incident | Human learning | Emerged patterns informing future |

These remain separate — merging them would conflate proposal with learning.

---

## 3. V2 Facade Layer (GOVERNANCE FIREWALL)

### Facade Purpose

The `/api/v1/policy/*` facade is **not an API convenience**.
It is a **governance firewall**.

### Facade Responsibilities

| DO | DO NOT |
|----|--------|
| Answer authority questions | Expose O2-O5 reasoning |
| Provide stable references | Accept mutations |
| Hide internal complexity | Contain workflow logic |
| Prevent capability sprawl | Mirror internal subdomains |

### Facade Endpoints (5 Authority Surfaces)

```http
GET /api/v1/policy/active      → What governs execution now?
GET /api/v1/policy/library     → What patterns are available?
GET /api/v1/policy/lessons     → What governance emerged?
GET /api/v1/policy/controls    → What limits are enforced?
GET /api/v1/policy/violations  → What enforcement occurred?
```

### Response Schema (Mandatory Fields)

```python
class PolicyActiveResponse(BaseModel):
    """GET /policy/active response."""
    data: list[PolicySummary]
    total: int

class PolicySummary(BaseModel):
    policy_id: str
    name: str
    scope: str  # TENANT, PROJECT, AGENT, PROVIDER, GLOBAL
    enforcement: str  # HARD, SOFT, ADVISORY
    applies_to: list[str]  # ["ACTIVITY", "INCIDENTS"]
    effective_from: datetime
    # Reference for cross-domain navigation
    facade_ref: str  # "/policy/active/{policy_id}"
```

---

## 4. Capability Architecture (LOAD-BEARING WALL)

### The Split (Non-Negotiable)

```yaml
# FACADE CAPABILITIES (Cross-Domain Visible)
policy.active:
  endpoint: /policy/active
  cross_domain: true
  consumers: [activity, incidents, logs]

policy.library:
  endpoint: /policy/library
  cross_domain: true
  consumers: [activity]

policy.lessons:
  endpoint: /policy/lessons
  cross_domain: true
  consumers: [incidents]

policy.controls:
  endpoint: /policy/controls
  cross_domain: true
  consumers: [activity]

policy.violations:
  endpoint: /policy/violations
  cross_domain: true
  consumers: [incidents, logs]

# INTERNAL CAPABILITIES (Policy Domain Only)
internal.policy.governance.*:
  cross_domain: false
  consumers: [policy_ui_only]

internal.policy.limits.*:
  cross_domain: false
  consumers: [policy_ui_only]
```

### CI Enforcement (MANDATORY)

```yaml
# .github/workflows/capability-boundaries.yml
rules:
  - name: "Activity cannot import internal.policy.*"
    pattern: "backend/app/api/activity.py"
    forbidden: "internal.policy"

  - name: "Incidents cannot import internal.policy.*"
    pattern: "backend/app/api/incidents.py"
    forbidden: "internal.policy"

  - name: "Only policy facade exposed cross-domain"
    allowed_exports:
      - policy.active
      - policy.library
      - policy.lessons
      - policy.thresholds
      - policy.violations
```

---

## 5. O-Level Depth (VIEWS, NOT SURFACES)

### Correct Mental Model

O1-O5 are:
- ✅ Progressive disclosure
- ✅ Investigation depth
- ✅ Human navigation aids
- ✅ UI presentation layers

O1-O5 are NOT:
- ❌ Architecture
- ❌ Contracts
- ❌ Domain boundaries
- ❌ API surfaces

### Facade vs Depth

| Level | Facade Visibility | Internal Depth |
|-------|-------------------|----------------|
| O1 | ✅ Evidence (facade response) | — |
| O2 | ❌ Internal only | List details |
| O3 | ✅ Detail endpoint (`/{id}`) | Explanation |
| O4 | ⚠️ Preflight only | Evidence/context |
| O5 | ⚠️ Preflight only | Raw proof |

### Panel Mapping (Preserved)

```
Facade: /policy/active
  └── POL-GOV-ACT-O1 (evidence) → Facade response
  └── POL-GOV-ACT-O2 (interpretation) → Internal depth
  └── POL-GOV-ACT-O3 (interpretation) → Internal depth
  └── POL-GOV-ACT-O4 (execution) → Internal depth
  └── POL-GOV-ACT-O5 (interpretation) → Internal depth
```

All 30 panels remain. O2-O5 become internal implementation details.

---

## 6. Cross-Domain Binding (policy_context)

### Activity's policy_context

```python
class PolicyContext(BaseModel):
    """Advisory metadata showing why a run is at-risk."""

    # Identity (stable references)
    policy_id: str
    policy_name: str
    facade_ref: str  # "/policy/active/{policy_id}" - navigable

    # Classification
    policy_scope: str  # TENANT, PROJECT, AGENT, PROVIDER, GLOBAL
    limit_type: str | None

    # Threshold reference
    threshold_id: str | None
    threshold_ref: str | None  # "/policy/thresholds/{id}" - navigable
    threshold_value: float | None
    threshold_unit: str | None
    threshold_source: str

    # Evaluation (facts, not decisions)
    evaluation_outcome: str  # OK, NEAR_THRESHOLD, BREACH, OVERRIDDEN, ADVISORY
    actual_value: float | None
    risk_type: str | None  # COST, TIME, TOKENS, RATE, OTHER
    proximity_pct: float | None

    # Violation reference (if breached)
    violation_ref: str | None  # "/policy/violations/{id}" - navigable
```

### Incidents' policy_context

```python
class IncidentPolicyBinding(BaseModel):
    """Links incident to policy enforcement."""

    # Source
    source_run_id: str

    # Policy that was violated
    policy_id: str
    policy_ref: str  # "/policy/active/{id}"

    # Violation record
    violation_id: str
    violation_ref: str  # "/policy/violations/{id}"

    # Lesson (if created)
    lesson_id: str | None
    lesson_ref: str | None  # "/policy/lessons/{id}"
```

---

## 7. Feedback Loop Diagram (Complete)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     IMPLICIT FEEDBACK LOOP                              │
│              (Artifact-based, never control-flow)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐                                                       │
│  │   ACTIVITY   │                                                       │
│  │  (Execution) │                                                       │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         │ 1. Run executes                                               │
│         │    policy_context evaluated (READ-ONLY)                       │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────────────────────────┐                                   │
│  │ Threshold breached?              │                                   │
│  └──────────────┬───────────────────┘                                   │
│                 │                                                       │
│       ┌─────────┴─────────┐                                             │
│       │                   │                                             │
│       ▼ YES               ▼ NO                                          │
│  ┌──────────┐        ┌──────────┐                                       │
│  │  POLICY  │        │ Complete │                                       │
│  │VIOLATION │        │ normally │                                       │
│  │(recorded)│        └──────────┘                                       │
│  └────┬─────┘                                                           │
│       │                                                                 │
│       │ 2. Violation ARTIFACT created                                   │
│       │    (append-only, immutable)                                     │
│       │                                                                 │
│       ▼                                                                 │
│  ┌──────────────┐                                                       │
│  │  INCIDENTS   │                                                       │
│  │(Manifestation│                                                       │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         │ 3. Incident created (MANDATORY)                               │
│         │    Links to violation_ref                                     │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                       │
│  │   RESOLVED   │                                                       │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         │ 4. Resolution PROPOSES lesson                                 │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                       │
│  │    POLICY    │                                                       │
│  │    DRAFT     │◄─────────────────────────────────────────────────────┐│
│  │   (lesson)   │                                                      ││
│  └──────┬───────┘                                                      ││
│         │                                                              ││
│         │ 5. HUMAN reviews                                             ││
│         │    (MANDATORY gate)                                          ││
│         │                                                              ││
│    ┌────┴────┐                                                         ││
│    │         │                                                         ││
│    ▼         ▼                                                         ││
│ APPROVE   REJECT                                                       ││
│    │         │                                                         ││
│    │         └──────────► Archived                                     ││
│    │                                                                   ││
│    ▼                                                                   ││
│  ┌──────────────┐                                                      ││
│  │    POLICY    │                                                      ││
│  │    ACTIVE    │──────────────────────────────────────────────────────┘│
│  │  (enforced)  │                                                       │
│  └──────────────┘                                                       │
│         │                                                               │
│         │ 6. LOOP CLOSED                                                │
│         │    Future runs governed by updated policy                     │
│         │                                                               │
│         └───────────────────► Back to ACTIVITY                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. SDSR Loop Assertions (MANDATORY)

### Assertion 1: Violation Before Incident

```yaml
assertion: SDSR-LOOP-001
rule: A policy violation MUST exist BEFORE an incident exists
test: |
  Given a breach scenario
  When incident is created
  Then violation_id must be non-null
  And violation.created_at < incident.created_at
```

### Assertion 2: Lesson References Source

```yaml
assertion: SDSR-LOOP-002
rule: A lesson MUST reference an incident OR violation
test: |
  Given a lesson exists
  Then lesson.source_incident_id IS NOT NULL
    OR lesson.source_violation_id IS NOT NULL
```

### Assertion 3: Active Policy Has Origin

```yaml
assertion: SDSR-LOOP-003
rule: An active policy MUST reference a prior draft OR system origin
test: |
  Given an active policy
  Then policy.origin IN ('DRAFT_PROMOTED', 'SYSTEM_DEFAULT')
  And IF origin = 'DRAFT_PROMOTED'
    THEN draft_id IS NOT NULL
```

### Assertion 4: Activity Resilience

```yaml
assertion: SDSR-LOOP-004
rule: Activity MUST NOT change behavior if Policy facade is unavailable
test: |
  Given Policy facade returns 503
  When Activity processes a run
  Then run uses cached policy_context
  And run completes (does not fail)
```

---

## 9. Migration Plan (Safe, Incremental)

### Phase 1: Add V2 Facade (Non-Breaking) ✅ COMPLETE

```python
# backend/app/api/policy.py (IMPLEMENTED)
# Layer: L2 — Product APIs
# Role: Policy V2 Facade - governance firewall

router = APIRouter(prefix="/api/v1/policy", tags=["policy-v2-facade"])

@router.get("/active")
@router.get("/library")
@router.get("/lessons")
@router.get("/controls")
@router.get("/violations")
```

**Deliverables:**
- [x] Create `backend/app/api/policy.py` (added to existing file)
- [x] Wire to main.py (already wired)
- [x] Map from existing services
- [x] Zero behavior change

### Phase 2: Add Detail Endpoints ✅ COMPLETE

```python
@router.get("/active/{policy_id}")           # O3 ✅
@router.get("/controls/{control_id}")        # O3 ✅
@router.get("/violations/{violation_id}")    # O3 ✅
@router.get("/lessons/{lesson_id}")          # O3 ✅
# O4/O5 endpoints deferred to future phase
```

### Phase 3: Capability Registry Update ✅ COMPLETE

```yaml
# Created facade capabilities (in AURORA_L2_CAPABILITY_REGISTRY):
policy.active      ✅ AURORA_L2_CAPABILITY_policy.active.yaml
policy.library     ✅ AURORA_L2_CAPABILITY_policy.library.yaml
policy.lessons     ✅ AURORA_L2_CAPABILITY_policy.lessons.yaml
policy.controls    ✅ AURORA_L2_CAPABILITY_policy.controls.yaml
policy.violations  ✅ AURORA_L2_CAPABILITY_policy.violations.yaml

# Status: DECLARED (awaiting SDSR observation → OBSERVED)
```

### Phase 4: Cross-Domain Rebind 🔄 IN PROGRESS

- [x] Activity consumes `policy.*` facades with `facade_ref`, `threshold_ref`, `violation_ref`
- [ ] Incidents consumes only `policy.*` facades
- [ ] Logs references `policy_context` with `facade_ref`
- [ ] CI blocks internal capability imports

### Phase 5: Deprecation (Optional, Later)

- [ ] Mark `/policy-layer/*` as deprecated
- [ ] Keep `/policies/*` for admin depth
- [ ] Monitor usage, remove when safe

---

## 10. Explicit Non-Goals (LOCKED)

| Feature | Status | Rationale |
|---------|--------|-----------|
| Policy evaluation endpoints | ❌ NOT NOW | Belongs to future simulation |
| Inline mutation | ❌ NEVER | Violates artifact-only rule |
| Policy simulator | ❌ NOT NOW | Phase 2 upgrade candidate |
| Cross-domain writes | ❌ NEVER | Domains are sovereign |
| Auto-tuning | ❌ NEVER | Human gate is mandatory |
| Silent feedback | ❌ NEVER | DRAFT state required |

---

## 11. Files to Create/Modify

| File | Action | Status | Purpose |
|------|--------|--------|---------|
| `backend/app/api/policy.py` | MODIFY | ✅ DONE | V2 facade implementation (added to existing) |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policy.active.yaml` | CREATE | ✅ DONE | Facade capability |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policy.library.yaml` | CREATE | ✅ DONE | Facade capability |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policy.lessons.yaml` | CREATE | ✅ DONE | Facade capability |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policy.controls.yaml` | CREATE | ✅ DONE | Facade capability |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policy.violations.yaml` | CREATE | ✅ DONE | Facade capability |
| `backend/scripts/sdsr/scenarios/SDSR-POL-LOOP-001.yaml` | CREATE | ✅ DONE | Violation before incident |
| `backend/scripts/sdsr/scenarios/SDSR-POL-LOOP-002.yaml` | CREATE | ✅ DONE | Lesson references source |
| `backend/scripts/sdsr/scenarios/SDSR-POL-LOOP-003.yaml` | CREATE | ✅ DONE | Active policy has origin |
| `backend/scripts/sdsr/scenarios/SDSR-POL-LOOP-004.yaml` | CREATE | ✅ DONE | Activity resilience |
| `backend/app/api/activity.py` | MODIFY | ✅ DONE | PolicyContext with facade refs |
| `backend/app/api/incidents.py` | MODIFY | ✅ DONE | IncidentPolicyBinding (policy_ref, violation_ref) |
| `.github/workflows/cross-domain-policy-guard.yml` | CREATE | ✅ DONE | CI enforcement |
| `docs/contracts/CROSS_DOMAIN_POLICY_CONTRACT.md` | MODIFY | ✅ DONE | Binding rules (v1.1) |
| `docs/contracts/CROSS_DOMAIN_INVARIANTS.md` | CREATE | ✅ DONE | Constitutional layer (15 invariants) |

---

## 12. Cross-Domain Contract (Next Step)

**Recommended next action:**

> Write a Cross-Domain Contract Doc — not APIs, not schemas, but **allowed references and forbidden couplings**.

This document will protect the design long-term by codifying:
- What Activity can reference from Policy
- What Incidents can reference from Policy
- What Policy can reference from Incidents (lessons only)
- Forbidden bidirectional dependencies
- Artifact ownership boundaries

---

## Appendix A: Capability Registry (Full)

### Facade Capabilities

```yaml
policy.active:
  status: DECLARED
  endpoint: GET /api/v1/policy/active
  panels: [POL-GOV-ACT-O1]
  cross_domain: true

policy.library:
  status: DECLARED
  endpoint: GET /api/v1/policy/library
  panels: [POL-GOV-LIB-O1]
  cross_domain: true

policy.lessons:
  status: DECLARED
  endpoint: GET /api/v1/policy/lessons
  panels: [POL-GOV-LES-O1, POL-GOV-DFT-O1]
  cross_domain: true

policy.controls:
  status: DECLARED
  endpoint: GET /api/v1/policy/controls
  panels: [POL-LIM-CTR-O1]
  cross_domain: true

policy.violations:
  status: DECLARED
  endpoint: GET /api/v1/policy/violations
  panels: [POL-LIM-VIO-O1]
  cross_domain: true
```

### Internal Capabilities (Partial)

```yaml
internal.policy.governance.metrics:
  status: ASSUMED
  endpoint: GET /api/v1/policies/metrics
  panels: [POL-GOV-ACT-O2, POL-GOV-ACT-O5]
  cross_domain: false

internal.policy.limits.config:
  status: ASSUMED
  endpoint: PUT /api/v1/policies/limits/{id}/params
  panels: [POL-LIM-CTR-O3]
  cross_domain: false
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Facade** | The 5 cross-domain visible endpoints |
| **Internal** | O2-O5 depth, policy domain only |
| **Artifact** | Immutable record (violation, lesson, policy) |
| **Control flow** | Synchronous domain-to-domain calls (FORBIDDEN) |
| **Reference** | Navigable link to another domain's facade |
| **Human gate** | Mandatory DRAFT → ACTIVE promotion by human |

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-19 | 2.0 | Initial V2 design with GPT architecture review |
| 2026-01-19 | 2.1 | Implementation progress: Phase 1-3 complete, Phase 4.1 complete |
| 2026-01-19 | 2.2 | Implementation complete: Phase 4.2, Phase 5, Constitutional layer |

### Implementation Details (2026-01-19)

**Completed:**
- V2 facade endpoints added to `backend/app/api/policy.py` (9 endpoints total)
- 5 capability registry YAML files created with status DECLARED
- 4 SDSR loop assertion scenarios created
- Activity's `PolicyContext` model updated with `facade_ref`, `threshold_ref`, `violation_ref`
- `_extract_policy_context()` helper updated to populate navigation refs
- Incidents' policy binding with `policy_ref`, `violation_ref`, `lesson_ref` (as Optional)
- CI enforcement guardrails in `.github/workflows/cross-domain-policy-guard.yml`
- Constitutional layer in `docs/contracts/CROSS_DOMAIN_INVARIANTS.md`

**Pending:**
- Execute SDSR scenarios to move capabilities from DECLARED → OBSERVED
- Database schema evolution to add `policy_id`, `violation_id` to incidents table

