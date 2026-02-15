# PIN-551: CLI Canonicalization + Worker Relocation (HOC)

**Status:** ✅ COMPLETE  
**Created:** 2026-02-09  
**Category:** Architecture / Integrations / Runtime

---

## Summary

Customer‑facing CLI was relocated into the integrations domain under HOC, internal CLI moved under HOC internal integrations, and legacy root CLIs were removed without shims. Run creation now matches the API path: explicit `tenant_id`, explicit `origin_system_id`, plan generation via L4, then execution via RunRunner. The worker package was relocated from `app/worker` to `app/hoc/int/worker` to remove `app/*` dependencies for runtime execution paths.

---

## Changes

### CLI Canonicalization (No Shims)

- **Customer CLI:** `backend/app/hoc/cus/integrations/cus_cli.py`
- **Internal CLI:** `backend/app/hoc/int/integrations/int_cli.py`
- **Legacy deleted:** `backend/app/aos_cli.py`, `backend/app/hoc/api/int/account/aos_cli.py`

### Run Creation Parity

- `cus_cli.py` now:
  - Requires `tenant_id`
  - Sets `origin_system_id`
  - Generates plan via `app.hoc.cus.policies.L5_engines.plan_generation.generate_plan_for_run`
  - Executes via `app.hoc.int.worker.runner.RunRunner`

### Worker Relocation

- Moved runtime worker package to `backend/app/hoc/int/worker/`
- Updated imports across app, tests, and scripts from `app.worker.*` → `app.hoc.int.worker.*`

---

## Rationale

- Enforce audience separation: customer‑facing CLIs must live under `hoc/cus`, internal tools under `hoc/int`.
- Remove root‑level `app/*` CLI shims and align with HOC topology rules.
- Ensure CLI run creation is identical to API creation (tenant‑scoped, plan‑generated, trace‑producing).

---

## Verification

- Customer CLI produces a real run with trace evidence in Postgres.
- Internal CLI remains demo/ops only (no run creation).
- Legacy CLIs removed; no shims introduced.

