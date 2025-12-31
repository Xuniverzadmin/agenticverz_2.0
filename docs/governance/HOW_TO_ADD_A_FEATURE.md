# How to Add a Feature Without Breaking Governance

**(Mandatory Operating Guide)**

**Version:** 2.0
**Date:** 2025-12-31
**Status:** BLOCKING
**Enforcement:** BLCA + Session Playbook

---

## Purpose

This guide defines the **only allowed way** to introduce new functionality into the system **without violating governance, authority boundaries, or BLCA guarantees**.

If you follow this guide, the system remains structurally truthful.
If you deviate, BLCA will (and must) block you.

---

## Non-Negotiable Principle (Read First)

> **Features do not start in code.**
> **Features start as intent and must earn execution.**

Any feature that directly executes code without passing through **L3 → L4 → L5** is invalid, even if it "works."

---

## Step 0 — Classify the Change (Before Touching Code)

You must classify the feature **before implementation**.

### Ask exactly one question:

**Does this feature create, modify, or commit authoritative state?**

| Answer | Classification | You Must Do |
|--------|----------------|-------------|
| No | Non-transactional | UI / read-only work allowed |
| Yes | Transactional | Follow the full pipeline below |

If you misclassify, BLCA will catch it later and you will redo the work.

---

## Step 1 — Declare the Feature Intent

Create a **Feature Intent Declaration** (can be lightweight, but explicit):

```yaml
feature_intent:
  name: <feature name>
  actor: human | system | scheduler
  intent: <what authoritative change is requested>
  scope: tenant | user | system | global
  expected_effects:
    - <authoritative state change>
    - <observable effect>
```

**Prohibitions:**
- "Refactor", "cleanup", "helper" are invalid intents
- Multiple intents in one declaration

If you cannot write this cleanly, the feature is not ready.

---

## Step 2 — L2: API Intent (Entry Only)

### What L2 Is Allowed to Do

- Accept requests
- Validate shape (not meaning)
- Authenticate identity
- Forward intent

### What L2 Is NOT Allowed to Do

- Decide policy
- Call workers
- Enforce thresholds
- Perform side effects

### Required Action

If the feature is transactional:

- Add or extend an **L2 endpoint**
- That endpoint **must call an L3 adapter**
- No imports from L4 or L5 are allowed

If you feel tempted to import L5 here → **stop**.

### L2 Compliance Declaration

```yaml
L2:
  endpoint_added_or_modified: true | false
  performs_decision_logic: false   # MUST be false
  imports_L4_or_L5: false          # MUST be false
  delegates_to_L3: true
```

---

## Step 3 — L3: Adapter (Translation Only)

### Purpose of L3

L3 exists to answer one question:

> "How do I translate this request into domain language?"

### L3 Rules

- May map request → domain inputs
- May normalize, rename, validate formats
- May not decide outcomes
- May not enforce policy
- May not touch persistence or workers

### Required Artifact

Create or extend an **L3 adapter**:

```
backend/app/adapters/<feature>_adapter.py
```

This adapter must call **exactly one L4 command**.

If L3 logic feels "smart" → you're doing it wrong.

### L3 Compliance Declaration

```yaml
L3:
  adapter_created_or_extended: true | false
  contains_policy_or_thresholds: false   # MUST be false
  performs_side_effects: false           # MUST be false
  calls_single_L4_command: true
```

---

## Step 4 — L4: Domain Authority (Decision Lives Here)

### This Is the Most Important Step

If the feature:

- Enforces rules
- Decides allow/deny
- Selects strategies
- Computes thresholds
- Chooses actions

**All of that logic lives in L4.**

### L4 Rules

- Pure logic only
- Deterministic
- No DB access (except via L6 models)
- May delegate to L5 for execution
- No platform imports except L6

### Required Artifact

Create or extend an **L4 command or engine**:

```
backend/app/commands/<feature>_command.py
```

This module must:

- Accept domain facts (not HTTP context)
- Return a decision object
- Contain **all** authority

If authority is split across files → governance violation.

### L4 Compliance Declaration

```yaml
L4:
  domain_command_or_engine: <file_name>
  contains_all_decisions: true
  imports_only_L5_L6: true
  returns_domain_result: true
```

---

## Step 5 — L5: Execution (Effects Only)

### What L5 Is For

- DB writes
- External API calls
- File I/O
- Scheduling
- Metrics emission

### Critical Rule

L5 **must not decide anything**.

It executes **only what L4 has already decided**.

### Pattern

```python
decision = L4.decide(inputs)
execute(decision)
```

If L5 recomputes or "double-checks" authority → violation.

### L5 Compliance Declaration

```yaml
L5:
  executes_only_L4_decisions: true
  recomputes_authority: false   # MUST be false
  side_effects_present: true | false
```

---

## Step 6 — BLCA Check (Mandatory)

Before the feature is considered done:

```bash
python3 scripts/ops/layer_validator.py --backend --ci
```

### BLCA Compliance Declaration

```yaml
BLCA:
  run_completed: true
  status: CLEAN | BLOCKED
  new_violations: 0
```

### Hard Rule

- `status != CLEAN` → WORK HALTS
- Violations may **not** be documented away
- Fixes required before proceeding

