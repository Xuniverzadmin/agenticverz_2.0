# L2.1 Governance Assertions (Table-Level)

**Version:** 1.0.0
**Status:** ACTIVE (FROZEN)
**Created:** 2026-01-07

---

## Purpose

This document defines **table-level governance assertions** that must hold for all L2.1 data.

These assertions are enforced via:
- Database constraints (schema level)
- Application validation (runtime level)
- CI checks (deployment level)

**Claude must FAIL if any assertion cannot be verified.**

---

## Assertion Categories

| Category | Scope | Enforcement |
|----------|-------|-------------|
| Authority | All rows | DB constraint + app validation |
| Execution | All rows | App validation |
| Learning | All rows | App validation |
| Scope | All rows | DB constraint |
| Projection | O3+ rows | App validation |
| Immutability | O5 rows | DB trigger |

---

## 1. Authority Assertions

### A1: No Row Has Authority

**Assertion:**
```sql
SELECT COUNT(*) FROM l2_1_epistemic_surface
WHERE authority != 'none';
-- Must return 0
```

**Enforcement:**
```sql
-- Schema constraint
CHECK (authority = 'none')
```

**Claude Check:**
```
ASSERTION A1: No row has authority ≠ NONE
Status: PASS | FAIL
Count of violations: {n}
```

### A2: Facilitation is Non-Authoritative

**Assertion:**
```sql
SELECT COUNT(*) FROM l2_1_epistemic_surface
WHERE (facilitation->'signal_metadata'->>'authoritative')::boolean = true;
-- Must return 0
```

**Enforcement:**
```sql
-- Schema constraint
CHECK (facilitation->'signal_metadata'->>'authoritative' = 'false')
```

**Claude Check:**
```
ASSERTION A2: No facilitation signal is authoritative
Status: PASS | FAIL
Count of violations: {n}
```

---

## 2. Execution Assertions

### E1: No Row Implies Execution

**Assertion:**
Every `ui_intent.affordances` must NOT include execution-capable actions.

**Forbidden Actions:**
- `create`
- `update`
- `delete`
- `approve`
- `execute`
- `trigger`

**Validation Query:**
```sql
SELECT surface_id FROM l2_1_epistemic_surface
WHERE ui_intent->'action_intent' IS NOT NULL
  AND ui_intent->'action_intent'->>'available_actions' LIKE ANY (
    ARRAY['%create%', '%update%', '%delete%', '%approve%', '%execute%', '%trigger%']
  );
-- Must return 0 rows
```

**Claude Check:**
```
ASSERTION E1: No row implies execution
Status: PASS | FAIL
Violating surfaces: {list}
```

---

## 3. Learning Assertions

### L1: No Mutable State

**Assertion:**
All surfaces are read-only projections. No row may store or imply mutable learning state.

**Validation:**
```sql
SELECT COUNT(*) FROM l2_1_epistemic_surface
WHERE (projection->>'enrichment_allowed')::boolean = true;
-- Must return 0
```

**Claude Check:**
```
ASSERTION L1: No mutable/learning state
Status: PASS | FAIL
```

---

## 4. Scope Assertions

### S1: Tenant Isolation

**Assertion:**
```sql
SELECT COUNT(*) FROM l2_1_epistemic_surface
WHERE tenant_isolation = false;
-- Must return 0
```

**Enforcement:**
```sql
-- Schema constraint
CHECK (tenant_isolation = true)
```

**Claude Check:**
```
ASSERTION S1: All rows have tenant_isolation = true
Status: PASS | FAIL
```

### S2: No Cross-Tenant Aggregation

**Assertion:**
```sql
SELECT COUNT(*) FROM l2_1_epistemic_surface
WHERE (scope_constraints->>'cross_tenant_aggregation')::boolean = true;
-- Must return 0
```

**Claude Check:**
```
ASSERTION S2: No cross-tenant aggregation
Status: PASS | FAIL
```

---

## 5. Projection Assertions

### P1: All O3+ Rows Reference Interpreter Output

**Assertion:**
For orders O3, O4, O5, the projection must have valid `ir_hash` and `fact_snapshot_id`.

**Validation:**
```sql
SELECT surface_id FROM l2_1_epistemic_surface
WHERE 'O3' = ANY(enabled_orders)
   OR 'O4' = ANY(enabled_orders)
   OR 'O5' = ANY(enabled_orders)
AND (
    projection->>'ir_hash' IS NULL
    OR projection->>'fact_snapshot_id' IS NULL
);
-- Must return 0 rows for active surfaces
```

**Claude Check:**
```
ASSERTION P1: All O3+ rows reference interpreter output
Status: PASS | FAIL
Surfaces missing projection: {list}
```

---

## 6. Immutability Assertions

### I1: All O5 Rows Are Immutable Proof Only

**Assertion:**
O5 (Proof) rows must:
- Have `is_terminal = true` in order_config
- Have `immutable = true` in order_config
- Not allow any modification after creation

