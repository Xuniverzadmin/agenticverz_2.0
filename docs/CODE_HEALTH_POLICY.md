# Code Health Policy

**Version:** 1.0
**Status:** ACTIVE
**Last Updated:** 2025-12-24
**Authority:** PIN-121 (Mypy Technical Debt)

---

## Purpose

This document defines the steady-state code health system for AOS. It is designed to:

- Keep type errors **visible**, not hidden
- Keep fixes **mechanical**, not heroic
- Preserve **design pressure** from real issues
- Prevent **signal death** from over-optimization

---

## The Golden Rule

> **Any new mypy error is either a regression or a documented architectural decision.**

We do not chase zero errors. We maintain visibility and bounded debt.

---

## Current Baselines

| Tool | Count | Target | Status |
|------|-------|--------|--------|
| **Mypy** | ~999 errors | ~900-1000 | LOCKED |
| **Ruff** | 0 auto-fixable | 0 | ENFORCED |
| **Zone A** | 0 errors | 0 | BLOCKING |

---

## Mypy Policy

### Zones

| Zone | Strictness | Enforcement | Files |
|------|------------|-------------|-------|
| **A: Critical** | Strict | Pre-commit blocks | IR, evidence, pg_store, canonicalize |
| **B: Standard** | Moderate | CI warns | API, skills, integrations, agents |
| **C: Flexible** | Baseline only | Freeze | Metrics, workers, main.py, models |

### Accepted Debt Categories

| Category | Count | Rule |
|----------|-------|------|
| **A: Structural** | ~250 | `# type: ignore` with reason comment |
| **B: Diminishing Returns** | ~150 | Accept baseline, no ignores needed |
| **C: Requires Refactor** | ~250 | No ignores allowed, must remain visible |

### What NOT to Do

1. Do not try to drive mypy below ~900
2. Do not "clean up" Category C with casts
3. Do not add `# type: ignore` without category comment
4. Do not blanket-ignore any warnings

---

## Ruff Policy

### Auto-Fix + Gate (CI fails on diffs)

These run automatically and must produce no changes:

| Code | Description |
|------|-------------|
| `F401` | Unused imports |
| `F841` | Unused locals |
| `I001` | Import sorting |
| `E741` | Ambiguous names |
| `E711/E712` | Style comparisons |

### Scoped Ignores (Don't chase)

| Code | Allowed Scope |
|------|---------------|
| `E402` | `alembic/versions/*.py` only |
| `ASYNC230/101` | `tests/**` only |

### Hard Fail (Never ignore)

| Code | Description |
|------|-------------|
| `F821` | Undefined name |
| `ASYNC1xx` | Blocking in prod async code |

---

## Developer Workflow

### Before Every Commit

```bash
# Run autofix tools
python tools/mypy_autofix/apply.py
ruff check --fix

# Verify no diffs
git diff --exit-code
```

### Pre-Commit Hooks (Automatic)

- `ruff` - Format and lint
- `mypy` - Type check (warning mode, skippable with `SKIP=mypy`)
- `detect-secrets` - Credential scanning

### CI Enforcement

| Check | Behavior |
|-------|----------|
| Ruff autofix diffs | **Block** |
| Zone A mypy increase | **Block** |
| Zone B/C mypy increase | **Warn** |
| `F821` undefined name | **Block** |

---

## Adding New Code

### For Zone A Files (Critical)

All new code in Zone A must:
- Pass mypy strict mode
- Have no `# type: ignore` without explicit reason
- Be covered by the autofix system

### For Zone B/C Files

New code should:
- Not introduce new error patterns
- Use existing patterns for framework quirks
- Document any new `# type: ignore` with category

---

## Quarterly Review

Every 2-4 weeks or after major refactors:

1. **Recount Category C** — Has anything moved to A or B?
2. **Check for promotion** — Any autofixable patterns that emerged?
3. **Validate baselines** — Run `python scripts/mypy_zones.py --report`
4. **Update counts** — If categories shifted, update PIN-121

---

## Quick Reference Commands

```bash
# Check mypy error count
mypy backend/app/ --ignore-missing-imports 2>&1 | grep -c ': error:'

# Run Zone A only
python scripts/mypy_zones.py --zone-a

# Full zone report
python scripts/mypy_zones.py --report

# Run autofix (dry-run)
python tools/mypy_autofix/apply.py --dry-run

# Ruff check
ruff check backend/

# Ruff fix
ruff check --fix backend/
```

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [PIN-121](memory-pins/PIN-121-mypy-technical-debt.md) | Full mypy debt ledger and categories |
| [PIN-120](memory-pins/PIN-120-test-suite-stabilization.md) | Prevention mechanisms (PREV-1 to PREV-20) |
| [pyproject.toml](../pyproject.toml) | Tool configuration |
| [.pre-commit-config.yaml](../.pre-commit-config.yaml) | Pre-commit hooks |

---

## FAQ

### Q: Mypy found a new error. What do I do?

1. Check if it's in Zone A → **Must fix before merge**
2. Check if autofix handles it → Run `python tools/mypy_autofix/apply.py`
3. Check PIN-121 categories → Document if accepting as debt
4. Otherwise → Fix it or add to ledger with justification

### Q: Can I add `# type: ignore`?

- **Category A**: Yes, with reason comment (e.g., `# type: ignore[call-overload]  # SQLAlchemy stub incomplete`)
- **Category B**: No ignores needed, baseline accepted
- **Category C**: **No ignores allowed** — must remain visible

### Q: Ruff is complaining about test files. What do I do?

Check if it's a scoped ignore (E402, ASYNC). If so, it should already be configured in `pyproject.toml`. If not, fix it.

### Q: Should I clean up unrelated mypy errors while I'm in a file?

Only if:
- It's Zone A (critical)
- It's a trivial fix (guard, cast, annotation)
- You're not introducing new patterns

Otherwise, leave it. Drive-by cleanups often create more debt than they fix.

---

## Version History

| Date | Change |
|------|--------|
| 2025-12-24 | Initial policy document created |
| 2025-12-24 | Steady-state locked at 999 mypy errors |
| 2025-12-24 | Ruff policy categorized (auto-fix, scoped, block) |
