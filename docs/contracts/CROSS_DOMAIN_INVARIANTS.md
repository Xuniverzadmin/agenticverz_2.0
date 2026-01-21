# Cross-Domain Invariants (Constitutional Layer)

**Status:** LOCKED
**Version:** 1.0
**Effective:** 2026-01-19
**Scope:** Activity, Policy, Incidents
**Reference:** PIN-447, POLICY_DOMAIN_V2_DESIGN.md

---

## Purpose

This document is the **constitutional layer** for cross-domain interactions.
These are not guidelines. They are **hard invariants** that CI enforces.

Violation of any invariant is a **blocking failure**.

---

## I. Domain Sovereignty Invariants

### INV-DOM-001: Incidents May Not Evaluate Policy

```
FORBIDDEN:
  - Incidents querying /policy/active to reason about enforcement
  - Incidents computing threshold proximity
  - Incidents deciding if a violation "should" exist

ALLOWED:
  - Incidents storing policy_id, violation_id as references
  - Incidents reading /policy/violations/{id} for display
  - Incidents proposing lessons (DRAFT state only)
```

**Rationale:** Incidents are narrators, not judges. Policy domain owns enforcement truth.

---

### INV-DOM-002: Policy May Not Mutate From Signals

```
FORBIDDEN:
  - Policy auto-activating rules based on incident patterns
  - Policy adjusting thresholds from Activity metrics
  - Policy creating lessons without human review
  - Any policy change without DRAFT → ACTIVE human gate

ALLOWED:
  - Policy recording violations (append-only)
  - Policy creating lesson DRAFTs from incident resolution
  - Policy reading Activity/Incidents facades for context
```

**Rationale:** Policy governs through artifacts. It does not self-tune.

---

### INV-DOM-003: Activity Must Run Without Live Policy Access

```
REQUIREMENT:
  - Activity MUST complete runs if Policy facade returns 503
  - Activity MUST use cached policy_context
  - Activity MUST NOT fail due to Policy unavailability
  - Activity MUST log warning (not error) on Policy timeout

FORBIDDEN:
  - Activity blocking on Policy response
  - Activity failing runs due to Policy errors
  - Activity re-evaluating policy synchronously
```

**Rationale:** Activity is the source of execution truth. Policy unavailability cannot corrupt it.

---

### INV-DOM-004: All Learning Is Human-Gated

```
REQUIREMENT:
  - Every lesson MUST pass through DRAFT state
  - Every policy activation MUST have human approval
  - Every threshold change MUST be auditable

FORBIDDEN:
  - Auto-promoting lessons to active policy
  - Silent threshold adjustments
  - System-originated policy without human review
```

**Rationale:** Governance requires accountability. Automation is advisory, never authoritative.

---

## II. Boundary Enforcement Invariants

### INV-BOUND-001: Facade-Only Cross-Domain Access

```
ALLOWED ENDPOINTS (cross-domain):
  - GET /api/v1/policy/active
  - GET /api/v1/policy/active/{id}
  - GET /api/v1/policy/library
  - GET /api/v1/policy/lessons
  - GET /api/v1/policy/lessons/{id}
  - GET /api/v1/policy/thresholds
  - GET /api/v1/policy/thresholds/{id}
  - GET /api/v1/policy/violations
  - GET /api/v1/policy/violations/{id}

FORBIDDEN ENDPOINTS (cross-domain):
  - /api/v1/policies/* (internal admin)
  - /api/v1/policy-layer/* (internal operations)
  - Any POST/PUT/DELETE to /api/v1/policy/*
```

**Rationale:** The facade is the governance firewall. Internal endpoints are for Policy domain only.

---

### INV-BOUND-002: No Internal Import Leakage

```
FORBIDDEN IMPORTS (in Activity):
  - from app.services.policy.*
  - from app.models.policy_control_plane.*
  - internal.policy.*

FORBIDDEN IMPORTS (in Incidents):
  - from app.services.policy.*
  - from app.models.policy_control_plane.*
  - internal.policy.*

ALLOWED IMPORTS:
  - Response models from facade (PolicyContext, etc.)
  - Type definitions for references
```

**Rationale:** Import boundaries prevent coupling. Helpers become dependencies.

---

### INV-BOUND-003: Reference-Only Cross-Domain Data

```
ALLOWED in cross-domain responses:
  - facade_ref (navigational link)
  - threshold_ref (navigational link)
  - violation_ref (navigational link)
  - policy_ref (navigational link)
  - lesson_ref (navigational link)
  - IDs for linking (policy_id, violation_id, etc.)

FORBIDDEN in cross-domain responses:
  - Embedded policy rules
  - Threshold computation logic
  - Enforcement decision trees
  - Policy metrics or summaries
```

