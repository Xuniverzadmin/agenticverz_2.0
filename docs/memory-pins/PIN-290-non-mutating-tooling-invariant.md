# PIN-290: Non-Mutating Tooling Invariant

**Status:** CONSTITUTIONAL
**Created:** 2026-01-04
**Category:** Governance / Tooling
**Related:** PIN-284, PIN-289

---

## Summary

Establishes the Non-Mutating Tooling Invariant: No automated system may mutate source files during commit, CI, or certification. All mutation must be explicit and human-initiated.

---

## Problem Statement

Auto-fix tooling in pre-commit hooks caused recurring "stash conflicts" during commits:

```
[WARNING] Unstaged files detected.
[INFO] Stashing unstaged files to /root/.cache/pre-commit/patch...
...
Stashed changes conflicted with hook auto-fixes... Rolling back fixes...
```

This is not a Git issue. It is a **governance breach in tooling design**.

### Governance Properties Violated by Auto-Fix

| Property | How Auto-Fix Violates It |
|----------|-----------------------------|
| Frozen design boundaries | Style changes can violate layer boundaries |
| Determinism | Same commit produces different code |
| Auditability | Mutations occur without human intent |
| Authority separation | Judges (CI) become editors |
| Phase discipline | Mutation happens outside intent |

---

## Solution: Non-Mutating Tooling Invariant

### Core Invariant (Constitutional)

> **No automated system may mutate source files during commit, CI, or certification.**

This is not a convention. It is a constitutional rule.

### Authority Separation

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

### A. Pre-Commit Hooks (Check-Only)

**Changed from auto-fix to check-only:**

| Before | After |
|--------|-------|
| `trailing-whitespace` (auto-fix) | `check-trailing-whitespace` (check-only) |
| `end-of-file-fixer` (auto-fix) | `check-eof-newline` (check-only) |
| `ruff` (auto-fix) | `ruff --no-fix` (check-only) |
| `ruff-format` (auto-fix) | `ruff-format --check` (check-only) |

### B. Explicit Mutation Commands

All auto-fix capability moved to explicit human commands:

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

### C. Governance-Safe Workflow

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

## Files Changed

### `.pre-commit-config.yaml`

- Removed: `trailing-whitespace`, `end-of-file-fixer` (auto-fix)
- Added: `check-trailing-whitespace`, `check-eof-newline` (check-only)
- Updated: `ruff` with `--no-fix`, `ruff-format` with `--check`

### `Makefile`

- Enhanced `lint-fix` target with:
  - Trailing whitespace fix
  - EOF newline fix
  - Ruff check with `--fix`
  - Ruff format

### `scripts/dev/fix_style.sh` (NEW)

Explicit human-initiated style mutation script with:
- Same 4-step fix process as `make lint-fix`
- Clear output and guidance
- Reference to PIN-290

### `docs/governance/NON_MUTATING_TOOLING_INVARIANT.md` (NEW)

Constitutional governance document defining the invariant.

---

## Enforcement

### Pre-Commit Hooks

Hooks now fail-only, never fix:
- Check whitespace and EOF issues
- Emit actionable error messages
- Direct developers to `make lint-fix`

### CI Pipeline

CI must be:
- Read-only
- Deterministic
- Replayable
- Non-interactive

CI may re-run all guards but must never mutate files.

### Violations

If any tool violates this invariant:

1. **Identify** the mutating tool
2. **Remove** the auto-fix behavior
3. **Add** a check-only alternative
4. **Document** the change

---

## Relation to Governance

| Governance Rule | Tooling Implication |
|-----------------|---------------------|
| Authority separation | Judges never mutate |
| Auditability | No silent changes |
| Determinism | Same input → same output |
| Design freeze | Auto-fix forbidden |
| Phase discipline | Intent before action |

---

## Test Verification

The Non-Mutating Tooling Invariant is verified by:

1. **Pre-commit hooks**: Run check-only, fail on issues
2. **CI guards**: Re-run checks without mutation
3. **Workflow compliance**: `make lint-fix` before staging

---

## References

- `docs/governance/NON_MUTATING_TOOLING_INVARIANT.md`
- `.pre-commit-config.yaml`
- `scripts/dev/fix_style.sh`
- `Makefile` (lint-fix target)

---

## Attestation

This PIN establishes the Non-Mutating Tooling Invariant as a constitutional governance rule.

All tooling must conform to this invariant. Violations require explicit ratification.
