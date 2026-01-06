# PIN-283: LIFECYCLE-DERIVED-FROM-QUALIFIER Governance Rule

**Status:** 📋 ACTIVE
**Created:** 2026-01-04
**Category:** Governance / Capability Lifecycle

---

## Summary

Establishes that capability lifecycle status is derived from qualifier evaluation, not manually assigned. Enforces coherence between CAPABILITY_LIFECYCLE.yaml and QUALIFIER_EVALUATION.yaml.

---

## Details

## Overview

This PIN establishes the **LIFECYCLE-DERIVED-FROM-QUALIFIER** governance rule, which ensures that capability lifecycle status is a mechanically enforced consequence of qualifier evaluation, not a manual update.

## Problem Statement

PIN-281 L2 Promotion Governance work completed successfully, but the update to `CAPABILITY_LIFECYCLE.yaml` was procedural, not enforced. This created a governance gap where:

1. Lifecycle status could be set without qualifying evidence
2. Registry drift could occur silently
3. Manual edits could bypass governance checks

## Solution

### Rule: LIFECYCLE-DERIVED-FROM-QUALIFIER

> A capability **MUST NOT** transition to `status: COMPLETE` unless:
> `QUALIFIER_EVALUATION.yaml` → `capability.state == QUALIFIED`

No exceptions. No manual edits.

### Source of Truth Hierarchy

| Artifact | Role |
|----------|------|
| `QUALIFIER_EVALUATION.yaml` | **Authoritative verdict** |
| `CAPABILITY_LIFECYCLE.yaml` | **Derived projection** |
| CI Guards | **Enforcement** |

Lifecycle **never leads**, it only **follows**.

## Implementation

### 1. Schema Update

`CAPABILITY_LIFECYCLE.yaml` now includes:
- Governance rule header documenting derivation requirement
- Per-capability qualifier bindings (`qualifier`, `qualifier_state`)
- Schema version bumped to 1.5

### 2. CI Guard

`scripts/ci/lifecycle_qualifier_guard.py`:
- Loads both YAML files
- Cross-references each capability
- Verifies qualifier_state matches evaluation
- Blocks if any divergence detected

### 3. Bootstrap Integration

`scripts/ops/session_start.sh` now includes:
- Step 8: BLCA layer validation
- Step 9: Lifecycle-qualifier coherence check
- Session blocked if either fails

## Enforcement Points

| Point | Mechanism |
|-------|-----------|
| Session Start | `session_start.sh` step 9 |
| CI Pipeline | `lifecycle_qualifier_guard.py` |
| Qualifier Regeneration | `evaluate_qualifiers.py --generate` |

## Verification

```bash
# Run lifecycle-qualifier coherence guard
python3 scripts/ci/lifecycle_qualifier_guard.py

# Regenerate qualifier evaluation
python3 scripts/ops/evaluate_qualifiers.py --generate

# Run session start (includes both checks)
./scripts/ops/session_start.sh
```

## Current State

| Metric | Value |
|--------|-------|
| Capabilities | 17 |
| COMPLETE (lifecycle) | 16 |
| QUALIFIED (evaluation) | 16 |
| Coherence | 100% |

## Reference

- PIN-280: L2 Promotion Governance Framework
- PIN-281: Claude Task TODO
- PIN-282: PIN-281 L2 Promotion Governance Completion
- `docs/governance/CAPABILITY_LIFECYCLE.yaml`
- `docs/governance/QUALIFIER_EVALUATION.yaml`
- `docs/governance/GOVERNANCE_QUALIFIERS.yaml`

---

## Related PINs

- [PIN-280](PIN-280-.md)
- [PIN-281](PIN-281-.md)
- [PIN-282](PIN-282-.md)
