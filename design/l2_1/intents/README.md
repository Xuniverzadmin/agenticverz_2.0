# AURORA_L2 Intent Specs Directory

**Status:** SCAFFOLD (empty placeholder)

## Purpose

This directory will contain individual YAML intent spec files.

## File Naming Convention

```
{panel_id}.yaml
```

Examples:
- `POL-RU-O1.yaml` - Policy Rules Summary panel
- `POL-RU-O2.yaml` - Policy Rules List panel
- `INC-AI-OI-O2.yaml` - Open Incidents List panel

## Intent Spec Format (to be defined)

```yaml
# Example structure (pending schema definition)
panel_id: POL-RU-O2
version: "1.0.0"
metadata:
  domain: POLICIES
  subdomain: RULES
  topic: ACTIVE_RULES
  order: O2
  migrated_from: CSV
  migration_status: UNREVIEWED

display:
  name: "Policy Rules List"
  description: "List of active policy rules"
  expansion_mode: INLINE

data:
  source_table: policy_rules
  api_endpoint: /api/v1/policy-rules
  filters: []

controls:
  - type: FILTER
  - type: SORT
  - type: SELECT_SINGLE
  - type: NAVIGATE

visibility:
  default: true
  requires_permission: policies.rules.read
```

## Migration Notes

All 55 CSV rows from `L2_1_UI_INTENT_SUPERTABLE.csv` will be migrated here.
Each row becomes one YAML file with `migration_status: UNREVIEWED`.
