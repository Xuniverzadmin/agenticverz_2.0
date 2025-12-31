# Architecture Operating Manual

**Status:** AUTHORITATIVE
**Version:** 1.0
**Effective:** 2025-12-30
**Reference:** PIN-245 (Integration Integrity System)

---

## Executive Summary

This manual defines the **self-defending architecture** for AgenticVerz 2.0.

**Core Principle:**
> Invalid states are unrepresentable. Architecture defends itself.

**Key Guarantees:**
- No code can exist without declared intent
- No temporal behavior can be inferred
- No layer boundary can be violated silently
- Integration errors are caught before merge

---

## Part 1: The Layer Model

### 1.1 Layer Definitions

| Layer | Name | Responsibility | Import Rights |
|-------|------|----------------|---------------|
| **L1** | Product Experience | UI, pages, user interactions | L2 only |
| **L2** | Product APIs | REST endpoints, API routes | L3, L4, L6 |
| **L3** | Boundary Adapters | Thin translation (< 200 LOC) | L4, L6 |
| **L4** | Domain Engines | Business rules, system truth | L5, L6 |
| **L5** | Execution & Workers | Background jobs, async work | L6 only |
| **L6** | Platform Substrate | DB, Redis, external services | None |
| **L7** | Ops & Deployment | Systemd, Docker, monitoring | L6 |
| **L8** | Catalyst / Meta | CI, tests, validators | Any |

### 1.2 Layer Import Rules

```
L1 ──► L2
       │
L2 ──► L3 ──► L4 ──► L5 ──► L6
       │      │             ▲
       └──────┴─────────────┘

L7 ──► L6
L8 ──► * (tests can import anything)
```

**Forbidden Patterns:**
- L1 importing from L3, L4, L5, L6
- L2 importing from L5 (workers)
- L3 importing from L5
- Any layer importing from L7 (ops)

### 1.3 Layer Detection

Layers are detected by:

1. **File header declaration** (authoritative)
2. **Path pattern** (fallback)

Path patterns:
```
website/aos-console/console/src/products → L1
website/aos-console/console/src/pages   → L1
backend/app/api                         → L2
backend/app/adapters                    → L3
backend/app/domain                      → L4
backend/app/worker                      → L5
backend/app/db                          → L6
scripts/ops                             → L7
backend/tests                           → L8
```

---

## Part 2: Temporal Integrity

### 2.1 Temporal Declaration

Every artifact must declare:

| Property | Values | Required |
|----------|--------|----------|
| **Trigger** | user, api, worker, scheduler, external | YES |
| **Execution** | sync, async, deferred | YES |
| **Lifecycle** | request, job, long-running, batch | YES |

### 2.2 Temporal Contract

**Synchronous Layers (L1-L3) MUST NOT:**
- Await worker execution
- Import worker or execution modules
- Block on long-running computation
- Create background tasks directly

**Asynchronous Layer (L5) MUST:**
- Be initiated via L4 (domain) or L3 (adapter)
- Never leak execution semantics upward
- Declare lifecycle explicitly

### 2.3 Temporal Violation Types

| Code | Name | Severity | Detection |
|------|------|----------|-----------|
| TV-001 | Sync importing async | BLOCKING | Import analysis |
| TV-002 | API awaiting worker | BLOCKING | AST analysis |
| TV-003 | Hidden deferred | BLOCKING | Pattern match |
| TV-004 | Background in L1-L2 | BLOCKING | Pattern match |
| TV-005 | Undeclared temporal | BLOCKING | Header check |
| TV-006 | Async leak upward | BLOCKING | Call graph |

### 2.4 Invalid Temporal Justifications

These phrases **MUST BE REJECTED**:

| Phrase | Why Invalid |
|--------|-------------|
| "Temporary sync" | Temporal violations are architectural |
| "Fast async" | Speed doesn't change execution model |
| "We'll refactor later" | Debt accumulation forbidden |
| "Probably fast enough" | Inference forbidden |
| "Likely async" | Inference forbidden |
| "Just for now" | Temporary becomes permanent |
| "Quick hack" | Shortcuts create debt |

---

## Part 3: Intent Declaration

### 3.1 Intent Requirement

> **No artifact may exist without explicit, versioned intent declaration.**

An artifact without intent is:
- Architecturally invalid
- Non-reviewable
- Non-mergeable

### 3.2 Required Intent Fields

