# Integration Integrity Contract

**Status:** ACTIVE
**Effective:** 2025-12-30
**Reference:** PIN-245 (Integration Integrity System)

---

## Prime Invariant

> **A build is invalid if:**
>
> 1. Any browser console error appears on first page load
> 2. Any layer seam returns malformed or undocumented data
> 3. Async execution leaks into sync layers

**Business correctness is allowed to fail.**
**Integration correctness is not.**

---

## Contract Obligations

### Obligation 1: Layer Seam Contracts (LIT)

Every L2 ↔ L3, L3 ↔ L4, L4 ↔ L5, and L2 ↔ L6 boundary must:

| Property | Requirement |
|----------|-------------|
| Response shape | Matches documented schema |
| Null safety | No unexpected None in required fields |
| Error format | Consistent error response shape |
| Content-Type | application/json for API responses |
| Status codes | Only documented status codes returned |

**Enforcement:** LIT tests in `backend/tests/lit/`

### Obligation 2: Browser Console Purity (BIT)

Every L1 page must load without:

| Error Type | Treatment |
|------------|-----------|
| `console.error` | BUILD FAILS |
| Unhandled promise rejection | BUILD FAILS |
| Network 5xx | BUILD FAILS |
| Network 4xx (except 401/403) | WARNING |

**Enforcement:** BIT tests in `website/aos-console/console/tests/bit/`

### Obligation 3: Pre-Build Gate

Any new L1 or L2 artifact MUST include:

| Artifact Type | Required Tests |
|---------------|----------------|
| API endpoint (L2) | At least one LIT test |
| UI page (L1) | Entry in page-registry.yaml |
| Adapter (L3) | LIT test for upstream seam |

**Enforcement:** Code review + CI gate

---

## Allowlist Protocol

Exceptions are ONLY permitted via explicit allowlist:

```yaml
# allowlist.yaml entry format
allowed_console_errors:
  - page: /path
    pattern: "Error message substring"
    reason: brief_reason_code
    expiry: YYYY-MM-DD
    owner: team-name
```

### Allowlist Rules

| Rule | Description |
|------|-------------|
| Expiry Required | Every entry MUST have expiry date |
| No Expiry = Invalid | CI rejects entries without expiry |
| Expired = Ignored | Expired entries don't suppress errors |
| Audit Trail | Removed entries kept as comments |

---

## Validation Questions

Before merge, these questions must all be answered **NO**:

| Question | Required Answer |
|----------|-----------------|
| Can a frontend page load with broken wiring and still pass CI? | **NO** |
| Can a developer introduce a new API without integration tests? | **NO** |
| Will browser console errors reach users without being caught? | **NO** |

If any answer is YES, the integration gate is broken.

---

## Prohibited Behaviors

The following are explicitly forbidden:

| Behavior | Why Forbidden |
|----------|---------------|
| Converting LIT/BIT to E2E | Conflates integration with business testing |
| Adding retry logic to hide errors | Masks integration failures |
| Silencing console errors | Prevents detection |
| Marking failures as flaky | Erodes signal quality |
| Testing business logic in LIT | Wrong scope |

---

## CI Pipeline Order

```
1. Static architecture validators
2. Unit tests
3. Layer Integration Tests (LIT) ← Integration gate
4. Browser Integration Tests (BIT) ← Integration gate
5. Smoke tests
6. E2E tests
```

LIT and BIT run BEFORE smoke and E2E. Integration errors are caught early.

---

## Failure Protocol

When integration tests fail:

1. **DO NOT** merge
2. **DO NOT** add to allowlist without expiry
3. **DO NOT** retry hoping it passes
4. **DO** investigate root cause
5. **DO** fix the integration error
6. **DO** add to allowlist ONLY if legitimate temporary exception

---

---

## Intent Declaration Contract

> **No artifact may exist without an explicit, versioned intent declaration.**

### What This Means

An artifact without intent is considered:

| Status | Consequence |
|--------|-------------|
| **Architecturally invalid** | Cannot be reasoned about |
| **Non-reviewable** | Code review cannot approve |
| **Non-mergeable** | CI must reject |

### Scope

This applies to:

| Artifact Type | Intent Required |
|---------------|-----------------|
| New files | YES |
| Significant modifications | YES |
| Boundary-changing refactors | YES |
| Import changes | YES |
| Layer transitions | YES |

### Required Intent Fields

Every artifact must declare:

```yaml
artifact_id: AOS-XXX-YYY-ZZZ
layer:
  declared: L{1-8}
  confidence: high | medium  # LOW = BLOCKED
  justification: "..."
temporal:
  trigger: user | api | worker | scheduler | external
  execution: sync | async | deferred
  lifecycle: request | job | long-running | batch
product:
  owner: ai-console | system-wide | product-builder
responsibility:
  role: "single-line description"
dependencies:
  allowed_layers: [L{x}, L{y}]
  forbidden_layers: [L{z}]
```

### Enforcement

| Mechanism | Gate ID | Action |
|-----------|---------|--------|
| PRE-BUILD-001 | Intent Declaration Gate | BLOCK_AND_QUERY |
| RUNTIME-003 | Intent Completeness Guard | BLOCK |
| ARCH-GOV-001 | Artifact Intent Gate | BLOCK |

### Intent Template

Use: `docs/templates/ARTIFACT_INTENT.yaml`

---

## Contract Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Added Intent Declaration Contract |
| 2025-12-30 | Contract established (PIN-245) |
