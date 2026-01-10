# AURORA_L2 Capability Registry

**Status:** SCAFFOLD (empty placeholder)

## Purpose

This directory will contain the capability binding registry for AURORA_L2.

The capability registry maps:
- Intent panel_ids → Backend capabilities (APIs, features)
- Backend capabilities → Required permissions
- Permissions → RBAC requirements

## Files (to be created)

| File | Purpose |
|------|---------|
| `capability_map.yaml` | panel_id → capability_id mapping |
| `capability_definitions.yaml` | capability_id → API/feature definitions |
| `permission_requirements.yaml` | capability_id → required permissions |

## Migration Notes

The existing `capability_intelligence_all_domains.csv` will be migrated to YAML format here.
