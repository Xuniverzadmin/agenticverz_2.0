# HOC_CAPABILITY_LINKAGE_WAVE1_REMEDIATION_2026-02-20

## Scope
Wave 1 remediation for HOC-only capability linkage blockers (`MISSING_CAPABILITY_ID`).

## Baseline
- Source blocker set from:
  - `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`
- Initial HOC missing-ID count: **5**

## Files Remediated
1. `backend/app/hoc/cus/integrations/cus_cli.py` -> `# capability_id: CAP-018`
2. `backend/app/hoc/int/agent/drivers/json_transform_stub.py` -> `# capability_id: CAP-016`
3. `backend/app/hoc/int/agent/drivers/registry_v2.py` -> `# capability_id: CAP-016`
4. `backend/app/hoc/int/agent/engines/http_call_stub.py` -> `# capability_id: CAP-016`
5. `backend/app/hoc/int/agent/engines/llm_invoke_stub.py` -> `# capability_id: CAP-016`

## Registry Evidence Sync
Updated capability evidence lists to remove `MISSING_EVIDENCE` warnings:
- `docs/capabilities/CAPABILITY_REGISTRY.yaml`
  - `capabilities.skill_system.evidence.engine` includes 4 HOC stub/registry files
  - `capabilities.integration_platform.evidence.engine` includes `cus_cli.py`

## Verification
```bash
python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
  backend/app/hoc/cus/integrations/cus_cli.py \
  backend/app/hoc/int/agent/drivers/json_transform_stub.py \
  backend/app/hoc/int/agent/drivers/registry_v2.py \
  backend/app/hoc/int/agent/engines/http_call_stub.py \
  backend/app/hoc/int/agent/engines/llm_invoke_stub.py
```

Result:
- `✅ All checks passed`

## Outcome
- HOC `MISSING_CAPABILITY_ID` blockers: **5 -> 0**
- Remaining open HOC blocker workstreams (unchanged in this wave):
  - Layer segregation violations
  - Relative-import hygiene