```yaml
artifact_id: AOS-{domain}-{type}-{name}-{seq}

layer:
  declared: L{1-8}
  confidence: high | medium  # LOW = blocked
  justification: "..."

temporal:
  trigger: user | api | worker | scheduler | external
  execution: sync | async | deferred
  lifecycle: request | job | long-running | batch

product:
  owner: ai-console | system-wide | product-builder
  slice: surface | adapter | platform | catalyst

responsibility:
  role: "single-line description"
  must_not_do:
    - "..."

dependencies:
  allowed_layers: [L{x}, L{y}]
  forbidden_layers: [L{z}]

state:
  mutates_persistent_state: true | false
  mutates_global_state: true | false

failure_scope:
  breaks_if_removed: [...]
  must_not_break: [...]

integration:
  lit_required: true | false
  bit_required: true | false
  seam_tested: "L2↔L3"
```

### 3.3 File Header Format

**Python:**
```python
# Layer: L{x} — {Layer Name}
# Product: {product | system-wide}
# Temporal:
#   Trigger: {user|api|worker|scheduler|external}
#   Execution: {sync|async|deferred}
# Role: {single-line responsibility}
# Callers: {who calls this?}
# Allowed Imports: L{x}, L{y}
# Forbidden Imports: L{z}
# Reference: PIN-{xxx}
```

**TypeScript:**
```typescript
/**
 * Layer: L{x} — {Layer Name}
 * Product: {product | system-wide}
 * Temporal:
 *   Trigger: {user|api|worker|scheduler}
 *   Execution: {sync|async}
 * Role: {single-line responsibility}
 * Callers: {who renders/uses this?}
 * Allowed Imports: L{x}, L{y}
 * Forbidden Imports: L{z}
 * Reference: PIN-{xxx}
 */
```

---

## Part 4: Pre-Build Guards

### 4.1 Guard Summary

| Guard ID | Name | Trigger | Action |
|----------|------|---------|--------|
| PRE-BUILD-001 | Intent Declaration | New file | BLOCK_AND_QUERY |
| PRE-BUILD-002 | Temporal Declaration | Any code | BLOCK_AND_QUERY |
| PRE-BUILD-003 | Layer Confidence | New file | BLOCK_AND_QUERY |
| RUNTIME-001 | Sync-Async Boundary | Import | BLOCK |
| RUNTIME-002 | Async Leak Detection | Pattern | BLOCK |
| RUNTIME-003 | Intent Completeness | All fields | BLOCK |

### 4.2 PRE-BUILD-001: Intent Declaration Gate

**Rule:** Any new file must have a corresponding ARTIFACT_INTENT.yaml entry or file header.

**Missing intent response:**
```
PRE-BUILD-001: Intent Declaration Required

Cannot create code without artifact intent.

Required fields:
- artifact_id
- layer (L1-L8)
- temporal (trigger, execution, lifecycle)
- product owner
- dependencies

Template: docs/templates/ARTIFACT_INTENT.yaml
```

### 4.3 PRE-BUILD-002: Temporal Declaration Gate

**Rule:** Every artifact must declare trigger, execution mode, and lifecycle. Temporal ambiguity is not allowed.

**Missing temporal response:**
```
PRE-BUILD-002: Temporal Declaration Required

Cannot proceed with ambiguous temporal behavior.
Inference is forbidden.

Declare explicitly:
- Trigger: who/what initiates this?
- Execution: sync | async | deferred
- Lifecycle: request | job | long-running | batch
```

### 4.4 PRE-BUILD-003: Layer Confidence Gate

**Rule:** Layer must be declared with HIGH or MEDIUM confidence. LOW confidence = BLOCKED.

**Low confidence response:**
```
PRE-BUILD-003: Layer Confidence Insufficient

Layer declaration requires HIGH or MEDIUM confidence.
LOW confidence means the artifact is not understood.

Clarify layer assignment before proceeding.
```

### 4.5 RUNTIME-001: Sync-Async Boundary Guard

**Rule:** Synchronous layers (L1-L3) must not directly invoke async execution layers (L5).

**Detection patterns:**
- L1/L2/L3 importing from `app.worker.*`
- Sync function with `await` on worker
- API handler blocking on long-running computation

**Violation response:**
```
RUNTIME-001: Sync-Async Boundary Violation

Synchronous layer (L1-L3) is accessing async execution layer (L5).
This is an architectural incident, not an implementation bug.

Resolution options:
1. Add an adapter layer (L3)
2. Change the execution model
3. Restructure the call hierarchy
```

