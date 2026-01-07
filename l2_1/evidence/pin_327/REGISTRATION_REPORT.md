# PIN-327: Capability Registration Finalization Report

**Status:** COMPLETE
**Date:** 2026-01-06
**Category:** Governance / Capability Registration
**Scope:** Full System Registration
**Prerequisites:** PIN-326 (Dormant Capability Elicitation)

---

## Executive Summary

This report documents the complete registration of all executable capabilities in the AgenticVerz 2.0 system into a single, closed Capability Registry with explicit status, scope, and constraints.

### Key Achievement

| Before PIN-327 | After PIN-327 |
|----------------|---------------|
| 18 CAP in registry | 128 capabilities registered |
| 103 LCAP unregistered | 0 unregistered capabilities |
| No unified schema | V2.0.0 schema enforced |
| Mixed status tracking | Explicit status for every capability |

---

## Registration Summary

### Total Capabilities Registered: 128

| Status | Count | Percentage |
|--------|-------|------------|
| FIRST_CLASS | 18 | 14% |
| DORMANT | 103 | 80% |
| SUBSTRATE | 7 | 6% |

### By Execution Vector

| Vector | Count | Description |
|--------|-------|-------------|
| HTTP | 77 | API routes |
| SDK | 31 | Python/JS SDK methods |
| CLI | 10 | CLI commands |
| Worker | 3 | Background workers |
| None | 7 | SUBSTRATE (no invocation) |

### By Console Scope

| Scope | Count | Description |
|-------|-------|-------------|
| CUSTOMER | 8 | Customer console visible |
| FOUNDER | 3 | Founder console only |
| SDK | 2 | SDK-only |
| NONE | 115 | Internal/SUBSTRATE |

### By Authority Model

| Model | Count | Description |
|-------|-------|-------------|
| DECLARED | 25 | FIRST_CLASS + SUBSTRATE |
| UNCLASSIFIED | 103 | DORMANT (awaiting classification) |

---

## Artifacts Produced

### Schema Extension
- **File:** `docs/capabilities/CAPABILITY_REGISTRY_SCHEMA_V2.yaml`
- **Purpose:** Define V2 schema with three statuses (FIRST_CLASS, DORMANT, SUBSTRATE)
- **Key additions:**
  - `status_enum` with validation rules
  - `execution_vector_enum`
  - `authority_model_enum`
  - `console_scope_enum`
  - Capability entry schema with required/optional fields
  - Validation rules for status consistency

### Unified Registry
- **File:** `docs/capabilities/CAPABILITY_REGISTRY_UNIFIED.yaml`
- **Purpose:** Single, closed registry of ALL executable capabilities
- **Sections:**
  1. FIRST_CLASS capabilities (CAP-001 to CAP-018)
  2. DORMANT capabilities (103 LCAP from PIN-326)
  3. SUBSTRATE capabilities (SUB-001 to SUB-007)
  4. Registry summary and statistics
  5. Negative assertion

---

## FIRST_CLASS Capabilities (18)

| ID | Name | Console Scope |
|----|------|---------------|
| CAP-001 | Execution Replay | CUSTOMER |
| CAP-002 | Cost Simulation V2 | CUSTOMER |
| CAP-003 | Policy Proposals | CUSTOMER |
| CAP-004 | C2 Prediction Plane | CUSTOMER |
| CAP-005 | Founder Console | FOUNDER |
| CAP-006 | Authentication | NONE |
| CAP-007 | Authorization (RBAC v2) | NONE |
| CAP-008 | M12 Multi-Agent Orchestration | SDK |
| CAP-009 | M19 Policy Engine | CUSTOMER |
| CAP-010 | M17 CARE-L Routing | NONE |
| CAP-011 | M28 Governance Orchestration | FOUNDER |
| CAP-012 | M4 Workflow Engine | NONE |
| CAP-013 | M5 Learning Pipeline | NONE |
| CAP-014 | M7 Memory System | CUSTOMER |
| CAP-015 | M22 Optimization Engine | NONE |
| CAP-016 | Skill System (M2/M3) | SDK |
| CAP-017 | Cross-Project Aggregation | FOUNDER |
| CAP-018 | M25 Integration Platform | CUSTOMER |

---

## DORMANT Capabilities (103)

### By Category

| Category | LCAP Range | Count |
|----------|------------|-------|
| Agent Autonomy | LCAP-001 to 010 | 10 |
| Cost Intelligence | LCAP-011 to 015 | 5 |
| Policy Governance | LCAP-016 to 019 | 4 |
| Incident Management | LCAP-020 to 023 | 4 |
| Trace & Replay | LCAP-024 to 027 | 4 |
| Recovery (M10) | LCAP-028 to 032 | 5 |
| Founder Actions | LCAP-033 to 035 | 3 |
| Ops Console | LCAP-036 to 040 | 5 |
| Runtime API | LCAP-041 to 045 | 5 |
| Run Management | LCAP-046 to 048 | 3 |
| Guard System | LCAP-049 to 051 | 3 |
| Predictions | LCAP-052 to 053 | 2 |
| Memory System | LCAP-054 to 055 | 2 |
| Integration Platform | LCAP-056 to 057 | 2 |
| Failures & Logs | LCAP-058 to 059 | 2 |
| Workers | LCAP-WKR-001 to 003 | 3 |
| CLI | LCAP-CLI-001 to 010 | 10 |
| Python SDK | LCAP-SDK-PY-001 to 015 | 15 |
| JavaScript SDK | LCAP-SDK-JS-001 to 016 | 16 |

