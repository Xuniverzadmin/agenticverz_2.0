# PIN-297: Scope Diff Guard - Closure Commit Enforcement

**Status:** 📋 ACTIVE
**Created:** 2026-01-05
**Category:** Governance / Enforcement
**Milestone:** Part-2 Closure

---

## Summary

L8 enforcement tool that prevents closure-tagged commits from mutating frozen code scope. Implements the procedural discipline learned from Part-2 closure violation.

---

## Details

## Problem Statement

During the Part-2 closure commit (6f7beeb0), pre-commit hooks detected legitimate lint violations. The fix process (`ruff check --fix`) mutated 19 files including 8 files **outside the intended Part-2 scope**.

This was a **procedural violation** of PIN-290 (Non-Mutating Tooling Invariant):

> A closure commit is a legal act, not a coding act.
> Lint fixes must be separate commits before closure.

### Files Touched Outside Scope

- `backend/app/adapters/__init__.py`
- `backend/app/api/guard.py`
- `backend/app/infra/error_store.py`
- `backend/app/main.py`
- `backend/app/models/__init__.py`
- `backend/app/services/ops_domain_models.py`
- `scripts/ops/preflight.py`
- `scripts/verification/truth_preflight.sh`

---

## Solution: Scope Diff Guard

Created `scripts/ops/scope_diff_guard.py` as L8 enforcement:

### Trigger Keywords

If commit message contains any of:
- `CLOSED`
- `RATIFIED`
- `ANCHOR`
- `FREEZE`
- `PART-2`
- `PART-3`
- `CONSTITUTIONAL`

### Allowed Paths (Closure Commits Only)

```python
ALLOWED_PATHS = [
    "docs/governance/",
    "docs/memory-pins/",
    "docs/contracts/",
    "docs/playbooks/",
    "docs/templates/",
    "scripts/ci/",
    "scripts/ops/scope_diff_guard.py",
    ".github/workflows/",
    ".pre-commit-config.yaml",
    "CLAUDE.md",
    "CLAUDE_AUTHORITY.md",
    "CLAUDE_BOOT_CONTRACT.md",
    "CLAUDE_PRE_CODE_DISCIPLINE.md",
    "CLAUDE_BEHAVIOR_LIBRARY.md",
]
```

### Forbidden Paths (Hard Block)

```python
FORBIDDEN_PATHS = [
    "backend/app/",
    "backend/tests/",
    "sdk/",
    "website/",
]
```

---

## Enforcement

### Pre-Commit Hook

Wired into `.pre-commit-config.yaml`:

```yaml
- id: scope-diff-guard
  name: Scope Diff Guard (Closure Commits)
  entry: python scripts/ops/scope_diff_guard.py --verbose
  language: python
  pass_filenames: false
  stages: [pre-commit]
  always_run: true
```

### Behavior

1. Detects closure keywords in commit message
2. Gets list of staged files
3. Checks each file against allowed/forbidden paths
4. **Hard fails** if any file is outside scope
5. Provides clear resolution steps in error message

### Resolution Guidance

When blocked, developers must:

1. **Split the commit into TWO commits:**
   - FIRST: Lint/format fixes (non-closure)
   - SECOND: Closure commit (governance only)

2. Or remove closure keyword if not actually a closure

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `scripts/ops/scope_diff_guard.py` | L8 enforcement script |
| `.pre-commit-config.yaml` | Hook integration |
| `docs/governance/POST_CLOSURE_HYGIENE_NOTE.md` | Procedural violation acknowledgment |

---

## Governance Relation

| Principle | Implementation |
|-----------|----------------|
| Closure commits are legal acts | Only governance paths allowed |
| No implicit mutation | Hard fail, no auto-fix |
| Scope discipline | Forbidden paths enforced |
| Audit integrity | Closure diffs are pure |

---

## Usage

```bash
# As pre-commit hook (automatic)
git commit -m "Part-3 ... - CLOSED"

# With explicit message (CI mode)
python scripts/ops/scope_diff_guard.py --message "Part-2 - CLOSED"

# Dry run (check without failing)
python scripts/ops/scope_diff_guard.py --dry-run
```

---

## References

- `scripts/ops/scope_diff_guard.py`
- `docs/governance/POST_CLOSURE_HYGIENE_NOTE.md`
- PIN-290 (Non-Mutating Tooling Invariant)
- PIN-284 (Phase-1 Closure Note)


---

## Related PINs

- [PIN-290](PIN-290-.md)
- [PIN-284](PIN-284-.md)
