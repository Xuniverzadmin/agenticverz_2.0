# Infra Obligation Schema

**Status:** ACTIVE
**Created:** 2026-01-02
**Purpose:** Define the structure for infrastructure obligations that MUST be fulfilled

---

## What is an Infra Obligation?

> **An Infra Obligation is a test-proven promise that MUST eventually be implemented in a specific layer, schema, and module.**

Once an obligation exists, it cannot be ignored, skipped, or silently tolerated.

---

## Obligation Schema (YAML)

```yaml
infra_obligation:
  id: string                    # Unique identifier (e.g., PB-S1, M10, M26)
  title: string                 # Human-readable name
  layer: string                 # L1-L8 layer classification
  schema: string                # Database schema name (if applicable)

  requires:                     # List of required infrastructure
    - type: table | trigger | function | constraint | index | view
      name: string              # Object name
      schema: string            # Schema location (optional, defaults to public)

  semantic_purpose: string      # Why this infra exists (business reason)

  status: UNFULFILLED | PARTIAL | PROMOTED | DEPRECATED

  migration_path: string        # Path to migrations folder (e.g., migrations/obligations/PB-S1/)

  test_files:                   # Tests that validate this obligation
    - path: string
      count: number             # Number of tests

  promotion_criteria:
    - all_objects_exist: boolean
    - all_tests_pass: boolean
    - no_schema_drift: boolean

  created: date
  promoted_at: date | null

  related_pins:                 # Reference PINs
    - string
```

---

## Status Definitions

| Status | Meaning | CI Behavior |
|--------|---------|-------------|
| **UNFULFILLED** | Obligation declared, infra not yet built | Tests skip with WARN |
| **PARTIAL** | Some infra exists, not complete | Tests skip with WARN |
| **PROMOTED** | All infra exists, tests must pass | Failures are BLOCKING |
| **DEPRECATED** | Obligation no longer needed | Tests should be removed |

---

## Promotion Rules (Non-Negotiable)

An Infra Obligation is PROMOTED when **ALL** of the following are true:

1. All required objects exist in the database
2. All corresponding tests pass
3. No schema drift detected between code and DB
4. Migration files exist in the designated path

**Once PROMOTED, tests can NEVER be skipped again.**
Failures become blocking regressions.

---

## Directory Structure

```
docs/infra/
├── INFRA_OBLIGATION_SCHEMA.md     # This file
├── INFRA_OBLIGATION_REGISTRY.yaml # All obligations
└── obligations/
    ├── PB-S1.yaml
    ├── PB-S2.yaml
    ├── PB-S3.yaml
    ├── PB-S4.yaml
    ├── PB-S5.yaml
    ├── M10.yaml
    ├── M24.yaml
    └── M26.yaml

backend/migrations/obligations/
├── PB-S1/
│   ├── 001_retry_schema.sql
│   └── 002_immutability_trigger.sql
├── PB-S2/
│   └── 001_crash_recovery.sql
└── ...
```

---

## CI Integration

```yaml
# .github/workflows/infra-obligations.yml
infra_obligation_check:
  rules:
    - obligation.status == UNFULFILLED: WARN (skip tests)
    - obligation.status == PARTIAL: WARN (skip tests)
    - obligation.status == PROMOTED && tests_fail: FAIL (blocking)
    - obligation.status == PROMOTED && tests_pass: PASS
```

---

## Claude's Decision Space

After this architecture, Claude's choices collapse to:

| Situation | Allowed Action |
|-----------|----------------|
| New infra needed | Create obligation YAML first |
| Obligation UNFULFILLED | Implement migration OR defer explicitly |
| Obligation PROMOTED | Fix the test OR fix the infra (no skip allowed) |

No silent hacks. No clever workarounds.
The system guides the fix.

---

## References

- `scripts/ops/check_infra_obligations.py` - Promotion checker
- `docs/governance/INFRA_REGISTRY.md` - Infrastructure state registry
- PIN-276 - Bucket A/B Permanent Fix Design
