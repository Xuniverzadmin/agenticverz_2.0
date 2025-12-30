# Quarantine Ledger

Purpose:
This ledger records **intentional technical debt** introduced via quarantines
(mypy ignores, lint suppressions, legacy modules).

Debt is:
- Allowed
- Bounded
- Explicit
- Tracked

Unregistered debt is **invalid**.

---

## Debt Rules (Non-Negotiable)

1. Every quarantine MUST have an entry here.
2. Every entry MUST have an expiry trigger.
3. Debt counts against a **ceiling**.
4. New debt requires either:
   - Paying existing debt, or
   - Explicit exception approval.

---

## Debt Ceilings

| Category                     | Ceiling Rule                              |
|------------------------------|-------------------------------------------|
| Quarantined mypy modules     | ≤ 15% of runtime code (L1–L6)             |
| `type: ignore` lines         | ≤ 2 per file                              |
| Legacy untyped modules       | Fixed allowlist only                      |
| Tool config suppressions     | No growth after housekeeping baseline     |

Breaching a ceiling **blocks CI**.

---

## Debt Entries

### Template

```yaml
id: TD-XXX
scope: <file | module | glob>
layer: Lx
type: typing | lint | legacy | config
reason: <why this debt exists>
introduced_on: YYYY-MM-DD
introduced_by: <commit | housekeeping | migration>
expiry: <Phase | Date | Trigger>
remediation_hint: <how this debt can be removed>
```

---

### Active Debt

```yaml
id: TD-001
scope: backend/app/policy/engine.py
layer: L4
type: typing
reason: circular dependency with adapter layer
introduced_on: 2025-12-30
introduced_by: housekeeping
expiry: Phase B
remediation_hint: split interface from implementation
```

```yaml
id: TD-002
scope: backend/app/api/guard.py
layer: L2a
type: typing
reason: SQLModel exec() typing issues, 200+ errors
introduced_on: 2025-12-30
introduced_by: housekeeping
expiry: Phase B
remediation_hint: gradual SQLModel typing fixes
```

```yaml
id: TD-003
scope: backend/app/api/agents.py
layer: L2
type: typing
reason: complex SQLModel patterns, 150+ errors
introduced_on: 2025-12-30
introduced_by: housekeeping
expiry: Phase B
remediation_hint: gradual SQLModel typing fixes
```

```yaml
id: TD-004
scope: backend/app/main.py
layer: L2
type: lint
reason: deferred router imports (FastAPI pattern)
introduced_on: 2025-12-30
introduced_by: housekeeping
expiry: never (structural)
remediation_hint: n/a - FastAPI requires this pattern
```

```yaml
id: TD-005
scope: backend/app/integrations/bridges.py
layer: L4
type: typing
reason: TYPE_CHECKING import for IntegrationDispatcher
introduced_on: 2025-12-30
introduced_by: housekeeping
expiry: Phase B
remediation_hint: resolve circular dependency
rca_reference: |
  Root cause identified via ARCH-GOV-007 audit (2025-12-30):
  - Directory was mislabeled L3 (Boundary Adapter), actually L4 (Domain Engine)
  - "integrations" means "pillar integration", not "external integration"
  - Circular dep likely stems from unclear layer boundaries
  - See: PIN-249, __init__.py historical note
```

```yaml
id: TD-006
scope: backend/alembic/versions/*.py
layer: L7
type: lint
reason: E402 required for alembic migration pattern
introduced_on: 2025-12-30
introduced_by: housekeeping
expiry: never (structural)
remediation_hint: n/a - alembic requires this pattern
```

```yaml
id: TD-007
scope: backend/app/contracts/__init__.py
layer: L4
type: lint
reason: F405/F401 star imports for contract re-exports
introduced_on: 2025-12-30
introduced_by: housekeeping
expiry: never (structural)
remediation_hint: n/a - intentional re-export pattern
```

---

## Debt Summary

| Type | Count | Ceiling Status |
|------|-------|----------------|
| Typing (mypy quarantine) | 10 modules | Under ceiling |
| Lint (E402 deferred imports) | ~15 files | Under ceiling |
| Config suppressions | 4 rules | Frozen at baseline |

Last updated: 2025-12-30
