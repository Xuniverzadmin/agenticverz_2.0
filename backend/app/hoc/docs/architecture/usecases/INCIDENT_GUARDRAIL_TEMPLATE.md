# Incident Guardrail Template

**Created:** 2026-02-16
**Purpose:** Every production incident MUST produce at least one guardrail artifact. This template defines the mandatory fields.

---

## Required Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| incident_id | string | Unique incident identifier (e.g., INC-001) | YES |
| incident_date | string (ISO-8601) | When the incident occurred | YES |
| severity | string | CRITICAL / HIGH / MEDIUM / LOW | YES |
| root_cause | string | Brief root cause description | YES |
| domain_affected | string | HOC domain (e.g., policies, incidents, integrations) | YES |
| invariant_id | string | New or existing invariant that prevents recurrence | YES |
| test_file | string | Path to the test that validates the guardrail | YES |
| owner | string | Who owns the guardrail (domain team / system) | YES |
| status | string | ACTIVE / SUPERSEDED / RETIRED | YES |
| created_by | string | Who created this guardrail entry | YES |

## Template

```yaml
- incident_id: "INC-XXX"
  incident_date: "2026-XX-XX"
  severity: "HIGH"
  root_cause: "Description of what went wrong"
  domain_affected: "domain_name"
  invariant_id: "INV-XXX-NNN"
  test_file: "tests/governance/t5/test_xxx.py::test_yyy"
  owner: "domain_team"
  status: "ACTIVE"
  created_by: "Claude"
```

## Guardrail Registry

All active guardrails are tracked in `INCIDENT_GUARDRAIL_REGISTRY.yaml` (co-located with this template).

### Current Guardrails

| Incident | Invariant | Test | Status |
|----------|-----------|------|--------|
| INC-BASELINE-001 | INV-TENANT-001 | test_business_invariants_runtime.py::test_tenant_create_invariant_passes | ACTIVE |
| INC-BASELINE-002 | INV-INC-001 | test_business_invariants_runtime.py::test_incident_resolve_fails_when_already_resolved | ACTIVE |
| INC-BASELINE-003 | INV-CTRL-001 | test_business_invariants_runtime.py::test_threshold_invariant_fails_with_negative | ACTIVE |

## Validation Rule

The `check_incident_guardrail_linkage.py` script validates:
1. Every incident entry has all required fields
2. Every invariant_id maps to a real invariant in `business_invariants.py`
3. Every test_file path exists and the test function exists
4. No orphan incidents (incident without guardrail)