**Rationale:** References enable navigation. Embedded logic creates coupling.

---

## III. Loop Integrity Invariants

### INV-LOOP-001: Violation Before Incident

```
INVARIANT:
  - A policy violation MUST exist BEFORE any incident referencing it
  - violation.created_at < incident.created_at

ENFORCEMENT:
  - SDSR scenario SDSR-POL-LOOP-001
  - Database constraint (FK on violation_id)
```

---

### INV-LOOP-002: Lesson References Source

```
INVARIANT:
  - A lesson MUST reference source_incident_id OR source_violation_id
  - Lessons without provenance are FORBIDDEN

ENFORCEMENT:
  - SDSR scenario SDSR-POL-LOOP-002
  - Database constraint (CHECK on source fields)
```

---

### INV-LOOP-003: Active Policy Has Origin

```
INVARIANT:
  - An active policy MUST have origin = 'DRAFT_PROMOTED' OR 'SYSTEM_DEFAULT'
  - IF origin = 'DRAFT_PROMOTED' THEN draft_id IS NOT NULL

ENFORCEMENT:
  - SDSR scenario SDSR-POL-LOOP-003
  - Database constraint (CHECK on origin)
```

---

### INV-LOOP-004: Activity Resilience

```
INVARIANT:
  - Activity MUST complete runs regardless of Policy facade status
  - Cached policy_context is acceptable fallback

ENFORCEMENT:
  - SDSR scenario SDSR-POL-LOOP-004
  - Chaos testing (Policy unavailability)
```

---

## IV. Capability Registry Invariants

### INV-CAP-001: Five Cross-Domain Capabilities Only

```
ALLOWED policy.* capabilities:
  - policy.active
  - policy.library
  - policy.lessons
  - policy.thresholds
  - policy.violations

FORBIDDEN:
  - Adding new policy.* capabilities without SDSR + architectural approval
  - Registering internal.policy.* as cross-domain
```

**Rationale:** Capability explosion defeats governance. Five is the stable surface.

---

### INV-CAP-002: SDSR Before OBSERVED

```
REQUIREMENT:
  - Capabilities remain DECLARED until SDSR validation passes
  - OBSERVED status requires all assertions passing
  - No manual status promotion

ENFORCEMENT:
  - AURORA_L2_apply_sdsr_observations.py
  - CI blocks OBSERVED without trace_id
```

---

## V. O-Level Boundary Invariants

### INV-O-001: Facade Is O1 Only

```
ALLOWED in facade responses:
  - O1: Summary/evidence data
  - O3: Detail endpoints (/{id})

FORBIDDEN in facade responses:
  - O2: Internal list interpretations
  - O4: Execution context
  - O5: Raw proof/audit data
```

**Rationale:** O2-O5 belong to Policy UI and governance workflows, not cross-domain consumers.

---

### INV-O-002: No Metrics Leakage

```
FORBIDDEN additions to facade:
  - Policy decision metrics
  - Threshold breach statistics
  - Enforcement rate calculations
  - Draft approval rates

WHERE THESE BELONG:
  - Policy domain internal endpoints
  - Governance dashboards
  - Audit reports
```

**Rationale:** Metrics invite reasoning. Cross-domain consumers should navigate, not analyze.

---

## VI. CI Enforcement Matrix

| Invariant | CI Check | Enforcement Level |
|-----------|----------|-------------------|
| INV-DOM-001 | Code review + SDSR | BLOCK |
| INV-DOM-002 | Code review + audit | BLOCK |
| INV-DOM-003 | SDSR-POL-LOOP-004 | BLOCK |
| INV-DOM-004 | Database constraints | BLOCK |
| INV-BOUND-001 | API route scanner | BLOCK |
| INV-BOUND-002 | Import analyzer | BLOCK |
| INV-BOUND-003 | Response schema validator | BLOCK |
| INV-LOOP-001 | SDSR + DB constraint | BLOCK |
| INV-LOOP-002 | SDSR + DB constraint | BLOCK |
| INV-LOOP-003 | SDSR + DB constraint | BLOCK |
| INV-LOOP-004 | SDSR + chaos test | BLOCK |
| INV-CAP-001 | Capability registry scanner | BLOCK |
| INV-CAP-002 | SDSR observation check | BLOCK |
| INV-O-001 | Response schema validator | BLOCK |
| INV-O-002 | Code review | WARN → BLOCK |

---

## VII. Amendment Process

### To Add New Invariant

1. Propose via RFC with rationale
2. Impact analysis on all three domains
3. Architect approval
4. Add to this document
5. Add CI enforcement
6. Announce to domain owners

