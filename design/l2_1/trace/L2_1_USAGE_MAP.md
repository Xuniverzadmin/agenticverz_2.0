# L2.1 Usage Map

**Version:** 1.0.0
**Status:** ACTIVE (manual updates required)
**Created:** 2026-01-07

---

## Purpose

This file tracks **every usage** of L2.1 surface IDs across:
- UI components
- Tests
- Replay tools
- Scenario fixtures

**This is manual but mandatory.** Every new reference must be recorded here.

---

## Format

```yaml
surface_id:
  used_by:
    - ui:<component_path>
    - test:<test_path>
    - replay:<tool_name>
    - scenario:<scenario_id>
  status: active | pending | deprecated
  notes: <optional notes>
```

---

## OVERVIEW Domain

### OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS

```yaml
surface_id: OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS

```yaml
surface_id: OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

---

## ACTIVITY Domain

### ACTIVITY.EXECUTIONS.ACTIVE_RUNS

```yaml
surface_id: ACTIVITY.EXECUTIONS.ACTIVE_RUNS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### ACTIVITY.EXECUTIONS.COMPLETED_RUNS

```yaml
surface_id: ACTIVITY.EXECUTIONS.COMPLETED_RUNS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### ACTIVITY.EXECUTIONS.RUN_DETAILS

```yaml
surface_id: ACTIVITY.EXECUTIONS.RUN_DETAILS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

---

## INCIDENTS Domain

### INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS

```yaml
surface_id: INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS

```yaml
surface_id: INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS

```yaml
surface_id: INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

---

## POLICIES Domain

### POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES

```yaml
surface_id: POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### POLICIES.ACTIVE_POLICIES.RATE_LIMITS

```yaml
surface_id: POLICIES.ACTIVE_POLICIES.RATE_LIMITS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### POLICIES.ACTIVE_POLICIES.APPROVAL_RULES

```yaml
surface_id: POLICIES.ACTIVE_POLICIES.APPROVAL_RULES
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### POLICIES.POLICY_AUDIT.POLICY_CHANGES

```yaml
surface_id: POLICIES.POLICY_AUDIT.POLICY_CHANGES
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

---

## LOGS Domain

### LOGS.AUDIT_LOGS.SYSTEM_AUDIT

```yaml
surface_id: LOGS.AUDIT_LOGS.SYSTEM_AUDIT
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### LOGS.AUDIT_LOGS.USER_AUDIT

```yaml
surface_id: LOGS.AUDIT_LOGS.USER_AUDIT
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

### LOGS.EXECUTION_TRACES.TRACE_DETAILS

```yaml
surface_id: LOGS.EXECUTION_TRACES.TRACE_DETAILS
used_by:
  - ui: pending
  - test: pending
  - replay: pending
status: pending
notes: "Initial surface, awaiting UI implementation"
```

---

## Summary

| Domain | Surfaces | UI | Test | Replay |
|--------|----------|------|------|--------|
| OVERVIEW | 2 | 0 | 0 | 0 |
| ACTIVITY | 3 | 0 | 0 | 0 |
| INCIDENTS | 3 | 0 | 0 | 0 |
| POLICIES | 4 | 0 | 0 | 0 |
| LOGS | 3 | 0 | 0 | 0 |
| **Total** | **15** | **0** | **0** | **0** |

---

## Update Instructions

When adding a new usage:

1. Find the `surface_id` section
2. Add the usage under `used_by`:
   - UI: `ui:website/app/components/overview/CurrentStatus.tsx`
   - Test: `test:backend/tests/l2_1/test_current_status.py`
   - Replay: `replay:scripts/replay/replay_tool.py`
   - Scenario: `scenario:SC-001-overview-health`
3. Update the summary table counts
4. Commit with message: `docs: update L2_1_USAGE_MAP for {surface_id}`

---

## Orphan Detection

A surface is **orphaned** if:
- Status is `active`
- No entries under `used_by`

Orphaned surfaces should be reviewed for:
- Implementation needed
- Deprecation candidate
- Missing documentation

---

## References

- `SURFACE_ID_SPECIFICATION.md` — ID format rules
- `L2_1_ASSERTIONS.md` — Governance constraints
