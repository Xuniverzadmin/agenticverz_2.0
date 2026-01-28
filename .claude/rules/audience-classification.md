---
paths:
  - "backend/**/*.py"
---

# Audience Classification Rules (BL-AUD-001)

**Status:** ALWAYS-ON for all Python files
**Reference:** docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md Section 21

## Core Principle

> Audience boundaries prevent accidental feature exposure.
> CUSTOMER code must never import FOUNDER code.

## Always-On Behavior

Claude MUST check on EVERY Python file read/write:
1. Read header — look for `# AUDIENCE:` and `# Role:` in first 50 lines
2. Validate imports — check audience boundary violations
3. Report — if unclassified or violation found, REPORT immediately

## Audience Types

| Audience | Description |
|----------|-------------|
| CUSTOMER | Customer-facing (SDK, APIs, Console) |
| FOUNDER | Founder/Admin-only (ops tools) |
| INTERNAL | Internal infrastructure (workers, adapters) |
| SHARED | Shared utilities (logging, types) |

## Required File Header

```python
# Layer: L{x} — {Layer Name}
# AUDIENCE: CUSTOMER | FOUNDER | INTERNAL | SHARED
# Role: <single-line description of file purpose>
```

## Import Rules (HARD ENFORCEMENT)

| From Audience | Forbidden Imports |
|---------------|-------------------|
| CUSTOMER | FOUNDER modules |

## Validation

```bash
python3 scripts/ops/audience_guard.py --ci
python3 scripts/ops/audience_guard.py --summary
```
