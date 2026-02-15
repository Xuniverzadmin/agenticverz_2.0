# UC Full-Scope Usecase Generation (All Scripts, Including Wave-Covered)

## Scope
Generate a complete UC-linking proposal across **all** `app/hoc/cus/*` scripts, including scripts already covered in Waves 1-4.

Inputs:
- `app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`
- `app/hoc/docs/architecture/usecases/HOC_CUS_SCRIPT_UC_GAP_UNLINKED_2026-02-12.txt`
- `tests/governance/t4/test_uc018_uc032_expansion.py`

Output:
- `app/hoc/docs/architecture/usecases/HOC_CUS_FULL_SCOPE_UC_PROPOSAL_2026-02-12.csv`

## Full-Scope Baseline
- Total scripts: `573`
- Current `UC_LINKED`: `176`
- Current `NON_UC_SUPPORT`: `278`
- Current `UNLINKED`: `119`

Non-init residual split:
- Non-init unlinked scripts: `88`
- Init-only unlinked scripts: `31`

## Full-Scope Proposal Outcome
From `HOC_CUS_FULL_SCOPE_UC_PROPOSAL_2026-02-12.csv`:
- `KEEP_EXISTING_UC`: `176`
- `KEEP_NON_UC_SUPPORT`: `278`
- `RECLASSIFY_NON_UC_SUPPORT` (init files): `31`
- `NEW_UC_LINK`: `88`

No manual-review rows remain.

## New Usecases Proposed

### UC-033: Spine Operation Governance and Contracts
- Target scripts: `26`
- Coverage: `hoc_spine/auth_wiring.py`, core `hoc_spine/orchestrator/*` (non-lifecycle), `hoc_spine/schemas/*`, `hoc_spine/tests/*`
- Intent: operation registration, dispatch contracts, orchestration invariants, schema contracts

### UC-034: Spine Lifecycle Orchestration
- Target scripts: `6`
- Coverage: `hoc_spine/orchestrator/lifecycle/*`
- Intent: onboarding/offboarding/pool lifecycle orchestration at L4

### UC-035: Spine Execution Safety and Driver Integrity
- Target scripts: `17`
- Coverage: `hoc_spine/drivers/*`, `hoc_spine/utilities/*`
- Intent: idempotency, transaction coordination, execution safety drivers/utilities

### UC-036: Spine Signals, Evidence, and Alerting
- Target scripts: `33`
- Coverage: `hoc_spine/consequences/*`, `hoc_spine/services/*`
- Intent: governance signals, evidence/audit services, alerting/compliance support surfaces

### UC-037: Integrations Secret Vault Lifecycle
- Target scripts: `3`
- Coverage: `integrations/L5_vault/*`
- Intent: integration credential vault and rule-check lifecycle

### UC-038: Integrations Notification Channel Lifecycle
- Target scripts: `1`
- Coverage: `integrations/L5_notifications/engines/channel_engine.py`
- Intent: notification channel orchestration for integrations flows

### UC-039: Integrations CLI Operational Bootstrap
- Target scripts: `1`
- Coverage: `integrations/cus_cli.py`
- Intent: CLI-run operational bootstrap path under HOC governance

### UC-040: Account CRM Audit Trail Lifecycle
- Target scripts: `1`
- Coverage: `account/logs/CRM/audit/audit_engine.py`
- Intent: account CRM audit evidence lifecycle

## Deterministic Gates for Promotion
For each new UC (`UC-033..UC-040`), require all gates:
1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
2. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
3. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`
6. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py`

UC-specific evidence requirements:
- L2->L4->L5/L6 route/operation linkage exists (or explicit runtime/facade authority path for hoc_spine infra)
- L5 purity checks pass (no runtime DB imports)
- L6 drivers contain no business-decision logic
- Registry docs updated in both:
  - `HOC_USECASE_CODE_LINKAGE.md`
  - `INDEX.md`

## Suggested Execution Order
1. UC-033
2. UC-034
3. UC-035
4. UC-036
5. UC-037
6. UC-038
7. UC-039
8. UC-040

## Claude Execution Command
```bash
cd /root/agenticverz2.0/backend && \
python3 -m pytest -q tests/governance/t4/test_uc018_uc032_expansion.py && \
PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json && \
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py && \
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py && \
PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json && \
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
```

## Notes
- This run explicitly included scripts already covered in Waves.
- Existing UC mappings were retained; missing existing `uc_id` entries were backfilled in proposal logic from governance test tuples and explicit mapping for residual gaps.
