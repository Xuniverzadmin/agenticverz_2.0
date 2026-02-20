# PIN-596 HOC Capability-Linkage Wave 1 Remediation

## Date
2026-02-20

## Context
After merging PR #9 and PR #10, remaining governance blockers under `backend/app/hoc/**` were:
- Layer segregation violations
- Relative-import hygiene
- Capability linkage (`MISSING_CAPABILITY_ID`)

Wave 1 targeted the smallest deterministic set: capability linkage missing-ID blockers.

## Changes
1. Added `capability_id` headers to 5 HOC files:
   - `backend/app/hoc/cus/integrations/cus_cli.py` (`CAP-018`)
   - `backend/app/hoc/int/agent/drivers/json_transform_stub.py` (`CAP-016`)
   - `backend/app/hoc/int/agent/drivers/registry_v2.py` (`CAP-016`)
   - `backend/app/hoc/int/agent/engines/http_call_stub.py` (`CAP-016`)
   - `backend/app/hoc/int/agent/engines/llm_invoke_stub.py` (`CAP-016`)
2. Updated capability evidence mapping in:
   - `docs/capabilities/CAPABILITY_REGISTRY.yaml`
3. Updated governance/docs:
   - `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`
   - `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`
   - `backend/app/hoc/docs/architecture/usecases/HOC_CAPABILITY_LINKAGE_WAVE1_REMEDIATION_2026-02-20.md`
   - `literature/hoc_domain/ops/SOFTWARE_BIBLE.md`

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
- HOC capability-linkage blocker count: **5 -> 0**
- Remaining open HOC blocker workstreams:
  - Layer segregation
  - Relative-import hygiene
