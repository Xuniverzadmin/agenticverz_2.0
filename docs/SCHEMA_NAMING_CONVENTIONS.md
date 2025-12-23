# Schema Naming Conventions

**Created:** 2025-12-23
**Status:** Enforced (M25 hygiene)
**Related:** PIN-140 M25 Complete

---

## Purpose

Prevent schema drift bugs like `blocked_incident_id` vs `incident_id_blocked`.

---

## Rules

### 1. Blocked Relationships

Use `blocked_*` prefix, NOT `*_blocked` suffix.

```sql
-- CORRECT
blocked_incident_id VARCHAR(64)
blocked_at TIMESTAMP

-- WRONG
incident_id_blocked VARCHAR(64)
blocked_at_timestamp TIMESTAMP
```

### 2. Source/Target Relationships

Use `source_*` and `target_*` prefixes.

```sql
-- CORRECT
source_pattern_id VARCHAR(64)
target_policy_id VARCHAR(64)

-- WRONG
pattern_id_source VARCHAR(64)
policy_id_target VARCHAR(64)
```

### 3. Original/Copy Relationships

Use `original_*` prefix for the source, no prefix for the copy.

```sql
-- CORRECT
original_incident_id VARCHAR(64)
incident_id VARCHAR(64)  -- the current/copy

-- WRONG
incident_id_original VARCHAR(64)
copy_incident_id VARCHAR(64)
```

### 4. Timestamps

Use `*_at` suffix for all timestamps.

```sql
-- CORRECT
created_at TIMESTAMP
updated_at TIMESTAMP
activated_at TIMESTAMP
prevented_at TIMESTAMP

-- WRONG
create_timestamp TIMESTAMP
update_time TIMESTAMP
activated TIMESTAMP
```

### 5. Foreign Keys

Use `*_id` suffix for all foreign keys.

```sql
-- CORRECT
policy_id VARCHAR(64)
tenant_id VARCHAR(64)
pattern_id VARCHAR(64)

-- WRONG
policy VARCHAR(64)
tenant_fk VARCHAR(64)
fk_pattern VARCHAR(64)
```

### 6. Boolean Fields

Use `is_*` or `has_*` prefix for booleans.

```sql
-- CORRECT
is_active BOOLEAN
is_simulated BOOLEAN
has_regret BOOLEAN

-- WRONG
active BOOLEAN
simulated BOOLEAN
regret_flag BOOLEAN
```

---

## Linter Enforcement

The linter at `scripts/ops/lint_schema_naming.py` checks for:

1. Mixed naming patterns (e.g., both `blocked_*` and `*_blocked`)
2. Missing `_id` suffix on foreign keys
3. Missing `_at` suffix on timestamps
4. Missing `is_` prefix on booleans

Run before migration:

```bash
python scripts/ops/lint_schema_naming.py backend/alembic/versions/
```

---

## Changelog

- 2025-12-23: Created after discovering `blocked_incident_id` vs `incident_id_blocked` bug