### To Remove/Modify Invariant

1. Demonstrate invariant is no longer needed
2. Show no downstream dependencies
3. Architect approval + founder sign-off
4. Update CI guards
5. 30-day deprecation notice

---

## VIII. Quick Reference Card

```
ACTIVITY RULES:
  ✅ Read policy_context (cached OK)
  ✅ Navigate via facade_ref
  ✅ Complete runs without Policy
  ❌ Import internal.policy.*
  ❌ Evaluate policy synchronously
  ❌ Fail on Policy unavailability

POLICY RULES:
  ✅ Record violations (append-only)
  ✅ Create lesson DRAFTs
  ✅ Read Activity/Incidents facades
  ❌ Auto-activate rules
  ❌ Mutate from signals
  ❌ Skip human gate

INCIDENTS RULES:
  ✅ Store policy_id, violation_id refs
  ✅ Read /policy/violations/{id}
  ✅ Propose lessons on resolution
  ❌ Evaluate policy
  ❌ Create violations
  ❌ Import internal.policy.*
```

---

## IX. Governance Metadata Contract (PIN-447)

### INV-META-001: PolicyMetadata Schema

```
All V2 facade responses MUST include a `metadata` field with governance traceability:

PolicyMetadata:
  created_by: Optional[str]     # actor_id who created (null if system-generated)
  created_at: datetime          # when created (REQUIRED - always present)
  approved_by: Optional[str]    # actor_id who approved (null if not applicable)
  approved_at: Optional[datetime]  # when approved (null if pending)
  effective_from: Optional[datetime]  # start of validity (null if immediate)
  effective_until: Optional[datetime] # end of validity (null = no expiry)
  origin: str                   # SYSTEM_DEFAULT | MANUAL | LEARNED | INCIDENT | MIGRATION
  source_proposal_id: Optional[str]  # if promoted from proposal
  updated_at: Optional[datetime]     # last modification time
```

**Rationale:** Cross-domain consumers need governance traceability without querying internal systems.

---

### INV-META-NULL-001: Null Field Semantics (CRITICAL)

```
INVARIANT:
A null governance metadata field means "NOT YET MATERIALIZED",
NOT "NOT APPLICABLE" and NOT "DENIED".

CONSUMERS MUST NOT:
  - Branch on `field is None` to infer absence
  - Treat null as negative truth (e.g., null approved_by ≠ rejected)
  - Auto-populate nulls with system actors
  - Interpret null effective_from as "never effective"

CORRECT INTERPRETATION:
  - null created_by → system-generated (SYSTEM actor)
  - null approved_by → pending approval OR no approval gate
  - null effective_from → use created_at as default
  - null effective_until → no expiry (permanent)
```

**Rationale:** Null semantics must be stable to prevent logic bugs during schema evolution.

---

### INV-META-002: Metadata Field Semantics

| Field | Meaning | When Null |
|-------|---------|-----------|
| `created_by` | Actor who created the artifact | System-generated artifacts |
| `created_at` | Timestamp of creation | Never null |
| `approved_by` | Actor who approved activation | Pending approval or no approval gate |
| `approved_at` | Timestamp of approval | Pending or not applicable |
| `effective_from` | Start of validity window | Immediately effective |
| `effective_until` | End of validity window | No expiry (permanent) |
| `origin` | How the artifact was created | Never null |
| `source_proposal_id` | Link to source proposal | Not from proposal workflow |
| `updated_at` | Last modification | Immutable artifacts |

---

### INV-META-003: Origin Values

```
ALLOWED origin values:
  - SYSTEM_DEFAULT: Built-in system policies
  - MANUAL: Human-created via admin interface
  - LEARNED: Generated from lessons learned engine
  - INCIDENT: Created as result of incident resolution
  - MIGRATION: Migrated from legacy system

FORBIDDEN:
  - Custom origin values
  - Empty or null origin
```

**Rationale:** Origin determines trust level and audit requirements.

---

### INV-META-004: Schema Evolution

```
REQUIREMENT:
  - Fields may be added to PolicyMetadata (non-breaking)
  - Fields MUST NOT be removed from PolicyMetadata
  - Fields MUST NOT change meaning
  - Null semantics MUST be stable

PROCESS:
  1. Propose new field in RFC
  2. Add as Optional with null default
  3. Update cross-domain consumers
  4. Document in this contract
```

**Rationale:** Schema stability enables reliable cross-domain contracts.

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.1 | 2026-01-19 | Added Section IX: Governance Metadata Contract |
| 1.0 | 2026-01-19 | Initial constitutional layer |
