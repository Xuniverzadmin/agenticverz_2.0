# UC Execution Taskpack (UC-033..UC-040) for Claude

- Date: 2026-02-13
- Source context:
  - `HOC_CUS_FULL_SCOPE_UC_PROPOSAL_2026-02-12.csv`
  - `UC_FULL_SCOPE_USECASE_GENERATION_2026-02-12.md`
- Goal: promote `UC-033..UC-040` from `RED -> YELLOW -> GREEN` with deterministic evidence.

## 0) Non-Negotiable Architecture Rules

1. Preserve topology: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7`.
2. Never allow direct L2 -> L5/L6 business calls.
3. Keep orchestration in L4; keep business decisions in L5.
4. Keep effects/persistence in L6 only.
5. No DB/ORM imports in L5 engines.
6. No business conditionals in L6 drivers.
7. No new `*_service.py` under HOC domains unless ratified exception.

## 1) Deterministic Gates (Run Every UC Closure)

Run in `backend/`:

1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
2. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
3. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`
6. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py`

Pass criteria:
1. All commands exit `0`.
2. No increase in cross-domain violations.
3. Pairing remains `orphaned=0` and `direct_l2_to_l5=0`.
4. Added/updated UC tests pass.

## 2) UC Backlog (Ordered)

## UC-033: Spine Operation Governance + Contracts (26 scripts)

Scope highlights:
- `hoc_spine/auth_wiring.py`
- `hoc_spine/orchestrator/operation_registry.py`
- `hoc_spine/orchestrator/plan_generation_engine.py`
- `hoc_spine/schemas/*`
- `hoc_spine/tests/test_operation_registry.py`

TODO:
1. Add concrete linkage evidence for operation registration + schema contract ownership.
2. Add/expand governance tests for deterministic operation dispatch and registry contract.
3. Record gate outputs and promote status.

Acceptance:
1. Deterministic operation registry behavior is test-covered.
2. Schema contracts are referenced by canonical handlers and evidence text.
3. All deterministic gates pass.

## UC-034: Spine Lifecycle Orchestration (6 scripts)

Scope highlights:
- `hoc_spine/orchestrator/lifecycle/drivers/execution.py`
- `hoc_spine/orchestrator/lifecycle/drivers/knowledge_plane.py`
- `hoc_spine/orchestrator/lifecycle/engines/onboarding.py`
- `hoc_spine/orchestrator/lifecycle/engines/offboarding.py`
- `hoc_spine/orchestrator/lifecycle/stages.py`

TODO:
1. Link lifecycle transitions to concrete operations and orchestration flow.
2. Add deterministic tests for lifecycle stage transition invariants.
3. Record evidence and run full gate pack.

Acceptance:
1. Lifecycle stage transitions are deterministic and L4-owned.
2. No direct L2->L5/L6 paths.
3. All deterministic gates pass.

## UC-035: Spine Execution Safety + Driver Integrity (17 scripts)

Scope highlights:
- `hoc_spine/drivers/idempotency.py`
- `hoc_spine/drivers/transaction_coordinator.py`
- `hoc_spine/drivers/guard_write_driver.py`
- `hoc_spine/drivers/ledger.py`
- `hoc_spine/utilities/recovery_decisions.py`

TODO:
1. Link safety/integrity drivers to explicit orchestration usage.
2. Add tests for idempotency/transaction invariants.
3. Verify drivers remain effect-only (no business branching creep).

Acceptance:
1. Safety and transaction behavior has deterministic tests.
2. Driver/engine boundaries are preserved.
3. All deterministic gates pass.

## UC-036: Spine Signals, Evidence, and Alerting (33 scripts)

Scope highlights:
- `hoc_spine/consequences/pipeline.py`
- `hoc_spine/services/alerts_facade.py`
- `hoc_spine/services/audit_store.py`
- `hoc_spine/services/retrieval_evidence_engine.py`
- `hoc_spine/services/compliance_facade.py`

TODO:
1. Link evidence/signal pipeline scripts to concrete UC operations.
2. Add tests for deterministic evidence generation and retrieval invariants.
3. Ensure consequence flow remains non-domain-owning and post-orchestration.

Acceptance:
1. Evidence/signal paths are deterministic and traceable.
2. No architecture boundary drift.
3. All deterministic gates pass.

## UC-037: Integrations Secret Vault Lifecycle (3 scripts)

Scope:
- `integrations/L5_vault/engines/service.py`
- `integrations/L5_vault/engines/vault_rule_check.py`
- `integrations/L5_vault/drivers/vault.py`

TODO:
1. Link vault lifecycle behavior to canonical integration/onboarding operations.
2. Add focused tests for vault rule-check and deterministic secret access behavior.
3. Run purity and full gates.

Acceptance:
1. Vault lifecycle is deterministic and architecture-safe.
2. L5/L6 purity holds.
3. All deterministic gates pass.

## UC-038: Integrations Notification Channel Lifecycle (1 script)

Scope:
- `integrations/L5_notifications/engines/channel_engine.py`

TODO:
1. Link notification channel operations to canonical orchestration path.
2. Add deterministic tests for channel config/dispatch behavior.
3. Run full gates and record evidence.

Acceptance:
1. Channel behavior is deterministic for fixed input/context.
2. No direct cross-layer violations.
3. All deterministic gates pass.

## UC-039: Integrations CLI Operational Bootstrap (1 script)

Scope:
- `integrations/cus_cli.py`

TODO:
1. Link CLI bootstrap flow to canonical runtime and tenant context contracts.
2. Add deterministic tests for CLI operational path (plan + run orchestration integration).
3. Run full gates and record evidence.

Acceptance:
1. CLI path is deterministic and architecture-compliant.
2. Tenant/context authority is preserved.
3. All deterministic gates pass.

## UC-040: Account CRM Audit Trail Lifecycle (1 script)

Scope:
- `account/logs/CRM/audit/audit_engine.py`

TODO:
1. Link CRM audit trail behavior to account lifecycle/operations.
2. Add deterministic tests for audit record creation/query invariants.
3. Run full gates and record evidence.

Acceptance:
1. Audit trail behavior is deterministic and test-backed.
2. Evidence is captured in linkage doc.
3. All deterministic gates pass.

## 3) Required Document Updates Per UC

1. Update `HOC_USECASE_CODE_LINKAGE.md` section with concrete evidence and status move (`RED -> YELLOW -> GREEN`).
2. Update `INDEX.md` usecase registry table status/date.
3. Update `PROD_READINESS_TRACKER.md` with new UC rows (initially `NOT_STARTED`) once UC reaches `GREEN`.
4. Publish implementation evidence artifact for this wave:
   - `UC_EXPANSION_UC033_UC040_implemented.md` (recommended filename)

## 4) Claude Execute Command (Batch)

```bash
claude -p "In /root/agenticverz2.0/backend execute UC-033..UC-040 closure from RED to GREEN using app/hoc/docs/architecture/usecases/UC_EXECUTION_TASKPACK_UC033_UC040_FOR_CLAUDE.md and app/hoc/docs/architecture/usecases/HOC_CUS_FULL_SCOPE_UC_PROPOSAL_2026-02-12.csv. For each UC add concrete code evidence in HOC_USECASE_CODE_LINKAGE.md, add/expand governance tests in tests/governance/t4/test_uc018_uc032_expansion.py, fix only architecture-safe issues, and run deterministic gates: hoc_cross_domain_validator, check_layer_boundaries, check_init_hygiene --ci, l5_spine_pairing_gap_detector --json, uc_mon_validation --strict, pytest -q tests/governance/t4/test_uc018_uc032_expansion.py. Publish app/hoc/docs/architecture/usecases/UC_EXPANSION_UC033_UC040_implemented.md with per-UC acceptance, fixes, and gate outputs."
```
