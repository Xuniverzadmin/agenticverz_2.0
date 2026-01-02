# PIN-269: Pre-Commit Locality Rule

**Status:** ACTIVE (Governance Invariant)
**Created:** 2026-01-02
**Category:** CI / Developer Experience / Governance
**Severity:** BLOCKING

---

## Summary

Pre-commit hooks must only evaluate what the commit is responsible for.
Surfacing unrelated violations trains developers to skip hooks, which defeats governance.

---

## The Problem

Pre-commit hooks were running in "CI mode" - scanning the entire repository
regardless of what files were staged. This caused:

1. **DETACH002 errors in untouched files** - blocking unrelated commits
2. **Training developers to use `--no-verify`** - defeating the purpose of hooks
3. **Violating the self-guiding principle** - mystery failures from unrelated code

This is a **scope error**, not a tooling error.

---

## The Rule (Non-Negotiable)

```
Pre-commit = delta validation (staged files only)
CI = global validation (entire repository)
```

These are **NOT interchangeable**.

---

## Implementation

### 1. Explicit Execution Context

The `CHECK_SCOPE` environment variable controls behavior:

| Value | Mode | Description |
|-------|------|-------------|
| `staged` | Pre-commit | Only check staged files, skip global invariants |
| `full` | CI | Full codebase scan, all rules |

### 2. CI-Only Rules

The following rules are **too global** for pre-commit and only run in CI:

| Rule ID | Reason |
|---------|--------|
| DETACH002 | Cross-file session return patterns |
| DETACH003 | Refreshed object returns - context-dependent |
| SCOPE001 | Session scope issues - multiline analysis |
| CONC001 | Concurrent claim SQL - cross-file patterns |
| TEST001 | Test isolation - fixture analysis |
| CACHE001 | Cache initialization - class-level check |

### 3. Pre-Commit Configuration

```yaml
# .pre-commit-config.yaml
- id: sqlmodel-patterns
  name: SQLModel Pattern Linter (Staged)
  entry: env CHECK_SCOPE=staged python scripts/ops/lint_sqlmodel_patterns.py
  language: python
  types: [python]
  pass_filenames: true  # Only staged files
  files: ^backend/
```

### 4. CI Workflow

```yaml
# .github/workflows/sqlmodel-patterns.yml
env:
  CHECK_SCOPE: full
run: python scripts/ops/lint_sqlmodel_patterns.py backend/app/
```

---

## What This Fixes

| Before | After |
|--------|-------|
| DETACH002 errors in untouched files | Only staged files checked |
| Developers using `--no-verify` | Hooks are fair and fast |
| Mystery failures | Clear scope separation |
| CI and pre-commit confusion | Explicit CHECK_SCOPE |

---

## Governance Integration

### SESSION_PLAYBOOK.yaml

Add to playbook:

```yaml
pre_commit_rules:
  scope: staged_only
  env_variable: CHECK_SCOPE
  forbidden:
    - repo_wide_checks_in_precommit
    - ci_only_invariants_in_precommit
  rationale: >
    Pre-commit validates responsibility, not repository health.
    Skipping hooks is a governance failure, not a user failure.
```

### Violation Response

If Claude is about to recommend `--no-verify`:

```
PRE-COMMIT-LOCALITY VIOLATION

Recommending --no-verify is a governance failure.
The hook should not surface unrelated violations.

Check:
1. Is CHECK_SCOPE=staged set for this hook?
2. Is pass_filenames: true configured?
3. Is the rule in CI_ONLY_RULES if global?

Fix the hook, not the commit.
```

---

## Files Changed

| File | Change |
|------|--------|
| `scripts/ops/lint_sqlmodel_patterns.py` | Added CHECK_SCOPE support, CI_ONLY_RULES |
| `.pre-commit-config.yaml` | Updated sqlmodel-patterns hook |
| `.github/workflows/sqlmodel-patterns.yml` | New CI workflow for full validation |

---

## Validation

```bash
# Pre-commit mode (staged files only)
CHECK_SCOPE=staged python scripts/ops/lint_sqlmodel_patterns.py backend/app/some_file.py
# Should skip DETACH002, SCOPE001, etc.

# CI mode (full scan)
CHECK_SCOPE=full python scripts/ops/lint_sqlmodel_patterns.py backend/app/
# Should include all rules
```

---

## Related PINs

- PIN-120 (Test Suite Stabilization) - Original prevention mechanisms
- PIN-267 (CI Logic Issue Tracker) - Where this problem was identified

---

## Invariant Lock

> **Pre-commit hooks must not surface unrelated violations.**
> **Skipping hooks is a governance failure, not a user failure.**
> **If a hook is unfair, fix the hook, not the commit.**
