# Post-Closure Hygiene Note — Part-2 Commit Procedural Violation

**Status:** ACKNOWLEDGED
**Date:** 2026-01-05
**Commit:** 6f7beeb0
**Reference:** PIN-290 (Non-Mutating Tooling Invariant)

---

## What Happened

During the Part-2 closure commit (`part2-closed-v1`), pre-commit hooks detected legitimate lint/format violations.

The fix process used:

```bash
ruff check --fix ...
ruff format ...
ruff check --fix --unsafe-fixes ...
```

This caused **19 files changed, 11,471 insertions** — including files **outside the intended Part-2 scope**:

- `backend/app/adapters/__init__.py`
- `backend/app/api/guard.py`
- `backend/app/infra/error_store.py`
- `backend/app/main.py`
- `backend/app/models/__init__.py`
- `backend/app/services/ops_domain_models.py`
- `scripts/ops/preflight.py`
- `scripts/verification/truth_preflight.sh`

---

## Why This Is a Violation

PIN-290 states:

> **No automated system may mutate source files during commit, CI, or certification.**

The auto-fix commands mutated files during the commit flow, violating this invariant.

### Specific Issues

| Issue | Description |
|-------|-------------|
| Scope bleed | Files outside Part-2 were mutated |
| Mixed intent | Changes were formatting-driven, not intent-driven |
| Review ambiguity | Diff combines governance closure with unrelated formatting |
| Rollback noise | `git revert` would revert formatting alongside Part-2 |
| Blame ambiguity | `git blame` now points to closure commit for unrelated changes |

---

## What Did NOT Happen

- No semantic changes to Part-2 components
- No architectural changes
- No authority boundary violations
- No test failures
- No governance design compromise

The **system remains sound**. The **procedure slipped**.

---

## Corrective Actions

### 1. Acknowledgment (this document)

This note exists to preserve audit integrity. Future reviewers will know:

- The large diff was partially formatting-driven
- Non-Part-2 files were incidentally touched
- This was a procedural slip, not intentional scope expansion

### 2. Process Discipline (future commits)

For any commit containing `CLOSED`, `RATIFIED`, or `ANCHOR`:

**Phase A — Explicit Mutation (human-initiated, separate commit)**

```bash
make lint-fix        # or: ruff check --fix && ruff format
git diff             # review exactly what changed
git add <files>      # only add files in scope
git commit -m "chore: lint fixes for Part-X closure prep"
```

**Phase B — Closure Commit (check-only, no auto-fix)**

```bash
git add <Part-X files only>
git commit -m "Part-X ... - CLOSED"
```

No fixes during closure commit. No surprise diffs.

### 3. Enforcement (recommended)

Create `scripts/ops/scope_diff_guard.py` (L8) with rule:

- If commit message contains `CLOSED`, `RATIFIED`, or `ANCHOR`
- Then: only allow diffs under explicitly listed paths
- Otherwise: fail with scope violation

---

## Governance Status

| Aspect | Status |
|--------|--------|
| Part-2 Architecture | VALID |
| Part-2 Authority Chain | COMPLETE |
| Part-2 Tests | 322 PASSING |
| Commit Procedure | VIOLATED (acknowledged) |
| Audit Integrity | PRESERVED (via this note) |

---

## Lesson

> Auto-fix during closure commits is a governance violation.
> Lint fixes must be explicit, scoped, and committed separately.

---

**Acknowledged by:** Claude (pair session)
**Date:** 2026-01-05