### Promotion Blockers Summary

| Blocker Type | Count |
|--------------|-------|
| not_classified | 67 |
| authority_missing | 67 |
| partial_mapping | 33 |
| founder_only_subset | 11 |
| cli_ungoverned | 10 |
| sdk_ungoverned | 31 |
| worker_internal | 3 |
| implicit_authority | 18 |
| auto_execute_ungated | 1 |
| impersonation_risk | 1 |

---

## SUBSTRATE Capabilities (7)

| ID | Name | Layer | Justification |
|----|------|-------|---------------|
| SUB-001 | Database Connection Pool | L6 | Foundational infrastructure |
| SUB-002 | Cache Substrate | L6 | Advisory cache only |
| SUB-003 | Task Scheduling Substrate | L5 | Internal scheduling |
| SUB-004 | Observability Substrate | L6 | Internal observability |
| SUB-005 | Migration Substrate | L7 | Operational infrastructure |
| SUB-006 | Configuration Substrate | L6 | Bootstrap infrastructure |
| SUB-007 | Container Runtime Substrate | L7 | Deployment infrastructure |

---

## Negative Assertion

### Question
> "Is there any executable capability NOT registered in this registry?"

### Answer Progression

| PIN | Answer | Coverage |
|-----|--------|----------|
| PIN-325 | YES | 8% registered, 92% shadow |
| PIN-326 | NO (undiscovered) | 100% discovered as DORMANT |
| PIN-327 | NO (unregistered) | 100% registered |

### Final Answer: NO

All statically-discoverable executable capabilities are registered in the unified registry.

### Caveat

This registry covers statically-discoverable capabilities only. The following are NOT covered:
- Runtime-generated routes
- Event-driven handlers (Redis pub/sub)
- Webhook callbacks
- Plugin-loaded skills

These require separate discovery mechanisms.

---

## Human Decisions Pending

### Decision 1: DORMANT Promotion
103 DORMANT capabilities require promotion decisions:
- Promote to FIRST_CLASS (add to CAP-XXX)
- Declare as FORBIDDEN (kill)
- Accept as internal-only

### Decision 2: Authority Gaps
67 capabilities have authority_missing:
- Define RBAC permissions
- Declare scope rules
- Enable audit trails

### Decision 3: CLI/SDK Governance
41 CLI/SDK capabilities are ungoverned:
- Create CAP-019 (CLI) and CAP-020 (SDK)?
- Consider as L1/L7 proxies to L2?
- Document as known limitations?

### Decision 4: Auto-Execute Gates
LCAP-WKR-002 has AUTO_EXECUTE without capability gate:
- Add CAP-XXX for recovery:auto_execute?
- Require human approval for all recovery?
- Accept as designed?

---

## Invariants Established

1. **Status Invariant:** Every capability has exactly one status
2. **Registration Invariant:** Every executable path maps to a capability
3. **Permanence Invariant:** Registration is permanent (no silent removal)
4. **DORMANT Invariant:** DORMANT capabilities cannot be invoked from frontend
5. **SUBSTRATE Invariant:** SUBSTRATE capabilities are never user-invokable

---

## Phase Execution Summary

| Phase | Task | Status |
|-------|------|--------|
| 1 | Extend Capability Registry Schema | COMPLETE |
| 2 | Register FIRST_CLASS (CAP-001 to CAP-018) | COMPLETE |
| 3 | Register DORMANT (103 LCAP) | COMPLETE |
| 4 | Register SUBSTRATE (7 SUB) | COMPLETE |
| 5 | Negative assertion (final) | COMPLETE |
| 6 | Produce registration report | COMPLETE |

---

## References

- PIN-325: Shadow Capability Forensic Audit
- PIN-326: Dormant → Declared Capability Elicitation
- docs/capabilities/CAPABILITY_REGISTRY_SCHEMA_V2.yaml
- docs/capabilities/CAPABILITY_REGISTRY_UNIFIED.yaml
- l2_1/evidence/pin_326/LATENT_CAPABILITIES_DORMANT.yaml

---

## Attestation

This report represents registration only. No capabilities were promoted, no code was modified, no behavior was changed. All findings are declarations of existing power into a closed registry for governance purposes.

**Date:** 2026-01-06
**Reference:** PIN-327
**By:** Claude
