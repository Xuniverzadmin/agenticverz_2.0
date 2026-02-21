# PIN-604: HOC Identity Seam Hardening and Observability

## Metadata
- Date: 2026-02-21
- Scope: In-house auth seam hardening (de-Clerk routing, provider policy enforcement, EdDSA/JWKS verification baseline, provider status observability)
- Capability: `CAP-006` (authentication)
- Branch context: `auth/scaffold-provider-seam`

## What Was Implemented

### 1) Provider policy hardening (no accidental Clerk fallback)
- File: `backend/app/auth/auth_provider.py`
- Changes:
  - `AUTH_PROVIDER` default locked to `hoc_identity`.
  - Non-`hoc_identity` values are explicitly overridden with a loud warning.
  - Prod-mode fail-fast added for invalid provider config (`AOS_MODE|APP_ENV|ENV` in `prod|production`).
  - Added `get_human_auth_provider_status()` for runtime observability.

### 2) Minimal HOC Identity verification path (V1 baseline)
- File: `backend/app/auth/auth_provider_hoc_identity.py`
- Changes:
  - Implemented EdDSA JWT verification.
  - Implemented required claim validation (canonical `JWTClaim.MANDATORY`).
  - Implemented JWKS load strategy:
    - URL or static JWKS file source
    - 10-minute cache TTL (configurable)
    - unknown-`kid` one-time refresh/retry.
  - Added provider diagnostics (issuer/audience, jwks source, cache state, last fetch timestamps).

### 3) Runtime provider status endpoint
- File: `backend/app/hoc/api/auth/routes.py`
- File: `backend/app/hoc/api/auth/schemas.py`
- Added:
  - `GET /hoc/api/auth/provider/status`
  - response model includes:
    - requested vs effective provider
    - forced policy flag
    - configured status
    - provider diagnostics payload.

### 4) Gateway and dependency alignment already locked in this cutover
- File: `backend/app/auth/gateway.py`
- File: `backend/app/auth/tenant_auth.py`
- Context:
  - Human issuer routing is HOC Identity only.
  - Tenant context messaging/session labels updated to HOC Identity semantics.

## Verification

- Tests:
  - `PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py tests/auth/test_auth_identity_routes.py -q`
  - Result: `42 passed`
- Governance gate:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files ...`
  - Result: pass with non-blocking `MISSING_EVIDENCE` warnings only.

## Documentation References

Primary implementation literature:
- `literature/hoc_domain/platform/HOC_PLATFORM_AUTH_PROVIDER_SEAM_CUTOVER_2026-02-21.md`

Software Bible update:
- `literature/hoc_domain/platform/SOFTWARE_BIBLE.md`

Design and baseline references:
- `backend/app/hoc/docs/architecture/usecases/HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_AUTH_SYSTEM_BASELINE_AND_INHOUSE_REPLACEMENT_REPORT_2026-02-21.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Pre_Wave0_Auth_Replacement_and_Observability_plan.md`
- `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Pre_Wave0_Auth_Replacement_and_Observability_plan_implemented.md`

## Outcome

Auth seam is now explicitly in-house-first, observable, and no longer silently dependent on Clerk routing behavior. The provider has a concrete EdDSA/JWKS verification baseline and an auditable status surface for stagetest/prod diagnostics.
