# Non-Mutating Tooling Invariant

**Status:** CONSTITUTIONAL
**Effective:** 2026-01-04
**Reference:** PIN-290

---

## Core Invariant

> **No automated system may mutate source files during commit, CI, or certification.**

This is not a convention. It is a **constitutional rule**.

---

## Why This Exists

### The Problem

Auto-fix tooling destroys governance properties:

| Property | How Auto-Fix Violates It |
|----------|--------------------------|
| Frozen design boundaries | Style changes can violate layer boundaries |
| Determinism | Same commit produces different code |
| Auditability | Mutations occur without human intent |
| Authority separation | Judges (CI) become editors |
| Phase discipline | Mutation happens outside intent |

### The Symptom

```
[WARNING] Unstaged files detected.
[INFO] Stashing unstaged files to /root/.cache/pre-commit/patch...
...
Stashed changes conflicted with hook auto-fixes... Rolling back fixes...
```

This is not a Git issue. It is a **governance breach in tooling design**.

---

## The Correct Architecture

### Authority Separation (Non-Negotiable)

```
HUMAN INTENT
   ↓
CODE MUTATION (explicit, human-initiated)
   ↓
STATIC JUDGMENT (check-only)
   ↓
SEMANTIC JUDGMENT (check-only)
   ↓
CERTIFICATION (check-only)
```

**Never the reverse. Never combined.**

---

## Implementation

### A. Commit Phase (Local Pre-Commit Hooks)

**Purpose:** Verify human intent

**Allowed:**
- Static checks
- Structural guards
- Semantic guards
- Design freeze enforcement
- Authority boundary enforcement

**Forbidden:**
- Auto-fix
- Formatting
- Rewriting imports
- Reordering code
- Generating files

**Commit must be:** *Fail-only, never fix.*

---

### B. CI Phase (Remote)

**Purpose:** Certify truth, not improve code

**CI must be:**
- Read-only
- Deterministic
- Replayable
- Non-interactive

**CI may:**
- Re-run all guards
- Re-run all semantic tests
- Re-run certification engines
- Produce reports

**CI must never:**
- Rewrite files
- "Help" the developer
- Apply formatting
- Auto-resolve lint

---

### C. Fix Phase (Explicit, Human-Initiated)

All auto-fix capability is moved into explicit human commands:

```bash
# Option 1: Make target
make lint-fix

# Option 2: Direct script
./scripts/dev/fix_style.sh
```

These commands:
- Are never run implicitly
- Are never run by CI
- Are never run by hooks
- Leave an intentional diff
- Are reviewed like any other change

---

## Correct Workflow

```bash
# 1. Write code
vim backend/app/foo.py

# 2. Explicit mutation (human-initiated)
make lint-fix

# 3. Review changes
git diff

# 4. Stage changes
git add backend/app/foo.py

# 5. Commit (check-only hooks verify)
git commit -m "Add foo feature"
```

---

## What Changed

### Pre-Commit Hooks

| Before | After |
|--------|-------|
| `trailing-whitespace` (auto-fix) | `check-trailing-whitespace` (check-only) |
| `end-of-file-fixer` (auto-fix) | `check-eof-newline` (check-only) |
| `ruff` (auto-fix) | `ruff --no-fix` (check-only) |
| `ruff-format` (auto-fix) | `ruff-format --check` (check-only) |

### Make Targets

| Target | Purpose |
|--------|---------|
| `make lint-fix` | Explicit mutation (human-initiated) |
| `make lint-check` | Check without fixing |

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/dev/fix_style.sh` | Explicit style mutation |

---

## Enforcement

### Pre-Commit Config

```yaml
# .pre-commit-config.yaml

# Ruff: CHECK-ONLY
- id: ruff
  args: [--no-fix]
- id: ruff-format
  args: [--check]

# Whitespace: CHECK-ONLY (custom hooks)
- id: check-trailing-whitespace
- id: check-eof-newline

# REMOVED: auto-fix hooks
# - trailing-whitespace
# - end-of-file-fixer
```

### Violations

If any tool violates this invariant:

1. **Identify** the mutating tool
2. **Remove** the auto-fix behavior
3. **Add** a check-only alternative
4. **Document** the change

---

## Relation to Governance

This invariant aligns with existing governance principles:

| Governance Rule | Tooling Implication |
|-----------------|---------------------|
| Authority separation | Judges never mutate |
| Auditability | No silent changes |
| Determinism | Same input → same output |
| Design freeze | Auto-fix forbidden |
| Phase discipline | Intent before action |

---

## References

- PIN-290: Non-Mutating Tooling Invariant
- PIN-284: Platform Monitoring System
- GOVERNANCE_CHECKLIST.md
- SESSION_PLAYBOOK.yaml

---

## Attestation

This document defines the Non-Mutating Tooling Invariant.

All tooling must conform to this invariant.

Violations require explicit ratification.