### 4.6 RUNTIME-002: Async Leak Detection Guard

**Rule:** Async execution semantics must not leak upward. L5 execution must be initiated via L4 or L3.

**Detection patterns:**
- `BackgroundTasks` in L1/L2
- `asyncio.create_task()` in API handlers
- Worker dispatch patterns in sync code

**Violation response:**
```
RUNTIME-002: Async Leak Detected

Async execution semantics are leaking into sync layers.
Execution must be initiated via domain or adapter boundaries.

This is a temporal contract violation.
```

---

## Part 5: Integration Testing

### 5.1 Test Categories

| Category | Name | Scope | Location |
|----------|------|-------|----------|
| **LIT** | Layer Integration Tests | Layer seam contracts | `backend/tests/lit/` |
| **BIT** | Browser Integration Tests | Console errors | `website/.../tests/bit/` |

### 5.2 LIT Requirements

**What LIT tests:**
- Response shape matches documented schema
- Null safety (no unexpected None)
- Error format consistency
- Content-Type correctness
- Status code validity

**When LIT required:**
- Any new L2 API endpoint
- Any L3 adapter
- Any L2↔L6 direct access

### 5.3 BIT Requirements

**What BIT tests:**
- No `console.error` on page load
- No unhandled promise rejections
- No 5xx responses
- No broken routes

**When BIT required:**
- Any new L1 page
- Any navigation change
- Any API integration change

### 5.4 Integration Seams

| Seam | Test Type | Required |
|------|-----------|----------|
| L1↔L2 | BIT | YES |
| L2↔L3 | LIT | YES |
| L3↔L4 | LIT | Optional |
| L4↔L5 | LIT | Optional |
| L2↔L6 | LIT | YES |

---

## Part 6: Claude Governance

### 6.1 Claude Role

Claude operates as **Architecture Governor**, not code generator.

**Mandatory behavior:**
- Verify intent before code
- Verify temporal before execution
- Block on ambiguity
- Never infer architectural properties

### 6.2 Claude Self-Check

Before ANY code generation:

```
INTENT & TEMPORAL SELF-CHECK
- Is this artifact allowed to exist without an intent file? → NO
- Is sync vs async explicitly declared? → REQUIRED
- Does this create a new execution boundary? → IF YES, BLOCK UNTIL DECLARED
- Am I inferring temporal behavior? → IF YES, STOP AND ASK
```

### 6.3 Hard Failure Responses

**Missing Intent:**
```
INTENT DECLARATION REQUIRED

Cannot proceed without artifact intent declaration.

Required fields:
- Layer (L1-L8)
- Temporal (trigger, execution, lifecycle)
- Product owner
- Dependencies (allowed/forbidden layers)

Template: docs/templates/ARTIFACT_INTENT.yaml
```

**Temporal Ambiguity:**
```
TEMPORAL DECLARATION REQUIRED

Cannot proceed with ambiguous temporal behavior.

Required declaration:
- Trigger: user | api | worker | scheduler | external
- Execution: sync | async | deferred
- Lifecycle: request | job | long-running | batch

Inference is not allowed. Please declare explicitly.
```

**Temporal Violation:**
```
TEMPORAL CONTRACT VIOLATION

Detected: [describe violation]

This is an architectural incident, not an implementation bug.
Cannot proceed until the violation is resolved.

Options:
1. Add an adapter layer
2. Change the execution model
3. Restructure the call hierarchy
```

---

## Part 7: Enforcement Tools

### 7.1 Tool Summary

| Tool | Purpose | Location |
|------|---------|----------|
| `intent_validator.py` | Validate intent declarations | `scripts/ops/` |
| `temporal_detector.py` | Detect temporal violations | `scripts/ops/` |
| `integration-integrity.yml` | CI pipeline | `.github/workflows/` |

### 7.2 Intent Validator

```bash
# Check single file
python scripts/ops/intent_validator.py --check backend/app/api/runs.py

# Scan directory
python scripts/ops/intent_validator.py --scan backend/app

# Check changed files only
python scripts/ops/intent_validator.py --diff

# Full compliance report
python scripts/ops/intent_validator.py --report

# JSON output for CI
python scripts/ops/intent_validator.py --report --json
```

### 7.3 Temporal Detector

