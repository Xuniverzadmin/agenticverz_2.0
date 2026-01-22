# PIN-436: Guardrail Violations Baseline

**Status:** ACTIVE
**Created:** 2026-01-16
**Category:** Governance / Architecture Enforcement
**Priority:** HIGH

---

## Summary

Baseline capture of 10 guardrail violations detected after implementing the 17-script governance enforcement system. These violations represent architectural gaps that must be fixed to achieve full governance compliance.

---

## Violation Summary

| # | Guardrail | Rule | Violations |
|---|-----------|------|------------|
| 1 | **DOMAIN-002** | Account domain boundaries | 3 |
| 2 | **DATA-001** | Cross-domain FK requirements | 1 |
| 3 | **LIMITS-001** | Single limit source of truth | 1 |
| 4 | **LIMITS-002** | Pre-execution limit check | 7 |
| 5 | **LIMITS-003** | Audit on limit change | 6 |
| 6 | **AUDIT-001** | Governance actions emit audit | 7 |
| 7 | **AUDIT-002** | Audit entry completeness | 2 |
| 8 | **CAP-003** | Capability status progression | 9 |
| 9 | **API-001** | Domain facade required | 2 |
| 10 | **API-002** | Consistent response envelope | 3 |

**Total Violations:** 41 across 10 guardrails
**Passed Guardrails:** 7 of 17 (41%)

---

## Detailed Violations

### 1. DOMAIN-002: Account Domain Boundaries

**Rule:** Account pages must NOT display Activity, Incidents, Policies, or Logs data.

**Violations (3):**
```
File: backend/app/api/aos_accounts.py

Line 33: Forbidden table reference - Incidents
Line 714: Reference to "runs" in tenant.runs_this_month
Line 732: Reference to "runs" in tenant.runs_this_month
```

**Fix:** Remove domain data references from account endpoints. Use separate domain APIs.

---

### 2. DATA-001: Cross-Domain FK Requirements

**Rule:** Cross-domain references MUST use foreign keys.

**Violations (1):**
```
Missing FK: incidents.source_run_id → runs
```

**Fix:** Create migration:
```sql
ALTER TABLE incidents ADD FOREIGN KEY (source_run_id) REFERENCES runs(id);
```

---

### 3. LIMITS-001: Single Limit Source of Truth

**Rule:** There is ONE limits system. No parallel limit tables.

**Violations (1):**
```
Parallel table detected: cost_budgets
Should use unified 'limits' table instead
```

**Fix:** Migrate `cost_budgets` data and logic to unified `limits` table.

---

### 4. LIMITS-002: Pre-Execution Limit Check

**Rule:** Every run creation MUST check limits BEFORE execution.

**Violations (7):**
```
File: backend/app/worker/runner.py

Functions without limit check:
- _get_run
- _check_authorization
- _update_run
- _create_incident_for_failure
- _create_governance_records_for_run
- run
- _execute
```

**Fix:** Add `limits_service.check_all_limits()` call before any run creation.

---

### 5. LIMITS-003: Audit on Limit Change

**Rule:** Every limit change MUST emit an audit entry.

**Violations (6):**
```
Functions modifying limits without audit:
- budget_enforcement_engine.py: emit_budget_halt_decision
- policy_layer.py: list_violations, list_policy_versions, prune_temporal_metrics
- policy_proposals.py: list_proposals
- policy.py: list_approval_requests
```

**Fix:** Add `audit_ledger_service.emit_governance_event()` to each function.

---

### 6. AUDIT-001: Governance Actions Emit Audit

**Rule:** Every governance action MUST create an audit entry.

**Violations (7):**
```
Governance actions without audit emission:
- founder_actions.py: throttle_tenant (api_key_changed)
- integration.py: resolve_checkpoint (policy_decision)
- integration.py: simulate_regret (policy_modified)
- agents.py: update_agent_strategy (policy_modified)
- founder_lifecycle.py: result_to_response (api_key_changed)
- rbac_api.py: reload_policies (policy_created)
- (1 more): limit_created operation
```