**Validation:**
```sql
SELECT surface_id FROM l2_1_epistemic_surface
WHERE 'O5' = ANY(enabled_orders)
AND (
    (order_config->'O5'->>'terminal')::boolean != true
    OR (order_config->'O5'->>'immutable')::boolean != true
);
-- Must return 0 rows
```

**Enforcement (Trigger):**
```sql
CREATE OR REPLACE FUNCTION prevent_o5_modification()
RETURNS TRIGGER AS $$
BEGIN
    IF 'O5' = ANY(OLD.enabled_orders) THEN
        -- Only allow status changes, not content
        IF NEW.order_config != OLD.order_config THEN
            RAISE EXCEPTION 'O5 surfaces are immutable';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Claude Check:**
```
ASSERTION I1: All O5 rows are immutable proof only
Status: PASS | FAIL
Violating surfaces: {list}
```

---

## 7. Domain Assertions

### D1: All Domains Match L1 Constitution

**Assertion:**
```sql
SELECT domain_id FROM l2_1_epistemic_surface
WHERE domain_id NOT IN (
    SELECT domain_id FROM l2_1_domain_registry
    WHERE is_frozen = true
);
-- Must return 0 rows
```

**Claude Check:**
```
ASSERTION D1: All domains match L1 Constitution
Status: PASS | FAIL
Invalid domains: {list}
```

---

## 8. Order Assertions

### O1: All Orders Are Valid

**Assertion:**
```sql
SELECT surface_id, unnest(enabled_orders) as ord FROM l2_1_epistemic_surface
WHERE unnest(enabled_orders) NOT IN ('O1', 'O2', 'O3', 'O4', 'O5');
-- Must return 0 rows
```

**Claude Check:**
```
ASSERTION O1: All orders are valid (O1-O5 only)
Status: PASS | FAIL
```

---

## Full Validation Script

```sql
-- L2.1 GOVERNANCE VALIDATION SCRIPT
-- Run before any deployment or CI check

DO $$
DECLARE
    violation_count INTEGER;
    assertion_failed BOOLEAN := false;
BEGIN
    -- A1: No authority
    SELECT COUNT(*) INTO violation_count
    FROM l2_1_epistemic_surface WHERE authority != 'none';
    IF violation_count > 0 THEN
        RAISE NOTICE 'ASSERTION A1 FAILED: % rows with authority', violation_count;
        assertion_failed := true;
    END IF;

    -- A2: Non-authoritative facilitation
    SELECT COUNT(*) INTO violation_count
    FROM l2_1_epistemic_surface
    WHERE (facilitation->'signal_metadata'->>'authoritative')::boolean = true;
    IF violation_count > 0 THEN
        RAISE NOTICE 'ASSERTION A2 FAILED: % rows with authoritative signals', violation_count;
        assertion_failed := true;
    END IF;

    -- S1: Tenant isolation
    SELECT COUNT(*) INTO violation_count
    FROM l2_1_epistemic_surface WHERE tenant_isolation = false;
    IF violation_count > 0 THEN
        RAISE NOTICE 'ASSERTION S1 FAILED: % rows without tenant isolation', violation_count;
        assertion_failed := true;
    END IF;

    -- S2: No cross-tenant aggregation
    SELECT COUNT(*) INTO violation_count
    FROM l2_1_epistemic_surface
    WHERE (scope_constraints->>'cross_tenant_aggregation')::boolean = true;
    IF violation_count > 0 THEN
        RAISE NOTICE 'ASSERTION S2 FAILED: % rows with cross-tenant aggregation', violation_count;
        assertion_failed := true;
    END IF;

    -- L1: No enrichment
    SELECT COUNT(*) INTO violation_count
    FROM l2_1_epistemic_surface
    WHERE (projection->>'enrichment_allowed')::boolean = true;
    IF violation_count > 0 THEN
        RAISE NOTICE 'ASSERTION L1 FAILED: % rows with enrichment allowed', violation_count;
        assertion_failed := true;
    END IF;

    IF assertion_failed THEN
        RAISE EXCEPTION 'L2.1 GOVERNANCE VALIDATION FAILED';
    ELSE
        RAISE NOTICE 'L2.1 GOVERNANCE VALIDATION PASSED';
    END IF;
END $$;
```

---

## Claude Stop Conditions

Claude must **STOP and ASK** if:

| Condition | Response |
|-----------|----------|
| Any assertion fails | `STATUS: BLOCKED - Governance assertion failed` |
| Domain not in L1 Constitution | `STATUS: BLOCKED - Invalid domain` |
| Topic cannot map to system boundary | `STATUS: BLOCKED - Unmappable topic` |
| Order implies action or enforcement | `STATUS: BLOCKED - Authority violation` |
| Data violates replay invariants | `STATUS: BLOCKED - Replay invariant violation` |

**No silent assumptions allowed.**

---

## References

- `l2_1_epistemic_surface.schema.sql` — Table constraints
- `docs/layers/L2_1/L2_1_GOVERNANCE_ASSERTIONS.md` — High-level assertions
- `SURFACE_ID_SPECIFICATION.md` — Trace key format