If BLCA flips:

- You stop
- You fix
- You do not document it away

---

## Step 7 — Governance Recording

If the feature introduces:

- New authority
- New command
- New transaction type
- New external effect

You must:

- Update the relevant governance PIN
- Ensure the feature appears in architecture artifacts

### Governance Declaration

```yaml
governance:
  pin_created_or_updated: true | false
  architecture_impact_acknowledged: true
```

Silence is not governance.

---

## Step 8 — Final Attestation (MANDATORY)

Before declaring the feature complete, attest:

```yaml
attestation:
  no_layer_bypass: true
  no_dual_role_modules: true
  no_implicit_authority: true
  BLCA_clean: true
  ready_for_merge: true
```

If **any value is false**, the session is **NOT COMPLETE**.

---

## Common Failure Modes (Do Not Rationalize These)

| Anti-Pattern | Why It's Forbidden |
|--------------|-------------------|
| "It's just a helper" | Helpers hide authority |
| "Temporary direct call" | Temporary bypasses become permanent |
| "We'll refactor later" | Governance debt compounds |
| "L3 can handle this" | Translation ≠ decision |
| "L5 needs context" | Context belongs in L4 |
| "It's faster without the adapter" | Speed ≠ correctness |
| "BLCA won't catch this" | It will |

---

## If You're Unsure — Stop Here

If at any step you ask:

- "Where should this logic go?"
- "Is this overkill?"
- "Can I just…?"

**Stop. Do not code.**

The correct move is to:

1. Surface the uncertainty
2. Let BLCA / governance decide
3. Then proceed

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│              FEATURE ADDITION PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 0: Classify (transactional or not)                    │
│  Step 1: Declare intent                                     │
│  Step 2: L2 endpoint (entry only, delegates to L3)          │
│  Step 3: L3 adapter (translation only, calls L4)            │
│  Step 4: L4 command (ALL decisions here)                    │
│  Step 5: L5 execution (effects only, no decisions)          │
│  Step 6: BLCA check (must be CLEAN)                         │
│  Step 7: Governance recording                               │
│  Step 8: Final attestation                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                     LAYER RULES                             │
│                                                             │
│  L2 → L3 (only)     No L4/L5 imports                        │
│  L3 → L4 (only)     Translation, no decisions               │
│  L4 → L5, L6        All decisions, may delegate             │
│  L5 → L6 (only)     Execute, never decide                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                     BLOCKING RULES                          │
│                                                             │
│  Missing classification → BLOCKED                           │
│  L2 importing L5 → BLOCKED                                  │
│  L3 making decisions → BLOCKED                              │
│  L5 recomputing authority → BLOCKED                         │
│  BLCA not CLEAN → BLOCKED                                   │
│  Deferred violations → BLOCKED                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## File Templates

### L2 Route Template

```python
# Layer: L2 — Product APIs
# Product: {product-name}
# Role: HTTP endpoint for {feature}
# Allowed Imports: L3, L6
# Forbidden Imports: L4, L5

from fastapi import APIRouter, Depends
from app.auth.rbac import require_role

router = APIRouter(prefix="/{feature}", tags=["{feature}"])

def _get_adapter():
    from app.adapters.{feature}_adapter import get_{feature}_adapter
    return get_{feature}_adapter()

@router.post("/action")
async def action(request: Request, tenant_id: str = Depends(get_tenant)):
    adapter = _get_adapter()
    result = await adapter.execute(tenant_id=tenant_id, ...)
    return result
```

### L3 Adapter Template

```python
# Layer: L3 — Boundary Adapter
# Product: {product-name}
# Role: Translate API requests to domain commands
# Allowed Imports: L4, L6
# Forbidden Imports: L2, L5

from app.commands.{feature}_command import execute_{feature}, {Feature}Result

class {Feature}Adapter:
    async def execute(self, tenant_id: str, ...) -> {Feature}Result:
        # Translation only - no decisions
        return await execute_{feature}(tenant_id=tenant_id, ...)

def get_{feature}_adapter() -> {Feature}Adapter:
    return {Feature}Adapter()
```

### L4 Command Template

```python
# Layer: L4 — Domain Engine (Command Facade)
# Product: {product-name}
# Role: {feature} domain decisions
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3

from dataclasses import dataclass
from typing import Optional

@dataclass
class {Feature}Result:
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

async def execute_{feature}(tenant_id: str, ...) -> {Feature}Result:
    # ALL DECISIONS HAPPEN HERE

    # 1. Validate domain preconditions
    if not valid:
        return {Feature}Result(success=False, error="reason")

    # 2. Make domain decision
    decision = compute_decision(...)

    # 3. Delegate to L5 if execution needed
    from app.worker.{feature}_worker import execute
    execution_result = await execute(decision)

    # 4. Return domain result
    return {Feature}Result(success=True, data=execution_result)
```

---

## Final Rule (Memorize This)

> **If a feature cannot be expressed as L2 → L3 → L4 → L5, it is not a valid feature yet.**

---

## Reference

- PIN-259: Phase G Steady-State Governance
- GOVERNANCE_CHECKLIST.md
- SESSION_PLAYBOOK.yaml Section 30