**Fix:** Add audit emission to each governance function.

---

### 7. AUDIT-002: Audit Entry Completeness

**Rule:** Every audit entry MUST have required fields (actor, action, target, timestamp, tenant_id).

**Violations (2):**
```
File: backend/app/api/rbac_api.py

Line 60: Missing fields - actor, action, target, timestamp, tenant_id
Line 271: Missing fields - actor, target, timestamp
```

**Fix:** Complete all required fields in audit entry creation.

---

### 8. CAP-003: Capability Status Progression

**Rule:** Capability status must be valid (DECLARED, OBSERVED, TRUSTED, DEPRECATED, DEFERRED).

**Violations (9):**
```
Invalid status "ASSUMED" in capabilities:
- policies.violations_list
- policies.versions_list
- policies.temporal_policies
- policies.risk_ceilings
- policies.current_version
- policies.layer_metrics
- policies.quota_runs
- (2 more)

Invalid status "LOCKED":
- CAPABILITY_STATUS_MODEL
```

**Fix:** Change `ASSUMED` → `DECLARED` in capability YAML files.

---

### 9. API-001: Domain Facade Required

**Rule:** External code must use domain facades, not direct service imports.

**Violations (2):**
```
Direct incident service imports:
- backend/app/api/ops.py: OpsIncidentService
- backend/app/worker/runner.py: get_incident_engine
```

**Fix:** Import via `incident_facade` instead of direct service imports.

---

### 10. API-002: Consistent Response Envelope

**Rule:** All API responses must use standard envelope format.

**Violations (3):**
```
File: backend/app/api/scenarios.py

- POST /{scenario_id}/simulate → direct model return
- POST /simulate-adhoc → direct model return
- GET /info/immutability → raw dict return
```

**Fix:** Wrap responses in `ResponseEnvelope(data=..., meta=...)`.

---

## Priority Matrix

### Critical (Data Integrity)
| Fix | Impact | Effort |
|-----|--------|--------|
| DATA-001: Add FK incidents.source_run_id → runs | High | Low |
| LIMITS-001: Migrate cost_budgets → limits | High | Medium |

### High (Security/Audit)
| Fix | Impact | Effort |
|-----|--------|--------|
| LIMITS-002: Add limit checks to runner.py | High | Medium |
| AUDIT-001: Add audit to 7 governance functions | High | Medium |
| AUDIT-002: Complete audit entries in rbac_api.py | Medium | Low |

### Medium (Architecture)
| Fix | Impact | Effort |
|-----|--------|--------|
| DOMAIN-002: Remove domain refs from accounts.py | Medium | Low |
| API-001: Use incident_facade | Medium | Low |
| CAP-003: Fix capability status values | Low | Low |

### Low (Consistency)
| Fix | Impact | Effort |
|-----|--------|--------|
| API-002: Add response envelopes to 3 endpoints | Low | Low |

---

## Enforcement System

**Scripts Location:** `scripts/ci/`

```
run_guardrails.py              # Main runner
guardrail_enforcer.py          # 3-layer enforcement
guardrail_precommit.py         # Pre-commit hook
guardrail_watcher.py           # Event-driven watcher
check_*.py                     # 17 individual checks
```

**Hooks Installed:**
- `pre-commit` - Blocks commits with violations
- `post-commit` - Records bypass usage
- `pre-push` - Blocks unauthorized bypasses

**Commands:**
```bash
# Run all guardrails
python scripts/ci/run_guardrails.py

# Check enforcement status
python scripts/ci/guardrail_enforcer.py --status

# View bypass ledger
python scripts/ci/guardrail_enforcer.py --bypasses
```

---

## Related

- GOVERNANCE_GUARDRAILS.md - Full guardrail documentation
- CUSTOMER_CONSOLE_BUILD_PLAN.md - Build plan based on audits
- CROSS_DOMAIN_AUDIT.md - Cross-domain integration gaps

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial baseline capture of 41 violations across 10 guardrails |
