# Pre-Push Hook Scope Contract

**Status:** ACTIVE
**Created:** 2026-01-05
**Reference:** PIN-314

---

## Governing Principle

> **Pre-push hooks validate _push intent_, not workspace state.**

---

## Scope Rules

### What Gets Checked

| Scope | Definition | Command |
|-------|------------|---------|
| **Committed Delta** | Files changed between `origin/main` and `HEAD` | `git diff --name-only origin/main...HEAD` |

### What Does NOT Get Checked

| Excluded | Reason |
|----------|--------|
| Untracked files | Not part of push intent |
| Uncommitted changes | Not part of push intent |
| Stashed changes | Not part of push intent |
| Files outside commit range | Not being pushed |

---

## Hook Behavior

### File Discovery

```bash
# Correct: Only committed delta
git diff --name-only origin/main...HEAD

# Incorrect: Workspace scan (DO NOT USE)
find . -name "*.tsx"
```

### Empty File Set

If the committed delta contains no relevant files:
- Hook exits with **success (0)**
- Logs: "No files in push scope - skipping check"
- Does NOT fail

### No Remote

If `origin/main` does not exist (fresh repo):
- Hook skips git-scoped checks
- Falls back to milestone validation only

---

## Enforcement

### Pre-Push Hook Location

```
.git/hooks/pre-push
```

### Main Script

```
scripts/ops/ci_consistency_check.sh
```

### Frontend Lint

```
scripts/ops/lint_frontend_api_calls.py --files
```

---

## Bypass

If a legitimate push is blocked by hook issues:

```bash
git push --no-verify
```

This bypass should be:
- Documented in commit message
- Followed by fix in next session
- Never used to skip genuine errors

---

## Invariants

1. Pre-push hook MUST NOT scan workspace
2. Pre-push hook MUST use git delta
3. Pre-push hook MUST pass on empty delta
4. Pre-push hook MUST NOT block unrelated work

---

## Related

- [PIN-314](../memory-pins/PIN-314-pre-push-governance-fixes.md) — Pre-Push Governance Fixes
