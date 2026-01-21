# PIN-453: Policies Domain Topic Rename: Thresholds to Controls

**Status:** ✅ COMPLETE
**Created:** 2026-01-20
**Category:** Architecture / UI Projection

---

## Summary

Renamed topic from 'Thresholds' to 'Controls' in Policies → Limits subdomain across all architecture documents, UI projection files, intent YAMLs, capability registries, SDSR scenarios, and frontend components.

---

## Details

## Summary

Comprehensive rename of the topic name from 'Thresholds' to 'Controls' in the Policies domain, Limits subdomain.

## Scope

This rename affects:

### Panel IDs
- `POL-LIM-THR-O1` → `POL-LIM-CTR-O1`
- `POL-LIM-THR-O2` → `POL-LIM-CTR-O2`
- `POL-LIM-THR-O3` → `POL-LIM-CTR-O3`
- `POL-LIM-THR-O4` → `POL-LIM-CTR-O4`
- `POL-LIM-THR-O5` → `POL-LIM-CTR-O5`

### Topic Name
- `THRESHOLDS` → `CONTROLS`
- `thresholds` → `controls`

## Files Updated

### Architecture Documents
- `docs/architecture/POLICIES_DOMAIN_ARCHITECTURE.md`
- `docs/architecture/CROSS_DOMAIN_DATA_ARCHITECTURE.md`
- `docs/architecture/FRONTEND_PROJECTION_ARCHITECTURE.md`
- `docs/architecture/BACKEND_DOMAIN_INVENTORY.md`
- `docs/architecture/policies/POLICY_DOMAIN_V2_DESIGN.md`
- `docs/architecture/limits/THRESHOLD_PARAMS_CONTRACT.md`
- `docs/architecture/PANEL_CREATION_PLAN.md`
- `docs/architecture/PANEL_EXECUTION_PLAN.md`
- `docs/architecture/FRONTEND_L1_BUILD_PLAN.md`

### UI Projection Files
- `design/l2_1/ui_plan.yaml`
- `design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml`
- `website/app-shell/src/contracts/ui_plan_scaffolding.ts`

### Intent YAML Files (via sync_from_intent_ledger.py)
- `design/l2_1/INTENT_LEDGER.md` (source)
- `design/l2_1/intents/AURORA_L2_INTENT_POL-LIM-CTR-O*.yaml` (regenerated)

### Capability Registry Files
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policy.controls.yaml` (renamed from policy.thresholds)
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policies.quota_runs.yaml`
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policies.cooldowns_list.yaml`
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policies.quota_tokens.yaml`
- `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_policies.risk_ceilings.yaml`

### SDSR Scenario Files
- `backend/scripts/sdsr/scenarios/SDSR-POL-LIM-CTR-O*.yaml` (renamed and updated)

### Frontend Components
- `website/app-shell/src/components/panels/PanelContentRegistry.tsx`
  - Renamed `ThresholdLimitsNavigation` → `ControlLimitsNavigation`
  - Changed panel ID `POL-LIM-TL-O1` → `POL-LIM-CTR-O1`

### Backend Files
- `backend/aurora_l2/tools/aurora_full_sweep.py`
- `backend/app/services/panel_invariant_registry.yaml`

## NOT Updated (Historical/Generated)

The following files contain historical observation data and were intentionally not updated:
- `backend/scripts/sdsr/observations/*.json`
- `backend/aurora_l2/tools/sweep_results.json`
- `backend/scripts/sdsr/pdg_audit/*.json`

These will reflect the new panel IDs on next regeneration.

## References

- PIN-447: Policy V2 Facade Implementation
- PIN-452: Policy Control Lever System Implementation
- CUSTOMER_CONSOLE_V2_CONSTITUTION.md: Authoritative domain structure

---

## Related PINs

- [PIN-447](PIN-447-.md)
- [PIN-452](PIN-452-.md)
