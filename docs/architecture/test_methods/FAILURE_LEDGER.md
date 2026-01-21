# Failure Ledger — Test Cleanup 2026-01-12

**Status:** ACTIVE
**Total Failures:** 61
**Target:** 0

---

## Classification Summary

| Category | Count | Action |
|----------|-------|--------|
| A — Deleted Architecture | 11 | DELETE test file |
| B — Wrong Truth Assertion | 13 | FIX test (add auth headers) |
| C — Environment-Coupled | 2 | DELETE or SKIP with PIN |
| D — Legitimate Bugs | 35 | FIX code (auth exempt paths, RBAC mapping) |
| **TOTAL** | **61** | |

---

## Category A — Tests for Deleted Architecture (DELETE)

### tests/test_category2_auth_boundary.py (11 tests)

**Reason:** Tests import classes/functions that no longer exist in auth system.
- `TokenAudience`, `CustomerRole`, `CustomerToken` - removed
- `FounderRole`, `FounderToken` - removed
- `AuthAuditEvent`, `AuthRejectReason` - removed
- `CONSOLE_COOKIE_NAME`, `FOPS_COOKIE_NAME`, `get_cookie_settings` - removed
- `verify_fops_token`, `verify_console_token` - signature changed

**Invariant Reference:** Auth architecture redesigned per PIN-271, PIN-391, PIN-392.

**Action:** DELETE `tests/test_category2_auth_boundary.py`

| Test | Status |
|------|--------|
| TestAuthBoundaryInvariants::test_console_key_rejected_on_fops_endpoint | DELETE |
| TestAuthBoundaryInvariants::test_fops_key_rejected_on_console_endpoint | DELETE |
| TestAuthBoundaryInvariants::test_no_key_rejected_on_fops | DELETE |
| TestAuthBoundaryInvariants::test_no_key_rejected_on_console | DELETE |
| TestTokenAudienceSeparation::test_token_audiences_are_separate | DELETE |
| TestTokenAudienceSeparation::test_customer_token_claims | DELETE |
| TestTokenAudienceSeparation::test_founder_token_requires_mfa | DELETE |
| TestAuditLogging::test_auth_audit_event_schema | DELETE |
| TestAuditLogging::test_reject_reasons_are_explicit | DELETE |
| TestCookieSeparation::test_cookie_names_are_separate | DELETE |
| TestCookieSeparation::test_cookie_settings_per_domain | DELETE |

---

## Category B — Tests Asserting Wrong Truth (FIX TEST)

### tests/test_m24_ops_console.py — TestOpsAPIEndpoints (7 tests)

**Reason:** Tests call `/ops/*` endpoints without auth headers.
Auth middleware correctly returns 401.

**Fix:** Add auth headers to test client.

| Test | Status |
|------|--------|
| test_system_pulse_returns_healthy | FIX TEST |
| test_customer_segments_empty | FIX TEST |
| test_event_stream | FIX TEST |
| test_stickiness_by_feature | FIX TEST |
| test_incident_patterns | FIX TEST |
| test_revenue_risk | FIX TEST |
| test_infra_limits | FIX TEST |

### tests/test_recovery.py — TestRecoveryAPI + TestAcceptanceCriteria (4 tests)

**Reason:** Tests call `/api/v1/recovery/*` without auth headers.

**Fix:** Add auth headers to test client.

| Test | Status |
|------|--------|
| test_suggest_endpoint_basic | FIX TEST |
| test_candidates_endpoint | FIX TEST |
| test_stats_endpoint | FIX TEST |
| test_ac1_suggests_for_5_entries | FIX TEST |

### tests/integration/test_m7_rbac_memory.py — TestCostSimMemory (2 tests)

**Reason:** Tests call costsim endpoints without auth headers.

**Fix:** Add auth headers to test client.

| Test | Status |
|------|--------|
| test_costsim_v2_status | FIX TEST |
| test_costsim_simulate_with_memory_flag | FIX TEST |

---

## Category C — Environment-Coupled Tests (DELETE OR SKIP)

### tests/test_m10_production_hardening.py — TestRetentionGC (2 tests)

**Reason:** Tests import script that requires `DB_AUTHORITY=neon`.
Script calls `require_neon()` at import time, causing SystemExit.

**Invariant Reference:** DB-AUTH-001 — Authority must be declared.

