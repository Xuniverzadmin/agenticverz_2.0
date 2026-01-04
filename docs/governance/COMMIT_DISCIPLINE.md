# Governance-Safe Commit Discipline

**Status:** ACTIVE
**Effective:** 2026-01-04
**Authority:** PIN-284 (Platform Monitoring System)
**Reference:** platform-health-v1 tag

---

## Prime Rule

> **Pre-commit hooks must NEVER mutate files.**
> **All mutation happens explicitly before staging.**

---

## Why This Matters

Constitutional code requires:

1. **Audit-clean diffs** - Every change must be intentional and traceable
2. **Frozen file protection** - Auto-fixers can corrupt frozen artifacts
3. **Deterministic commits** - Same code → same commit
4. **Stash-safe workflow** - No conflicts during selective staging

Auto-fix during commit violates all four principles.

---

## The Problem (What Was Happening)

```
Pre-commit stashes unstaged changes
→ Auto-fix hooks modify staged files
→ Try to re-apply stash
→ Conflicts
→ Rollback everything
→ Commit fails
```

This repeats **every time** you do governance commits with selective staging.

---

## The Solution (Governance-Safe Commit Mode)

### Workflow

```bash
# 1. Write code
#    (normal development)

# 2. EXPLICIT mutation
make lint-fix

# 3. Stage changes
git add <files>

# 4. Commit (check-only hooks verify)
git commit -m "message"
```

### Commands

| Command | Purpose |
|---------|---------|
| `make lint-fix` | Auto-fix lint errors and format code (EXPLICIT) |
| `make lint-check` | Check lint errors without fixing |
| `git commit` | Runs CHECK-ONLY hooks (no mutation) |

---

## Pre-Commit Configuration

The `.pre-commit-config.yaml` is configured for CHECK-ONLY mode:

```yaml
# Ruff hooks - CHECK ONLY (no auto-fix)
- id: ruff
  args: [--no-fix]       # Check only
- id: ruff-format
  args: [--check]        # Check only
```

**Never use:**
- `--fix`
- `--exit-non-zero-on-fix`
- Any auto-fixing hook

---

## Enforcement

| Rule | Enforcement |
|------|-------------|
| COMMIT-001 | Pre-commit hooks must not mutate files |
| COMMIT-002 | All mutation must be via `make lint-fix` |
| COMMIT-003 | Constitutional commits require this workflow |
| COMMIT-004 | `--no-verify` is forbidden for governance code |

---

## When This Applies

This discipline is **mandatory** for:

- Any commit touching frozen files
- Constitutional code (L4 services, L8 guards)
- Governance artifacts (PINs, contracts, closures)
- Phase closure commits
- Tag creation commits

It is **recommended** for all commits.

---

## Anti-Patterns (Forbidden)

| Pattern | Why Forbidden |
|---------|---------------|
| `git commit --no-verify` | Bypasses all governance checks |
| `SKIP=ruff git commit` | Selective bypass erodes trust |
| Auto-fix hooks | Causes stash conflicts |
| `git reset` workarounds | Recovery, not workflow |
| Committing unfixed lint errors | CI will fail anyway |

---

## Recovery (If You Already Hit This)

If pre-commit rolled back auto-fixes:

```bash
# 1. Reset staging area
git reset HEAD

# 2. Run explicit fix
make lint-fix

# 3. Re-stage files
git add <files>

# 4. Retry commit
git commit -m "message"
```

---

## Reference

- PIN-284: Platform Monitoring System (Phase-1 Closure)
- `.pre-commit-config.yaml`: Check-only hooks
- `Makefile`: lint-fix and lint-check targets
- `platform-health-v1` tag: Immutable governance anchor

---

## Attestation

This commit discipline ensures that:

1. Constitutional code remains audit-clean
2. Auto-fixers cannot corrupt frozen files
3. Stash conflicts are impossible
4. Every mutation is intentional

**Governance integrity requires explicit control over mutation.**
