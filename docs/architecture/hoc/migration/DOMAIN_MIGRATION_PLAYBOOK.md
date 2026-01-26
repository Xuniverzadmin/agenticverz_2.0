# Domain Migration Playbook

**Status:** ACTIVE
**Created:** 2026-01-18
**Reference Implementation:** Incidents Domain V2 Migration
**Scope:** Repeatable pattern for fixing domain anti-patterns

---

## Executive Summary

This playbook documents the **proven pattern** for migrating domains from query-param-based topic filtering to endpoint-scoped topic boundaries.

**Origin:** Successfully applied to the Incidents Domain (2026-01-18).

**Core insight:**
> Topic-scoped endpoints + shadow validation + registry locks scale better than any review process.

---

## When to Use This Playbook

### Symptoms That Indicate Need

| Symptom | Example |
|---------|---------|
| Generic list endpoints used by multiple topics | `/api/v1/things?topic=X` |
| Query-param-driven semantics | Caller controls what data scope they receive |
| Frontend aggregation for historical views | UI computes trends/distributions |
| Capabilities with 0/N invariants | Registry claims capability works, but it doesn't |
| Same endpoint serving different UX contexts | ACTIVE and RESOLVED panels both hit `/things` |

### Common Suspect Domains

- Alerts
- Jobs / Tasks
- Policies
- Experiments
- Audits
- Any domain with "list by status" patterns

---

## The Five-Phase Pattern

### Phase 0: Freeze Semantics (Paper Change)

**Duration:** Immediate
**Code Changes:** None
**Risk:** None

**Actions:**
1. Declare topic scopes as endpoint-owned
2. Mark generic endpoint as INTERNAL/DEPRECATED
3. Declare frontend aggregation deprecated
4. Get team acknowledgment

**Exit Criteria:**
- [ ] Migration plan document approved
- [ ] Topic boundaries defined
- [ ] No capability registry changes yet

---

### Phase 1: Add Topic-Scoped Endpoints (Additive)

**Duration:** 1-2 days
**Code Changes:** API file only
**Risk:** Low (additive)

**Actions:**
1. Add new endpoints that hardcode topic semantics
2. Do NOT remove or modify generic endpoint
3. Do NOT rebind capabilities yet
4. Do NOT change panels yet
5. Add unit tests for each endpoint

**Endpoint Pattern:**
```python
@router.get("/things/active")  # Topic = ACTIVE, hardcoded
async def list_active_things(...):
    # Filter is built-in, not caller-controlled
    stmt = select(Thing).where(Thing.state == "ACTIVE")
```

**Exit Criteria:**
- [ ] All topic-scoped endpoints return valid responses
- [ ] All endpoints enforce tenant isolation
- [ ] OpenAPI spec updated
- [ ] Unit tests pass

---

### Phase 2: Shadow Validation (Critical)

**Duration:** 2-3 days
**Code Changes:** Logging/telemetry only
**Risk:** None (observational)

**Actions:**
1. Compare generic endpoint vs topic-scoped endpoints
2. Verify identity and count parity
3. Log any discrepancies
4. Document known schema gaps (acceptable NULLs)

**Shadow Comparison Matrix:**
| Comparison | Expected Result |
|------------|-----------------|
| Generic with filter vs topic-scoped | Identical rows |
| Frontend aggregation vs backend analytics | Identical counts |

**Exit Criteria:**
- [ ] Zero discrepancies in shadow comparison (72 hours minimum)
- [ ] Backend endpoints eliminate need for frontend aggregation
- [ ] Schema gaps documented (not fixed - separate workstream)

---

### Phase 3: Panel Rebinding (Controlled)

**Duration:** 1 day
**Code Changes:** Frontend API calls, Intent Ledger
**Risk:** Medium (UI behavior change)

**Actions:**
1. Rebind panels from generic to topic-scoped fetch functions
2. Update response shape handling (if changed)
3. Verify all panels render correctly
4. Update Intent Ledger bindings

**Blast Radius Order:**
1. ACTIVE topic (lowest risk - most recent data)
2. RESOLVED topic (medium risk)
3. HISTORICAL topic (highest risk - aggregation changes)

**Rollback Trigger:**
- Any panel shows empty/error state → revert and investigate

**Exit Criteria:**
- [ ] All panels render correctly
- [ ] No console errors
- [ ] Telemetry shows panels hitting new endpoints
- [ ] No `fetchGeneric()` calls remain in components

---

### Phase 4: Capability Registry Update

**Duration:** 1 day
**Code Changes:** Capability YAML files
**Risk:** Low (registry alignment)

**Critical Order (Trap Avoidance):**
1. **Create NEW capability files FIRST** (bound to topic-scoped endpoints)
2. **Promote new capabilities** (DECLARED → OBSERVED with evidence)
3. **Update Intent Ledger** (panels → new capabilities)
4. **THEN deprecate old capabilities** (mark status: DEPRECATED)

**Never:** Edit old capabilities first. Always create new ones.

**Exit Criteria:**
- [ ] All panel-bound capabilities map to topic-scoped endpoints
- [ ] No capability maps to generic endpoint
- [ ] All new capabilities have N/N invariants
- [ ] Legacy capabilities explicitly deprecated

