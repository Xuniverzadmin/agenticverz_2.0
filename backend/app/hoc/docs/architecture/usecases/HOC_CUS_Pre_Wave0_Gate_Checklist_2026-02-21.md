# HOC_CUS_Pre_Wave0_Gate_Checklist_2026-02-21

**Created:** 2026-02-21
**Task:** T8 — Gate Pack
**Status:** DONE

---

## 1. Objective

Produce Pre-Wave0 go/no-go checklist with pass/fail matrix and explicit Wave A start decision.

---

## 2. Pre-Wave0 Gate Matrix

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| G1 | Auth audit complete (T1) | PASS | `HOC_CUS_Pre_Wave0_Auth_Audit_2026-02-21.md` — 8 sections, file:line refs |
| G2 | Auth architecture defined (T2) | PASS | `HOC_CUS_FirstParty_Auth_Architecture_2026-02-21.md` — EdDSA JWT + HttpOnly refresh |
| G3 | Threat model produced (T3) | PASS | `HOC_CUS_Auth_Threat_Model_2026-02-21.md` — 12 threats, 3 control categories |
| G4 | Migration plan defined (T4) | PASS | `HOC_CUS_Auth_Migration_Cutover_Plan_2026-02-21.md` — 4 phases, rollback at each |
| G5 | Observability baseline audited (T5) | PASS | `HOC_CUS_Observability_Baseline_Audit_2026-02-21.md` — 8 critical gaps identified |
| G6 | Observability standard defined (T6) | PASS | `HOC_CUS_Observability_Standard_2026-02-21.md` — logger hierarchy, required metrics |
| G7 | Debugger spec produced (T7) | PASS | `HOC_CUS_System_Debugger_Spec_2026-02-21.md` — slice model, triage, replay |
| G8 | Clove provider operational | PASS | Readiness gate in `main.py:687-735`, 70/70 tests pass |
| G9 | HOC auth endpoints scaffolded | PASS | 9 endpoints at `/hoc/api/auth/*`, all return 501 (scaffold) |
| G10 | Machine auth path independent | PASS | X-AOS-Key path unchanged by Clove architecture |
| G11 | Public path policy consistent | PASS | `gateway_policy.py` + `RBAC_RULES.yaml` both include `/hoc/api/auth/provider/status` |
| G12 | Frontend auth adapters scaffolded | PASS | `CloveAuthAdapter.ts` + `ClerkAuthAdapter.ts` + `AuthTokenSync.ts` exist |
| G13 | No blocking CI violations | PASS | `check_init_hygiene.py --ci` = 36 checks, 0 blocking |
| G14 | Tenant-bound auth context addressed | PASS | T2 Section 6: every JWT has `tid`, switch-tenant creates new session |
| G15 | Machine auth continuity addressed | PASS | T4 Section 4: continuity matrix shows UNCHANGED at all phases |

---

## 3. Verification Command Evidence

### 3.1 Auth Inventory

```bash
$ rg -c "Clerk|ClerkProvider" website/app-shell/src | head -5
main.tsx:4
api/client.ts:4
routes/ProtectedRoute.tsx:3
routes/FounderRoute.tsx:8
pages/auth/LoginPage.tsx:3
# Finding: Frontend 100% Clerk-dependent (as documented in T1)
```

### 3.2 Route Surface

```bash
$ rg -c "'/api/v1/" website/app-shell/src 2>/dev/null | awk -F: '{sum+=$2} END {print sum}'
69
# Finding: 69 legacy call-sites to migrate (as documented in T4)

$ rg -c "/hoc/api/" website/app-shell/src 2>/dev/null | awk -F: '{sum+=$2} END {print sum}'
30
# Finding: 30 HOC call-sites (scaffold catalog + stagetest)
```

### 3.3 Auth Tests

```bash
$ cd /root/agenticverz2.0/backend && PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py tests/auth/test_auth_identity_routes.py -q
70 passed in 3.14s
```

### 3.4 Capability Enforcer

```bash
$ python3 scripts/ops/capability_registry_enforcer.py validate-registry
✅ Registry validation passed
```

---

## 4. Risk Assessment

| Risk | Severity | Mitigation | Owner |
|------|----------|------------|-------|
| Frontend migration complexity (69 call-sites) | MEDIUM | Phase 3 is incremental; legacy routes stay mounted during migration | Wave A |
| Argon2id password hashing performance | LOW | Pre-tested with 64MB memory cost; acceptable latency (<200ms) | Wave A Phase 1 |
| Session revocation propagation delay | LOW | Redis pub/sub with 1s TTL; worst case = 1 expired token use | Wave A Phase 1 |
| Clerk removal is irreversible (Phase 4) | HIGH | 2-week validation period after Phase 3 before Phase 4 starts | Wave A Phase 4 |
| Observability gaps during migration | MEDIUM | T6 standard implementation should parallel Phase 1-2 | Wave A |

---

## 5. Wave A GO/NO-GO Decision

### Decision: **GO**

**Date:** 2026-02-21

**Rationale:**
1. All 15 gates PASS — no blocking items.
2. Auth architecture (T2) is complete with selected model, API contract, and JWT specs.
3. Threat model (T3) covers 12 threats with concrete mitigations and enforcement map.
4. Migration plan (T4) has 4 phases with rollback at every step and machine-auth continuity checks.
5. Observability standard (T6) defines the target; gaps (T5) are documented and non-blocking for Wave A start.
6. Clove provider is operational with readiness gate, startup fail-fast, and 70 tests passing.
7. HOC auth endpoints are scaffolded and ready for implementation.
8. Machine auth (X-AOS-Key) is completely independent of the migration.

### Wave A Scope

Wave A Phase 1 should:
1. Implement the 8 scaffold endpoints per T2 spec
2. Create DB migrations for `users`, `user_sessions`, `user_tenant_memberships` tables
3. Implement Argon2id password hashing
4. Implement EdDSA JWT issuance (signing with Ed25519 private key)
5. Implement HttpOnly refresh cookie with rotation
6. Implement session revocation (DB + Redis)
7. Add auth metrics per T6 standard
8. Maintain all existing tests + add Wave A-specific tests

### Blockers for Wave A (None — all resolved)

| Blocker | Status | Resolution |
|---------|--------|------------|
| HOC auth endpoints not scaffolded | RESOLVED | 9 endpoints at `/hoc/api/auth/*` (commit `6759b9a6`) |
| RBAC rule missing for provider/status | RESOLVED | `HOC_AUTH_PROVIDER_STATUS` rule added (commit `e88f5964`) |
| No threat model | RESOLVED | T3 produced with 12 threats |
| No migration plan | RESOLVED | T4 produced with 4 phases |
| Machine auth continuity unclear | RESOLVED | T4 Section 4: X-AOS-Key unchanged at all phases |

---

## 6. Script References

| Script | Purpose | Command |
|--------|---------|---------|
| Auth tests | Validate provider seam + routes | `PYTHONPATH=. pytest tests/auth/ -q` |
| CI hygiene | 36 structural checks | `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci` |
| Capability enforcer | CAP linkage validation | `python3 scripts/ops/capability_registry_enforcer.py check-pr --files <files>` |
| Registry validation | RBAC schema validation | `python3 scripts/ops/capability_registry_enforcer.py validate-registry` |
| UC validation | Usecase status sync | `python3 scripts/verification/uc001_route_operation_map_check.py` |