```bash
# Check single file
python scripts/ops/temporal_detector.py --check backend/app/api/runs.py

# Scan directory
python scripts/ops/temporal_detector.py --scan backend/app

# Check changed files only
python scripts/ops/temporal_detector.py --diff

# Full report
python scripts/ops/temporal_detector.py --report

# JSON output for CI
python scripts/ops/temporal_detector.py --report --json
```

### 7.4 CI Pipeline

```yaml
# .github/workflows/integration-integrity.yml

jobs:
  intent-validation:
    - python scripts/ops/intent_validator.py --diff

  temporal-validation:
    - python scripts/ops/temporal_detector.py --diff

  lit-tests:
    - pytest tests/lit -v -m lit

  bit-tests:
    - npx playwright test tests/bit
```

---

## Part 8: Resolution Patterns

### 8.1 Temporal Violation Resolution

**Pattern 1: Add Adapter Layer**
```
BEFORE (violation):
  L2 API → L5 Worker (direct import)

AFTER (compliant):
  L2 API → L3 Adapter → L4 Domain → L5 Worker
```

**Pattern 2: Change Execution Model**
```
BEFORE (violation):
  L2 API awaits worker completion (sync facade over async)

AFTER (compliant):
  L2 API returns job_id, client polls for completion
```

**Pattern 3: Restructure Call Hierarchy**
```
BEFORE (violation):
  L1 Page creates background task

AFTER (compliant):
  L1 Page calls L2 API → L4 Domain schedules task
```

### 8.2 Layer Violation Resolution

**Wrong layer import:**
```
BEFORE (violation):
  L2 imports from L5 (worker)

AFTER (compliant):
  L2 imports from L3 (adapter)
  L3 imports from L4 (domain)
  L4 imports from L5 (worker)
```

---

## Part 9: Validation Questions

### 9.1 Intent Validation

| Question | Required Answer |
|----------|-----------------|
| Can code exist without declared intent? | **NO** |
| Can intent fields be incomplete? | **NO** |
| Can layer confidence be LOW? | **NO** |

### 9.2 Temporal Validation

| Question | Required Answer |
|----------|-----------------|
| Can temporal behavior be inferred? | **NO** |
| Can sync layers access L5 directly? | **NO** |
| Can async leak into sync handlers? | **NO** |
| Can "temporary sync" justify violation? | **NO** |

### 9.3 Integration Validation

| Question | Required Answer |
|----------|-----------------|
| Can API exist without LIT? | **NO** |
| Can page exist without BIT coverage? | **NO** |
| Can console errors reach users? | **NO** |

---

## Part 10: Quick Reference

### 10.1 File Creation Checklist

```
□ Fill out ARTIFACT_INTENT.yaml
□ Add file header with layer declaration
□ Declare temporal behavior (trigger, execution, lifecycle)
□ Verify allowed/forbidden imports
□ Add LIT test if API
□ Add to BIT registry if page
```

### 10.2 Code Modification Checklist

```
□ Verify existing intent declaration
□ Check layer boundary compliance
□ Verify temporal model unchanged (or update declaration)
□ Run intent_validator.py --check
□ Run temporal_detector.py --check
□ Update tests if seam affected
```

### 10.3 Emergency Reference

**I need to create a new file:**
1. Fill out `docs/templates/ARTIFACT_INTENT.yaml`
2. Add file header per `docs/templates/FILE_HEADER_TEMPLATE.md`
3. Run `python scripts/ops/intent_validator.py --check <file>`

**I'm seeing a temporal violation:**
1. Identify violation type (TV-001 to TV-006)
2. Apply resolution pattern (Part 8)
3. Run `python scripts/ops/temporal_detector.py --check <file>`

**I'm blocked by Claude:**
1. Read the blocking message
2. Provide the missing declaration
3. Do NOT ask Claude to proceed without it

---

## Document Index

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | Claude behavioral rules |
| `SESSION_PLAYBOOK.yaml` | Session governance |
| `INTEGRATION_INTEGRITY_CONTRACT.md` | Integration contract |
| `TEMPORAL_INTEGRITY_CONTRACT.md` | Temporal contract |
| `ARTIFACT_INTENT.yaml` | Intent template |
| `FILE_HEADER_TEMPLATE.md` | Header template |
| `intent_validator.py` | Intent validation tool |
| `temporal_detector.py` | Temporal detection tool |
| `integration-integrity.yml` | CI workflow |

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-12-30 | 1.0 | Initial release |
