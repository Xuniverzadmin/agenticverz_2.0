# HOC Auth Seam V1 Test Case (2026-02-21)

## Test Case ID
- `TC-HOC-AUTH-001`

## Goal
- Validate that the in-house auth seam is enforced and observable:
  1. non-`hoc_identity` config emits warning in non-prod.
  2. non-`hoc_identity` config fails fast in prod.
  3. EdDSA token verifies via static JWKS provider path.
  4. legacy Clerk issuer is rejected.
  5. provider status endpoint returns effective provider `hoc_identity`.

## Preconditions
- Repo: `/root/agenticverz2.0`
- Python test environment available in `backend/`

## Execution Commands

```bash
set -euo pipefail
cd /root/agenticverz2.0/backend

PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py::TestProviderFactory::test_invalid_provider_emits_warning -q
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py::TestProviderFactory::test_invalid_provider_fails_fast_in_prod -q
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py::TestHocIdentityVerification::test_verifies_token_via_static_jwks_file -q
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py::TestGatewayProviderIntegration::test_clerk_issuer_rejected -q
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_identity_routes.py::TestScaffoldResponses::test_provider_status_returns_200 -q
```

## Expected Result
- All 5 commands pass.
- No failure output in pytest summary.

## Evidence to Capture
- Pytest output snippets for each command.
- Final pass/fail statement with timestamp.
- If any test fails: error trace + minimal remediation note.
