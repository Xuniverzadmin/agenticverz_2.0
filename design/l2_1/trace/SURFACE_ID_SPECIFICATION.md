# L2.1 Surface ID Specification

**Version:** 1.0.0
**Status:** FROZEN
**Created:** 2026-01-07

---

## 1. Purpose

The `surface_id` is the **primary trace key** for all L2.1 epistemic surfaces.

Every reference to an L2.1 surface — in UI, tests, replay tools, or scenarios — MUST use this identifier.

---

## 2. Format

```
{DOMAIN}.{SUBDOMAIN}.{TOPIC}
```

### Components

| Component | Format | Example |
|-----------|--------|---------|
| DOMAIN | UPPER_SNAKE_CASE | `OVERVIEW`, `ACTIVITY` |
| SUBDOMAIN | UPPER_SNAKE_CASE | `SYSTEM_HEALTH`, `EXECUTIONS` |
| TOPIC | UPPER_SNAKE_CASE | `CURRENT_STATUS`, `ACTIVE_RUNS` |

### Rules

1. All components are **UPPERCASE**
2. Underscores separate words within components
3. Dots separate components
4. No spaces, no special characters
5. Must be valid in URLs (percent-encoding not required)

---

## 3. Examples

### Overview Domain

```
OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS
OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS
```

### Activity Domain

```
ACTIVITY.EXECUTIONS.ACTIVE_RUNS
ACTIVITY.EXECUTIONS.COMPLETED_RUNS
ACTIVITY.EXECUTIONS.RUN_DETAILS
```

### Incidents Domain

```
INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS
INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS
INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS
```

### Policies Domain

```
POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES
POLICIES.ACTIVE_POLICIES.RATE_LIMITS
POLICIES.ACTIVE_POLICIES.APPROVAL_RULES
POLICIES.POLICY_AUDIT.POLICY_CHANGES
```

### Logs Domain

```
LOGS.AUDIT_LOGS.SYSTEM_AUDIT
LOGS.AUDIT_LOGS.USER_AUDIT
LOGS.EXECUTION_TRACES.TRACE_DETAILS
```

---

## 4. Usage Requirements

### 4.1 UI Components

Every UI component rendering an L2.1 surface MUST:

```typescript
// Required: surface_id in component props
interface SurfaceProps {
  surfaceId: string;  // e.g., "OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS"
}

// Required: data-surface-id attribute on root element
<div data-surface-id={surfaceId}>
  {/* surface content */}
</div>
```

### 4.2 Tests

Every test targeting an L2.1 surface MUST:

```python
# Required: surface_id in test fixture
@pytest.fixture
def surface_fixture():
    return {
        "surface_id": "OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS",
        # ... test data
    }

# Required: surface_id in test name or marker
@pytest.mark.surface("OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS")
def test_current_status_rendering():
    pass
```

### 4.3 Replay Tools

Every replay request MUST include:

```json
{
  "surface_id": "ACTIVITY.EXECUTIONS.RUN_DETAILS",
  "ir_hash": "abc123...",
  "fact_snapshot_id": "uuid-here"
}
```

### 4.4 API Responses

Every API response for an L2.1 surface MUST include:

```json
{
  "meta": {
    "surface_id": "INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS",
    "schema_version": "1.0.0",
    "authority": "NONE"
  },
  "data": { }
}
```

---

## 5. Validation

### 5.1 Regex Pattern

```regex
^[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*$
```

### 5.2 Validation Function

```python
import re

SURFACE_ID_PATTERN = re.compile(
    r'^[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*$'
)

def validate_surface_id(surface_id: str) -> bool:
    """Validate surface_id format."""
    if not SURFACE_ID_PATTERN.match(surface_id):
        return False

    parts = surface_id.split('.')
    if len(parts) != 3:
        return False

    domain, subdomain, topic = parts

    # Check domain exists
    valid_domains = {'OVERVIEW', 'ACTIVITY', 'INCIDENTS', 'POLICIES', 'LOGS'}
    if domain not in valid_domains:
        return False

    return True
```

---

## 6. Database Constraint

```sql
-- Unique constraint on surface_id
ALTER TABLE l2_1_epistemic_surface
ADD CONSTRAINT chk_surface_id_format
CHECK (surface_id ~ '^[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*$');
```

---

## 7. Traceability Chain

```
surface_id (L2.1)
    |
    +---> UI Component (data-surface-id)
    |
    +---> Test Fixture (surface_id)
    |
    +---> Replay Tool (surface_id in request)
    |
    +---> API Response (meta.surface_id)
    |
    +---> Usage Map (L2_1_USAGE_MAP.md)
```

Every usage MUST be recorded in `L2_1_USAGE_MAP.md`.

---

## 8. References

- `l2_1_epistemic_surface.surface_id` (database column)
- `L2_1_USAGE_MAP.md` (usage tracking)
- `L2_1_ASSERTIONS.md` (governance)