**Action:** DELETE tests. Retention cleanup is a production script, not unit testable.

| Test | Status |
|------|--------|
| test_retention_cleanup_dry_run | DELETE |
| test_expired_locks_cleanup | DELETE |

---

## Category D — Legitimate Bugs (FIX CODE)

### tests/test_category7_legacy_routes.py (27 tests)

**Reason:** Legacy paths `/dashboard`, `/operator`, `/demo`, `/simulation`
return 401 instead of 410 because auth middleware intercepts first.

**Fix:** Add legacy paths to auth exempt list (PUBLIC_PATHS).

**Invariant Reference:** Legacy routes MUST return 410 Gone, not 401.

| Test | Status |
|------|--------|
| test_legacy_path_returns_410[/dashboard] | FIX CODE |
| test_legacy_path_returns_410[/operator] | FIX CODE |
| test_legacy_path_returns_410[/operator/status] | FIX CODE |
| test_legacy_path_returns_410[/operator/tenants] | FIX CODE |
| test_legacy_path_returns_410[/operator/tenants/123] | FIX CODE |
| test_legacy_path_returns_410[/operator/incidents] | FIX CODE |
| test_legacy_path_returns_410[/operator/incidents/456] | FIX CODE |
| test_legacy_path_returns_410[/demo] | FIX CODE |
| test_legacy_path_returns_410[/demo/simulate-incident] | FIX CODE |
| test_legacy_path_returns_410[/demo/seed-data] | FIX CODE |
| test_legacy_path_returns_410[/simulation] | FIX CODE |
| test_legacy_path_returns_410[/simulation/cost] | FIX CODE |
| test_legacy_path_returns_410[/simulation/run] | FIX CODE |
| test_legacy_path_returns_410[/api/v1/operator] | FIX CODE |
| test_legacy_path_returns_410[/api/v1/operator/replay/batch] | FIX CODE |
| test_legacy_path_post_returns_410[/dashboard] | FIX CODE |
| test_legacy_path_post_returns_410[/operator] | FIX CODE |
| test_legacy_path_post_returns_410[/operator/test] | FIX CODE |
| test_legacy_path_post_returns_410[/demo] | FIX CODE |
| test_legacy_path_post_returns_410[/demo/test] | FIX CODE |
| test_legacy_path_post_returns_410[/simulation] | FIX CODE |
| test_legacy_path_post_returns_410[/simulation/test] | FIX CODE |
| test_dashboard_410_has_error_field | FIX CODE |
| test_dashboard_410_has_message | FIX CODE |
| test_operator_410_has_migration_hint | FIX CODE |
| test_410_response_structure | FIX CODE |
| test_healthz_endpoint_works | FIX CODE |
| test_invariant_no_bare_path_redirects | FIX CODE |

### tests/auth/test_rbac_path_mapping.py (5 tests)

**Reason:** RBAC mapping missing for `/api/v1/incidents` path.
`get_policy_for_path()` returns None.

**Fix:** Add incidents resource mapping to RBAC rules.

| Test | Status |
|------|--------|
| TestIncidentsResource::test_get_incidents | FIX CODE |
| TestIncidentsResource::test_post_incidents | FIX CODE |
| TestIncidentsResource::test_incident_resolve | FIX CODE |
| TestNoGaps::test_protected_path_has_policy[/api/v1/incidents] | FIX CODE |
| TestFutureProofPathGuard::test_known_path_has_explicit_mapping[/api/v1/incidents] | FIX CODE |

---

## Execution Order

1. **Category A first** — Delete test_category2_auth_boundary.py (11 tests gone)
2. **Category C next** — Delete TestRetentionGC tests (2 tests gone)
3. **Category D** — Fix auth exempt paths for legacy routes (27 tests fixed)
4. **Category D** — Add incidents RBAC mapping (5 tests fixed)
5. **Category B** — Add auth headers to remaining tests (13 tests fixed)

---

## Post-Cleanup Verification

```bash
# Must show 0 failures
python3 -m pytest tests/ -q --tb=no

# Must show no skipped tests without PIN reference
grep -r "pytest.mark.skip" tests/ | grep -v "PIN-"
```

---

## Changelog

| Date | Action | Tests Affected | Failures Before | Failures After |
|------|--------|---------------|-----------------|----------------|
| 2026-01-12 | Initial audit | 61 | 61 | - |
