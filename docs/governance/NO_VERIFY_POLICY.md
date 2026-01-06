# --no-verify Usage Policy

**Status:** ACTIVE
**Created:** 2026-01-06
**Reference:** PIN-319 (Governance Fix - Clean Push By Construction)
**Session Playbook:** Section 35 (Intent Lock System)

---

## Purpose

This document formalizes when `--no-verify` is allowed and when it is forbidden.
**`--no-verify` is NOT banned** — it exists for valid reasons. But its usage must be regulated to prevent governance erosion.

---

## The Problem

Before this policy:
- Hook failures at commit/push time caused noise
- Developers used `--no-verify` as a workaround
- No audit trail of why it was used
- Governance bypassed silently

After this policy:
- `--no-verify` usage is allowed but regulated
- Usage must have documented justification
- Certain failure types cannot be bypassed
- Intent purity is enforced at session start (not commit time)

---

## When --no-verify IS Allowed

| Condition | Example | Allowed |
|-----------|---------|---------|
| Scope pollution (formatting) | ruff-format false positive | YES |
| Intent documented | INTENT_DECLARATION.yaml exists | YES |
| PIN updated | Commit references correct PIN | YES |
| Formatting-only violations | Whitespace, EOF newline | YES |

### Allowed Workflow

```bash
# 1. Understand why the hook failed
git commit -m "message"  # Fails

# 2. Verify it's a scope/formatting issue (NOT a real failure)
# Look at the failure output - is it ruff-format, whitespace, etc.?

# 3. If allowed condition met, use --no-verify with mental note
git commit --no-verify -m "PIN-319: Message here

Note: --no-verify used due to ruff-format false positive
"
```

---

## When --no-verify IS Forbidden

| Condition | Example | Forbidden |
|-----------|---------|-----------|
| Test failures present | pytest failures | YES - FORBIDDEN |
| Semantic violations | BLCA violations | YES - FORBIDDEN |
| Security guard failures | detect-secrets | YES - FORBIDDEN |
| Missing intent declaration | No INTENT_DECLARATION.yaml | YES - FORBIDDEN |
| SQLModel pattern violations | ROW001/DETACH001 errors | YES - FORBIDDEN |

### Forbidden Workflow (DO NOT DO THIS)

```bash
# WRONG: Tests are failing but you use --no-verify anyway
pytest tests/  # FAILS
git commit --no-verify -m "message"  # GOVERNANCE VIOLATION

# WRONG: Security secrets detected but you bypass
git commit -m "message"  # detect-secrets fails
git commit --no-verify -m "message"  # SECURITY VIOLATION
```

---

## Justification Format (Optional but Recommended)

When using `--no-verify`, include in commit message:

```
PIN-XXX: Your commit message

--no-verify justification:
- Reason: ruff-format false positive on already-formatted file
- Intent: PIN-319
- Files bypassed: backend/app/api/founder_explorer.py
```

---

## Audit Trail

The system logs `--no-verify` usage via:

1. **Git reflog**: Shows commits made with --no-verify
2. **CI verification**: Full validation runs in CI regardless
3. **Post-commit hook**: Optional logging (if configured)

---

## Root Cause Fix

The proper fix is NOT to use `--no-verify` more carefully.
The proper fix is **Intent Lock System** (SESSION_PLAYBOOK Section 35):

1. Declare intent at session start (`INTENT_DECLARATION.yaml`)
2. Worktree sanity enforced continuously
3. Mixed intent detected BEFORE commit, not at commit
4. Clean commits pass instantly
5. `--no-verify` rarely needed

---

## Decision Tree

```
Hook failed at commit time?
│
├── Is it a TEST failure?
│   └── YES → FIX THE TEST (--no-verify FORBIDDEN)
│
├── Is it a SECURITY failure (detect-secrets)?
│   └── YES → FIX THE SECRET (--no-verify FORBIDDEN)
│
├── Is it a SEMANTIC violation (BLCA, SQLModel)?
│   └── YES → FIX THE CODE (--no-verify FORBIDDEN)
│
├── Is it a SCOPE violation (files outside intent)?
│   ├── Is INTENT_DECLARATION.yaml present?
│   │   ├── NO → Create it first
│   │   └── YES → Was scope intentionally narrow?
│   │       ├── YES → Update INTENT_DECLARATION.yaml
│   │       └── NO → Stash the out-of-scope files
│   └── Still need to bypass? → --no-verify ALLOWED (with justification)
│
└── Is it a FORMATTING issue (ruff-format, whitespace)?
    ├── Run: make lint-fix
    ├── Still failing? → Likely false positive
    └── --no-verify ALLOWED (with justification)
```

---

## Quick Reference

```
ALLOWED:
  - Formatting false positives
  - Scope pollution (after intent documented)

FORBIDDEN:
  - Test failures
  - Security failures
  - Semantic violations
  - Missing intent

IF UNSURE:
  - Don't use --no-verify
  - Fix the root cause
  - Ask for help
```

---

## Related Documents

- `docs/governance/INTENT_DECLARATION_SCHEMA.yaml` - Intent declaration format
- `INTENT_DECLARATION.yaml` - Current session intent
- `scripts/ops/worktree_sanity_check.py` - Continuous enforcement
- `docs/playbooks/SESSION_PLAYBOOK.yaml` - Section 35 (Intent Lock)
