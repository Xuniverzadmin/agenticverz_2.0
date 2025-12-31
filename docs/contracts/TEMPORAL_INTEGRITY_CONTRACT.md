# Temporal Integrity Contract

**Status:** ACTIVE
**Effective:** 2025-12-30
**Reference:** PIN-245 (Integration Integrity System)

---

## Prime Invariant

> **Temporal violations are architectural incidents, not implementation bugs.**

Temporal behavior must be declared, not inferred. Sync-async boundary violations are blocking errors.

---

## Contract Obligations

### Obligation 1: Temporal Declaration Required

All artifacts must declare their temporal behavior explicitly:

| Property | Values | Description |
|----------|--------|-------------|
| **Trigger** | user, api, worker, scheduler, external | Who/what initiates this code? |
| **Execution** | sync, async, deferred | How does this code run? |
| **Lifecycle** | request, job, long-running, batch | How long does this code live? |

**Enforcement:** ARTIFACT_INTENT.yaml must have all three fields.

### Obligation 2: Synchronous Layer Restrictions (L1-L3)

Synchronous layers (L1, L2, L3) **MUST NOT**:

| Forbidden Action | Why Forbidden |
|------------------|---------------|
| Await worker execution | Creates hidden async dependency |
| Import worker or execution modules | Violates layer boundary |
| Block on long-running computation | Breaks request/response model |
| Create background tasks directly | Async must go through adapters |
| Access L5 directly | Must use L4 as intermediary |

**Enforcement:** RUNTIME-001 (Sync-Async Boundary Guard)

### Obligation 3: Asynchronous Layer Restrictions (L5)

Asynchronous execution (L5) **MUST**:

| Required Behavior | Rationale |
|-------------------|-----------|
| Be initiated via domain (L4) or adapter (L3) | Clean boundary separation |
| Never leak execution semantics upward | L1-L3 should not know about workers |
| Declare lifecycle explicitly | request vs job vs long-running |

**Enforcement:** RUNTIME-002 (Async Leak Detection Guard)

---

## Temporal Violation Types

| Type | Definition | Severity |
|------|------------|----------|
| **TV-001** | Sync layer importing from L5 | BLOCKING |
| **TV-002** | API handler awaiting worker | BLOCKING |
| **TV-003** | Deferred execution hidden behind sync API | BLOCKING |
| **TV-004** | Background task creation in L1-L2 | BLOCKING |
| **TV-005** | Undeclared temporal behavior | BLOCKING |

---

## Prohibition Clause

The following justifications are **INVALID** and must be rejected:

| Invalid Phrase | Why Invalid |
|----------------|-------------|
| "Temporary sync" | Temporal violations are architectural, not temporary |
| "Fast async" | Speed doesn't change execution model |
| "We'll refactor later" | Debt accumulation is not allowed |
| "Probably fast enough" | Inference is forbidden |
| "Likely async" | Inference is forbidden |
| "Just for now" | Temporary violations become permanent |
| "Quick hack" | Architectural shortcuts create debt |

---

## Resolution Patterns

When a temporal violation is detected, use one of these resolution patterns:

### Pattern 1: Add Adapter Layer

```
BEFORE (violation):
  L2 API → L5 Worker (direct import)

AFTER (compliant):
  L2 API → L3 Adapter → L4 Domain → L5 Worker
```

### Pattern 2: Change Execution Model

```
BEFORE (violation):
  L2 API awaits worker completion (sync facade over async)

AFTER (compliant):
  L2 API returns job_id, client polls for completion
```

### Pattern 3: Restructure Call Hierarchy

```
BEFORE (violation):
  L1 Page creates background task

AFTER (compliant):
  L1 Page calls L2 API → L4 Domain schedules task
```

---

## Validation Questions

Before merge, these questions must all be answered **NO**:

| Question | Required Answer |
|----------|-----------------|
| Can code exist without declared temporal behavior? | **NO** |
| Can sync layers directly access async execution layers? | **NO** |
| Can temporal violations be justified with "temporary"? | **NO** |
| Can async semantics leak into sync request handlers? | **NO** |

If any answer is YES, the temporal integrity gate is broken.

---

## Enforcement Mechanisms

| Mechanism | Location | Severity |
|-----------|----------|----------|
| PRE-BUILD-002 | SESSION_PLAYBOOK.yaml | BLOCKING |
| RUNTIME-001 | SESSION_PLAYBOOK.yaml | BLOCKING |
| RUNTIME-002 | SESSION_PLAYBOOK.yaml | BLOCKING |
| ARCH-GOV-003 | CLAUDE.md | BLOCKING |

---

## Failure Protocol

When temporal violations are detected:

1. **DO NOT** proceed with code generation
2. **DO NOT** accept "temporary" justifications
3. **DO NOT** infer temporal behavior
4. **DO** identify the violation type (TV-001 to TV-005)
5. **DO** propose a resolution pattern
6. **DO** require explicit temporal declaration

---

## Contract Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Contract established (PIN-245) |