---

### Phase 5: Deprecation & Lockdown

**Duration:** Ongoing
**Code Changes:** Guards, locks, warnings
**Risk:** Low (controlled sunset)

**Actions:**

**Step 5.1: Deprecate Generic Endpoint**
```python
@router.get(
    "",
    deprecated=True,
    summary="[DEPRECATED] List things - Use topic-scoped endpoints",
)
```

**Step 5.2: Add CI Guard**
```python
# scripts/preflight/check_domain_deprecation.py
def check_no_generic_binding():
    """Ensure no panel binds to deprecated generic endpoint."""
    for intent in load_intents():
        if intent.endpoint == "/api/v1/things":
            raise ValidationError(f"Panel {intent.panel_id} binds to deprecated endpoint")
```

**Step 5.3: Add Runtime Warning**
```python
logger.warning(
    "DEPRECATED ENDPOINT ACCESS: /api/v1/things called directly. "
    "Migrate to topic-scoped endpoints."
)
```

**Step 5.4: Lock Capability Registry**
```yaml
# REGISTRY_LOCKS.yaml
locked_endpoints:
  - endpoint: /api/v1/things
    locked_on: "YYYY-MM-DD"
    reason: "Generic endpoint deprecated"
    replacement_endpoints:
      - /api/v1/things/active
      - /api/v1/things/resolved
```

**Step 5.5: Formal Closure**
- Update migration plan to LOCKED
- Add Phase 5 evidence
- Update changelog

**Exit Criteria:**
- [ ] Generic endpoint marked deprecated in OpenAPI
- [ ] CI blocks new bindings to generic endpoint
- [ ] Runtime warning logs all access
- [ ] Registry locked
- [ ] Migration plan marked LOCKED

---

## Properties of a Successful Migration

A domain migration is complete when it has all four properties:

| Property | Meaning | Verification |
|----------|---------|--------------|
| **Semantic correctness** | Topics enforced at boundaries | Callers cannot request wrong scope |
| **Control-plane truthfulness** | Registry matches reality | All capabilities have N/N invariants |
| **Mechanical enforcement** | CI prevents regression | Guards block generic bindings |
| **Institutional memory** | Pattern documented | Migration plan locked, playbook updated |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Correct Approach |
|--------------|--------------|------------------|
| "Temporary" generic bindings | Become permanent | Only topic-scoped from start |
| Skipping shadow validation | Hides data discrepancies | Always validate before rebinding |
| Editing old capabilities first | Creates orphaned bindings | Create new, then deprecate old |
| Treating CI guards as optional | Regressions sneak back | Guards are mandatory |
| Frontend aggregation | Non-deterministic, expensive | Backend analytics endpoints |
| "Simplifying" registry locks later | Removes safety | Locks are permanent |

---

## Post-Migration Checklist

After completing all five phases:

- [ ] Migration plan status = LOCKED
- [ ] Phase 5 evidence documented
- [ ] CI guard in place and passing
- [ ] Registry locks active
- [ ] README updated with domain status
- [ ] Deprecated capabilities listed
- [ ] No frontend code calls generic endpoint

---

## Reference Implementations

| Domain | Migration Date | Documentation |
|--------|---------------|---------------|
| Incidents | 2026-01-18 | `docs/architecture/incidents/INCIDENTS_DOMAIN_MIGRATION_PLAN.md` |

---

## Template Files

### CI Guard Template
```python
#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Enforce deprecation of generic /{domain} endpoint

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
FRONTEND_SRC = REPO_ROOT / "website" / "app-shell" / "src"
CAPABILITY_REGISTRY = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"

DEPRECATED_PATTERNS = [
    (r'fetch{Domain}s\s*\(', 'fetch{Domain}s() call'),
    (r'[\"\\']\\/api\\/v1\\/{domain}[\"\\']', 'Direct /api/v1/{domain} reference'),
]

ALLOWED_PATTERNS = [
    r'/api/v1/{domain}/active',
    r'/api/v1/{domain}/resolved',
    r'/api/v1/{domain}/historical',
    # Add other valid topic-scoped patterns
]

# ... implementation follows check_incidents_deprecation.py pattern
```

### Registry Lock Template
```yaml
# REGISTRY_LOCKS.yaml
locked_endpoints:
  - endpoint: /api/v1/{domain}
    locked_on: "YYYY-MM-DD"
    reason: "Generic {domain} endpoint deprecated in favor of topic-scoped endpoints"
    migration_plan: "docs/architecture/{domain}/{DOMAIN}_MIGRATION_PLAN.md"
    replacement_endpoints:
      - /api/v1/{domain}/active
      - /api/v1/{domain}/resolved
      - /api/v1/{domain}/historical
    deprecated_capabilities:
      - {domain}.list
      - {domain}.generic_list
```

---

## Maintenance

This playbook should be updated when:
- A new domain migration is completed (add to reference implementations)
- A new anti-pattern is discovered
- Template files need enhancement

**Owner:** Architecture team
**Last Updated:** 2026-01-18
