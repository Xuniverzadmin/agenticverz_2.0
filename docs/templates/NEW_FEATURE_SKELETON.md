# New Feature Skeleton

**Status:** ENFORCED
**Reference:** PIN-269 (CLAUDE_AUTHORITY.md), PIN-268 (GU-003)

---

## Purpose

This skeleton MUST be used before implementing any new feature. It ensures:

1. FeatureIntent is declared (CLAUDE_AUTHORITY.md §4)
2. Invariant references are identified (CLAUDE_AUTHORITY.md §5)
3. Artifact summary block is included (CLAUDE_AUTHORITY.md §7)
4. Pre-flight requirements are satisfied (CLAUDE_AUTHORITY.md §2)

**Rule:** Features do not start in code. Features start as intent and must earn execution.

---

## PHASE 1: Pre-Flight Declaration

Before writing ANY code, Claude must output this block:

```markdown
## PRE-FLIGHT: {Feature Name}

### Applicable FeatureIntent(s)
- [ ] PURE_QUERY — Read-only, no side effects
- [ ] STATE_MUTATION — Writes to database
- [ ] EXTERNAL_SIDE_EFFECT — Calls external APIs
- [ ] RECOVERABLE_OPERATION — Must be crash-resumable

**Selected:** {FeatureIntent}

### Applicable TransactionIntent(s)
- [ ] READ_ONLY — Select queries only
- [ ] ATOMIC_WRITE — Single atomic write
- [ ] LOCKED_MUTATION — Requires locking

**Selected:** {TransactionIntent}

### Relevant Invariants
| Invariant | Document | Applies? | Why? |
|-----------|----------|----------|------|
| M10 Recovery constraints | [M10_RECOVERY_INVARIANTS.md](../invariants/M10_RECOVERY_INVARIANTS.md) | YES / NO | {reason} |
| PB-S1 Immutability | [PB_S1_INVARIANTS.md](../invariants/PB_S1_INVARIANTS.md) | YES / NO | {reason} |
| {Custom invariant} | {doc path} | YES / NO | {reason} |

### Expected Blast Radius
- **L2 (API):** {affected endpoints}
- **L3 (Adapters):** {affected adapters}
- **L4 (Domain):** {affected domain engines}
- **L5 (Workers):** {affected workers}
- **L6 (Platform):** {affected platform services}

### Expected Artifacts
| Type | Path | Description |
|------|------|-------------|
| Create | `app/{path}` | {description} |
| Modify | `app/{path}` | {description} |
| Delete | `app/{path}` | {description} |
| Governance | `docs/{path}` | {description} |
```

---

## PHASE 2: Module Template (for new files)

Every new module in critical directories must include this header:

```python
# Layer: L{x} — {Layer Name}
# Product: {product-name | system-wide}
# Temporal:
#   Trigger: {user | api | worker | scheduler | external}
#   Execution: {sync | async | deferred}
# Role: {One-line description of what this module does}
# Callers: {Who calls this?}
# Allowed Imports: L{x}, L{y}
# Forbidden Imports: L{z}
# Reference: PIN-{xxx}
# Invariants: {list of applicable invariants}

"""
{ModuleName}: {Brief description}

FeatureIntent: {PURE_QUERY | STATE_MUTATION | EXTERNAL_SIDE_EFFECT | RECOVERABLE_OPERATION}
TransactionIntent: {READ_ONLY | ATOMIC_WRITE | LOCKED_MUTATION}

Invariants:
- {invariant 1}: {why it applies}
- {invariant 2}: {why it applies}

This module {what it does}.
"""

from app.infra import FeatureIntent, RetryPolicy

# === FEATURE INTENT DECLARATION (Required) ===
FEATURE_INTENT = FeatureIntent.{SELECTED}
RETRY_POLICY = RetryPolicy.{SAFE | NEVER | DANGEROUS}

# === INVARIANT ACKNOWLEDGMENTS ===
# This module respects:
# - {invariant 1}: enforced by {how}
# - {invariant 2}: enforced by {how}

# ... rest of imports and code ...
```

---

## PHASE 3: Completion Attestation

After implementing a feature, Claude MUST output:

```markdown
## ARTIFACTS SUMMARY: {Feature Name}

**Date:** {YYYY-MM-DD}
**PIN:** {PIN-XXX or "N/A"}

### Artifacts Created
| Path | Layer | Artifact Class | Description |
|------|-------|----------------|-------------|
| `{path}` | L{x} | CODE | {description} |

### Artifacts Modified
| Path | Change Type | Description |
|------|-------------|-------------|
| `{path}` | {bugfix | refactor | behavior_change} | {description} |

### Artifacts Deleted
- {None | list of deleted files}

### Governance Updated
| Document | Change |
|----------|--------|
| `{doc path}` | {description} |

### Invariant Verification
| Invariant | Test | Status |
|-----------|------|--------|
| {invariant 1} | `test_{x}` | PASS / FAIL |
| {invariant 2} | `test_{y}` | PASS / FAIL |

### CI Verification
- [ ] All tests pass
- [ ] BLCA status: CLEAN
- [ ] No new mypy errors
- [ ] Feature intent checker passes
```

---

## Quick Reference: Intent Selection

| Scenario | FeatureIntent | RetryPolicy | TransactionIntent |
|----------|---------------|-------------|-------------------|
| Query data from DB | PURE_QUERY | N/A | READ_ONLY |
| Write to DB (single row) | STATE_MUTATION | SAFE | ATOMIC_WRITE |
| Write to DB (requires lock) | STATE_MUTATION | SAFE | LOCKED_MUTATION |
| Call external API | EXTERNAL_SIDE_EFFECT | NEVER | ATOMIC_WRITE |
| Worker task (must be resumable) | RECOVERABLE_OPERATION | SAFE | LOCKED_MUTATION |

---

## Quick Reference: When Invariants Apply

| If your feature... | Check these invariants |
|--------------------|------------------------|
| Touches `recovery_candidates` table | M10_RECOVERY_INVARIANTS.md |
| Modifies execution traces | PB_S1_INVARIANTS.md |
| Handles policy bypass | PB_S1_INVARIANTS.md |
| Touches cost records | {cost invariants if exist} |
| Creates new DB constraints | Create new invariant doc |

---

## CI Enforcement

Features without pre-flight are invalid per CLAUDE_AUTHORITY.md §2.

If this skeleton is skipped, the task is **INVALID**.

---

## References

- CLAUDE_AUTHORITY.md (governing document)
- PIN-269 (Claude Authority Spine)
- PIN-268 (Guidance System Upgrade)
- PIN-264 (Feature Intent System)
- docs/invariants/INDEX.md (invariant catalog)
- docs/templates/INTENT_BOILERPLATE.md (intent templates)
- docs/templates/ARTIFACT_INTENT.yaml (artifact declarations)
