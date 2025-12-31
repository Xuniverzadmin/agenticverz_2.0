# Governance Checklist — Feature Addition

**(Mandatory | Blocking | Claude-Enforced)**

**Version:** 1.0
**Date:** 2025-12-31
**Status:** BLOCKING
**Enforcement:** BLCA + Session Playbook

---

## Status

- **Applies to**: Every session that introduces or modifies behavior
- **Enforcement**: BLCA + Session Playbook
- **Bypass**: Not allowed (except emergency override with PIN + ratification)

---

## SECTION 1 — Change Classification (MUST COMPLETE FIRST)

Claude must explicitly answer:

```yaml
change_classification:
  creates_authoritative_state: true | false
  modifies_authoritative_state: true | false
  triggers_execution: true | false
  external_side_effects: true | false
```

### Blocking Rule

If **any** value is `true`, the change is **TRANSACTIONAL**
→ Full governance pipeline REQUIRED.

Claude must STOP if this section is missing or ambiguous.

---

## SECTION 2 — Feature Intent Declaration (REQUIRED)

```yaml
feature_intent:
  name: <string>
  actor: human | system | scheduler
  intent: <single sentence, no implementation detail>
  scope: user | tenant | system | global
  expected_effects:
    - <authoritative state change>
    - <observable effect>
```

### Prohibitions

- "Refactor", "cleanup", "helper" are invalid intents
- Multiple intents in one declaration

---

## SECTION 3 — Layer Compliance Checklist (MANDATORY)

Claude must confirm **each layer explicitly**.

### L2 — API Layer

```yaml
L2:
  endpoint_added_or_modified: true | false
  performs_decision_logic: false   # MUST be false
  imports_L4_or_L5: false          # MUST be false
  delegates_to_L3: true
```

### L3 — Adapter Layer

```yaml
L3:
  adapter_created_or_extended: true | false
  contains_policy_or_thresholds: false   # MUST be false
  performs_side_effects: false           # MUST be false
  calls_single_L4_command: true
```

### L4 — Domain Authority

```yaml
L4:
  domain_command_or_engine: <file_name>
  contains_all_decisions: true
  imports_only_L5_L6: true
  returns_domain_result: true
```

### L5 — Execution Layer

```yaml
L5:
  executes_only_L4_decisions: true
  recomputes_authority: false   # MUST be false
  side_effects_present: true | false
```

### Blocking Rule

If **any forbidden condition is true**, Claude must STOP and surface violation.

---

## SECTION 4 — BLCA PRE-CHECK (BLOCKING)

Claude must run BLCA **before claiming completion**.

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

---

## SECTION 5 — Violation Declaration (IF ANY)

If violations were discovered during work:

```yaml
violations:
  discovered: true | false
  count: <int>
  types:
    - authority_leak
    - layer_bypass
    - dual_role
    - implicit_side_effect
  resolution:
    applied: true | false
    deferred: false   # MUST be false
```

### Governance Rule

Deferred violations are **forbidden**.
Discovery without resolution = BLOCKED SESSION.

---

## SECTION 6 — Governance Recording (REQUIRED FOR TRANSACTIONS)

```yaml
governance:
  pin_created_or_updated: true | false
  transaction_registry_updated: true | false
  architecture_impact_acknowledged: true
```

Claude must surface links to:

- PIN
- Relevant architecture artifacts

---

## SECTION 7 — Final Attestation (MANDATORY)

Claude must conclude with:

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

## Complete Checklist Template

Copy and complete for each feature:

```yaml
# GOVERNANCE CHECKLIST - <Feature Name>
# Date: YYYY-MM-DD

# Section 1: Change Classification
change_classification:
  creates_authoritative_state:
  modifies_authoritative_state:
  triggers_execution:
  external_side_effects:

# Section 2: Feature Intent
feature_intent:
  name:
  actor:
  intent:
  scope:
  expected_effects:
    -

# Section 3: Layer Compliance
L2:
  endpoint_added_or_modified:
  performs_decision_logic: false
  imports_L4_or_L5: false
  delegates_to_L3: true

L3:
  adapter_created_or_extended:
  contains_policy_or_thresholds: false
  performs_side_effects: false
  calls_single_L4_command: true

L4:
  domain_command_or_engine:
  contains_all_decisions: true
  imports_only_L5_L6: true
  returns_domain_result: true

L5:
  executes_only_L4_decisions: true
  recomputes_authority: false
  side_effects_present:

# Section 4: BLCA
BLCA:
  run_completed:
  status:
  new_violations:

# Section 5: Violations (if any)
violations:
  discovered:
  count:
  types: []
  resolution:
    applied:
    deferred: false

# Section 6: Governance
governance:
  pin_created_or_updated:
  transaction_registry_updated:
  architecture_impact_acknowledged:

# Section 7: Attestation
attestation:
  no_layer_bypass:
  no_dual_role_modules:
  no_implicit_authority:
  BLCA_clean:
  ready_for_merge:
```

---

## Why This Works (Blunt Truth)

- This prevents **"it works" drift**
- This prevents **semantic laundering**
- This makes Claude incapable of accidental shortcuts
- This turns governance into muscle memory, not ceremony

You have now **institutionalized discipline**, not just architecture.

---

## Reference

- HOW_TO_ADD_A_FEATURE.md
- PIN-259: Phase G Steady-State Governance
- SESSION_PLAYBOOK.yaml Section 30
