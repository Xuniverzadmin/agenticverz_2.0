---
paths:
  - "**"
alwaysApply: true
---

# Governance Core Rules

These rules apply to ALL files in the project. They are always loaded.

## Session Playbook Bootstrap (BL-BOOT-001, BL-BOOT-002)

**Rule:** Memory decays. Contracts don't. Sessions must boot like systems, not humans.

**Bootstrap Sequence (MANDATORY ORDER):**
1. **Load Documents** - Read all mandatory governance documents
2. **Run BLCA** - Execute `python3 scripts/ops/layer_validator.py --backend --ci`
3. **Verify CLEAN** - BLCA must report 0 violations
4. **Confirm Bootstrap** - Only then provide SESSION_BOOTSTRAP_CONFIRMATION

**BL-BOOT-002:** Bootstrap is INCOMPLETE without BLCA verification.

### Session Continuation (BL-BOOT-003)

When a session is continued from a summarized context, governance rules remain FULLY ACTIVE.
Claude must include SESSION_CONTINUATION_ACKNOWLEDGMENT in the first response.

## Pre-Code Discipline (MANDATORY)

Claude must not write or modify any code until completing:

| Task | Phase | Purpose |
|------|-------|---------|
| 0 | Accept | Acknowledge contract explicitly |
| 1 | CLASSIFY | Change classification (transactional?) |
| 2 | PLAN | System state inventory (alembic, schema) |
| 3 | VERIFY | Conflict & risk scan |
| 4 | PLAN | Migration intent (if applicable) |
| 5 | PLAN | Execution plan (what changes, what doesn't) |
| 6 | ACT | Write code (only after 0-5 complete) |
| 7 | VERIFY | Self-audit (MANDATORY for all code) |
| 8 | ATTEST | Final attestation (for features) |

## SELF-AUDIT Section (REQUIRED for all code changes)

```
SELF-AUDIT
- Did I verify current DB and migration state? YES / NO
- Did I read memory pins and lessons learned? YES / NO
- Did I introduce new persistence? YES / NO
- Did I risk historical mutation? YES / NO
- Did I assume any architecture not explicitly declared? YES / NO
- Did I reuse backend internals outside runtime? YES / NO
- Did I introduce an implicit default (DB, env, routing)? YES / NO
- If YES to any risk → mitigation: <explain>
- If YES to last three → response is INVALID, must redesign
```

Outputs missing SELF-AUDIT are invalid.

## Engineering Authority Self-Check (PIN-270)

Before generating any code or recommendation, Claude must internally verify:
1. Am I fixing the architecture or just making tests pass?
2. Does this contradict Layer Model (L1-L8)?
3. Am I assuming infra exists without checking INFRA_REGISTRY?
4. Am I weakening an assertion to avoid a failure?
5. Is this a shortcut that future-me will regret?
6. Would a new engineer understand this without asking?
7. Am I guessing instead of asking one precise question?

## Forbidden Actions (ABSOLUTE)

| Action | Reason |
|--------|--------|
| Mutate historical executions | Violates S1, S6 |
| Assume schema state | Causes migration forks |
| Create migrations without checking heads | Multi-head chaos |
| Infer missing data | Violates truth-grade |
| Skip SELF-AUDIT | Invalidates response |

## Forbidden Assumptions (FA-001 to FA-007)

| ID | Assumption | Correct Model |
|----|------------|---------------|
| FA-001 | Consoles separated by API prefix | Subdomain + Auth Audience |
| FA-002 | Localhost database fallback | DATABASE_URL must be explicit |
| FA-003 | Importing app.db in scripts | Scripts use psycopg2 + explicit DATABASE_URL |
| FA-004 | Inferring config from environment markers | All config explicit via env vars |
| FA-005 | Different consoles see different data | Same data, different visibility rules |
| FA-006 | UI exposure without discovery | Discovery must precede visibility |
| FA-007 | Custom pages for domain data | Use projection-driven DomainPage + PanelContentRegistry |

## Canonical-First Fix Policy (ARCH-CANON-001)

Claude is FORBIDDEN from creating new database tables, schemas, or public APIs when addressing gaps in an existing domain. Fix the canonical structure instead.

## Governance Checklist (GC-001 to GC-007)

Every session that modifies behavior MUST complete the Governance Checklist (docs/governance/GOVERNANCE_CHECKLIST.md). All 7 sections required. Missing checklist = SESSION BLOCKED.

## Phase E Governance Invariants

- Extraction-First Rule (fix via extraction, not reclassification)
- Anti-Reclassification Constraint
- Dual-Role Prohibition (no module may simultaneously decide AND execute)
- BLCA Supremacy Rule (BLCA findings halt progress)
- Sequential Extraction Invariant (one domain at a time)
- No "Acceptable" States (no "watchlist", "note only", etc.)

## Architecture Governor Role (PIN-245)

Four Mandatory Gates: ARCH-GOV-001 (Artifact Intent), ARCH-GOV-002 (Layer Declaration), ARCH-GOV-003 (Temporal Clarity), ARCH-GOV-006 (Artifact Class).

## Intent & Temporal Enforcement

Missing intent or temporal ambiguity = hard failure. Claude must refuse to generate code without declared ARTIFACT_INTENT, explicit layer, and explicit temporal model.

## System Contracts

All future work follows the contract framework:
1. PRE-RUN: What must the system declare before execution starts?
2. CONSTRAINT: What constraints apply?
3. DECISION: What decisions must be surfaced?
4. OUTCOME: How do we reconcile what happened vs promised?

No code, no UI, no refactor without naming the contract obligation it satisfies.

## Testing Principles (P1-P6)

| Principle | Rule |
|-----------|------|
| P1 | Real scenarios against real infrastructure first |
| P2 | Real LLMs, real databases, no simulations |
| P3 | Full data propagation verification |
| P4 | O-level (O1-O4) propagation verification |
| P5 | Human semantic verification required |
| P6 | Localhost fallback only when Neon blocked |

## Execution Discipline (v1.4)

- No `eval` usage
- No nested command substitution
- Commands must be copy-paste safe
- Auth contract: `.env file → Shell environment → HTTP header → RBAC middleware`
- Frozen header format: `X-AOS-Key: <API_KEY>`

## Python Execution Invariant

- Working directory: Run from `backend/`, never from repo root
- Package root: `app/` is the root package
- Imports: Use absolute imports (`from app.db import ...`)
- `DATABASE_URL` required for execution, NOT for imports

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│              AGENTICVERZ CLAUDE DISCIPLINE                  │
├─────────────────────────────────────────────────────────────┤
│  1. LOAD: Memory pins, Lessons, Contracts                   │
│  2. PHASE: Identify current phase (A/A.5/B/C)               │
│  3. P-V-A: Plan → Verify → Act (in order, no skip)          │
│  4. FORBIDDEN: No mutation, no inference, no shortcuts      │
│  5. SELF-AUDIT: Required for all code changes               │
│  6. BLOCKED: Stop if conflict detected                      │
│  7. ARCH-GOV: Layer, Temporal, Ownership gates (PIN-245)    │
│  8. ARTIFACT: Every file has class + layer (PIN-248)        │
│  9. AUDIENCE: Check AUDIENCE headers on ALL files            │
└─────────────────────────────────────────────────────────────┘
```
