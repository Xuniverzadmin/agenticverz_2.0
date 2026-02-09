# Governance Guardrails & Architecture Violation Prevention

**Status:** MANDATORY ENFORCEMENT
**Created:** 2026-01-16
**Scope:** Customer Console Architecture

---

## 0. Purpose

This document defines the guardrails that PREVENT the problems discovered in the domain audits from recurring. Every rule has automated enforcement.

> **Principle:** If it's not enforced by code, it's not a rule—it's a suggestion.

---

## 1. Guardrail Categories

| Category | Purpose | Enforcement |
|----------|---------|-------------|
| **DOMAIN** | Prevent domain boundary violations | CI + Runtime |
| **DATA** | Prevent data integrity violations | DB + CI |
| **CROSS-DOMAIN** | Prevent silo creation | CI + Runtime |
| **LIMITS** | Prevent limit fragmentation | CI + Runtime |
| **AUDIT** | Prevent untracked mutations | Runtime |
| **CAPABILITY** | Prevent wrong capability bindings | CI |
| **API** | Prevent facade bypass | CI + Runtime |

---

## 2. Domain Boundary Guardrails

### DOMAIN-001: Domain Ownership Enforcement

**Rule:** Each table belongs to exactly ONE domain. No cross-domain writes.

| Table | Owner Domain | Can Write | Cannot Write |
|-------|--------------|-----------|--------------|
| `runs`, `worker_runs` | Activity | Activity services | Incidents, Policies, Logs |
| `incidents` | Incidents | IncidentEngine only | Activity, Policies, Analytics |
| `policy_rules`, `limits` | Policies | PolicyEngine only | Activity, Incidents, Analytics |
| `cost_records`, `cost_anomalies` | Analytics | CostServices only | Activity, Incidents, Policies |
| `audit_ledger`, `aos_traces` | Logs | AuditService, TraceStore | All others |
| `tenants`, `users`, `api_keys` | Accounts | AccountServices only | All domains |

**Enforcement:**

```python
# backend/app/core/domain_guard.py

DOMAIN_TABLE_OWNERSHIP = {
    "Activity": ["runs", "worker_runs", "agents"],
    "Incidents": ["incidents", "incident_notes"],
    "Policies": ["policy_rules", "policy_proposals", "limits", "prevention_records"],
    "Analytics": ["cost_records", "cost_budgets", "cost_anomalies", "feature_tags"],
    "Logs": ["audit_ledger", "aos_traces", "aos_trace_steps", "llm_run_records", "system_records"],
    "Accounts": ["tenants", "users", "tenant_memberships", "api_keys", "subscriptions"],
}

def assert_domain_ownership(caller_domain: str, table: str):
    """Called before any write operation"""
    owner = get_table_owner(table)
    if owner != caller_domain:
        raise DomainViolationError(
            f"Domain '{caller_domain}' cannot write to table '{table}' owned by '{owner}'"
        )
```

**CI Check:**

```yaml
# .github/workflows/domain-boundaries.yml
- name: Check domain boundary violations
  run: |
    python scripts/ci/check_domain_writes.py
    # Scans all services for cross-domain table writes
    # FAILS if Activity service writes to incidents table
```

---

### DOMAIN-002: No Domain Data in Account Section

**Rule:** Account pages must NOT display Activity, Incidents, Policies, or Logs data.

**Enforcement:**

```python
# backend/app/api/aos_accounts.py

FORBIDDEN_IMPORTS_IN_ACCOUNTS = [
    "app.models.incident",
    "app.models.policy",
    "app.models.worker_runs",
    "app.models.audit_ledger",
]

# CI scanner checks imports
```

**CI Check:**

```bash
# scripts/ci/check_account_boundaries.sh
grep -r "from app.models.incident" backend/app/api/aos_accounts.py && exit 1
grep -r "from app.models.policy" backend/app/api/aos_accounts.py && exit 1
grep -r "from app.models.worker_runs" backend/app/api/aos_accounts.py && exit 1
echo "Account boundary check passed"
```

---

### DOMAIN-003: Overview is Read-Only Projection

**Rule:** Overview domain owns NO tables. All data derived via queries.

**Enforcement:**

```python
# backend/app/api/overview.py

# GUARDRAIL: Overview MUST NOT have any INSERT/UPDATE/DELETE operations
# This file should only contain SELECT queries

class OverviewService:
    """
    INVARIANT: This service is READ-ONLY.
    It projects data from other domains, never mutates.
    """

    def get_highlights(self, tenant_id: str) -> HighlightsResponse:
        # SELECT only - no writes allowed
        incidents = self._query_incidents(tenant_id)  # READ
        policies = self._query_policies(tenant_id)    # READ
        costs = self._query_costs(tenant_id)          # READ
        return self._project(incidents, policies, costs)
```

**CI Check:**

```python
# scripts/ci/check_overview_readonly.py
FORBIDDEN_IN_OVERVIEW = ["INSERT", "UPDATE", "DELETE", "session.add", "session.commit"]

def check_overview_file():
    with open("backend/app/api/overview.py") as f:
        content = f.read()
        for forbidden in FORBIDDEN_IN_OVERVIEW:
            if forbidden in content:
                raise ViolationError(f"Overview contains '{forbidden}' - must be read-only")
```

---

## 3. Data Integrity Guardrails

### DATA-001: Foreign Key Enforcement

**Rule:** All cross-domain references MUST use foreign keys with ON DELETE behavior.

**Required FKs:**

| FK | From Table | To Table | On Delete |
|----|------------|----------|-----------|
| `source_run_id` | incidents | runs | SET NULL |
| `incident_id` | cost_records | incidents | SET NULL |
| `incident_id` | cost_anomalies | incidents | SET NULL |
| `api_key_id` | cost_records | api_keys | SET NULL |
| `run_id` | aos_traces | runs | CASCADE |
| `incident_id` | aos_traces | incidents | SET NULL |
| `tenant_id` | ALL tables | tenants | CASCADE |

**Enforcement:**

```sql
-- Migration template for cross-domain FK
ALTER TABLE cost_records
ADD CONSTRAINT fk_cost_records_incident
FOREIGN KEY (incident_id) REFERENCES incidents(id)
ON DELETE SET NULL;

-- CI validates all required FKs exist
```

**CI Check:**

```python
# scripts/ci/check_foreign_keys.py
REQUIRED_FKS = [
    ("incidents", "source_run_id", "runs"),
    ("cost_records", "incident_id", "incidents"),
    ("cost_records", "api_key_id", "api_keys"),
    ("aos_traces", "run_id", "runs"),
    ("aos_traces", "incident_id", "incidents"),
]

def check_fks_exist():
    for table, column, ref_table in REQUIRED_FKS:
        if not fk_exists(table, column, ref_table):
            raise ViolationError(f"Missing FK: {table}.{column} -> {ref_table}")
```

---

### DATA-002: Tenant Isolation Invariant

**Rule:** Every customer-facing query MUST include `tenant_id` filter.

**Enforcement:**

```python
# backend/app/core/tenant_guard.py

def require_tenant_filter(query: Select, tenant_id: str) -> Select:
    """
    GUARDRAIL: All queries must be tenant-scoped.
    This function is called by base repository.
    """
    if not has_tenant_filter(query):
        raise TenantIsolationViolation(
            "Query missing tenant_id filter - potential data leak"
        )
    return query.where(table.c.tenant_id == tenant_id)
```

**Runtime Check:**

```python
# Middleware that validates all responses are tenant-scoped
class TenantIsolationMiddleware:
    async def __call__(self, request, call_next):
        response = await call_next(request)

        # Log warning if response contains data from multiple tenants
        # (Should never happen if queries are correct)
        if self._has_cross_tenant_data(response):
            log.critical("TENANT ISOLATION VIOLATION DETECTED")
            raise SecurityViolation("Cross-tenant data in response")

        return response
```

---

### DATA-003: Immutable Audit Records

**Rule:** Audit ledger entries are APPEND-ONLY. No updates or deletes.

**Enforcement:**

```sql
-- Database trigger prevents mutation
CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'GUARDRAIL VIOLATION: audit_ledger is immutable';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_ledger_immutable
BEFORE UPDATE OR DELETE ON audit_ledger
FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();
```

---

## 4. Cross-Domain Integration Guardrails

### CROSS-001: Mandatory Cross-Domain Propagation

**Rule:** Certain events MUST propagate to other domains.

| Event | Source Domain | Must Propagate To | Enforcement |
|-------|---------------|-------------------|-------------|
| Run fails | Activity | Incidents (create incident) | Runtime check |
| Budget exceeded | Analytics | Incidents (create incident) | Runtime check |
| Incident created | Incidents | Logs (audit entry) | Runtime check |
| Policy changed | Policies | Logs (audit entry) | Runtime check |
| Limit changed | Policies | Analytics (sync budget) | Runtime check |

**Enforcement:**

```python
# backend/app/core/propagation_guard.py

REQUIRED_PROPAGATIONS = {
    "run_failed": ["create_incident"],
    "budget_exceeded": ["create_incident"],
    "incident_created": ["emit_audit_entry"],
    "policy_changed": ["emit_audit_entry"],
    "limit_changed": ["sync_analytics_budget"],
}

class PropagationGuard:
    def __init__(self):
        self.pending_propagations = {}

    def event_occurred(self, event_type: str, entity_id: str):
        """Register that an event occurred"""
        required = REQUIRED_PROPAGATIONS.get(event_type, [])
        self.pending_propagations[entity_id] = required

    def propagation_completed(self, entity_id: str, propagation_type: str):
        """Mark a propagation as completed"""
        if entity_id in self.pending_propagations:
            self.pending_propagations[entity_id].remove(propagation_type)

    def verify_all_propagations(self):
        """Called at end of request - fails if propagations missing"""
        for entity_id, pending in self.pending_propagations.items():
            if pending:
                raise PropagationViolation(
                    f"Entity {entity_id} missing propagations: {pending}"
                )
```

**Runtime Middleware:**

```python
class PropagationEnforcementMiddleware:
    async def __call__(self, request, call_next):
        guard = PropagationGuard()
        request.state.propagation_guard = guard

        response = await call_next(request)

        # Verify all required propagations happened
        guard.verify_all_propagations()

        return response
```

---

### CROSS-002: Bidirectional Query Requirement

**Rule:** If domain A links to domain B, both directions must be queryable.

| Link | Forward Query | Reverse Query | Status |
|------|---------------|---------------|--------|
| Run → Incident | `GET /incidents?source_run_id=X` | `GET /runs/{id}/incidents` | **REQUIRED** |
| Incident → Cost | `GET /incidents/{id}/cost-impact` | `GET /costs?incident_id=X` | **REQUIRED** |
| Anomaly → Incident | `GET /incidents/{id}` (from anomaly) | `GET /anomalies?incident_id=X` | **REQUIRED** |

**CI Check:**

```python
# scripts/ci/check_bidirectional_queries.py
REQUIRED_BIDIRECTIONAL = [
    ("runs", "incidents", "/runs/{id}/incidents"),
    ("incidents", "cost_records", "/incidents/{id}/cost-impact"),
    ("cost_anomalies", "incidents", "/anomalies?incident_id="),
]

def check_reverse_endpoints_exist():
    for source, target, endpoint_pattern in REQUIRED_BIDIRECTIONAL:
        if not endpoint_exists(endpoint_pattern):
            raise ViolationError(f"Missing reverse query: {source} <- {target}")
```

---

### CROSS-003: No Silo Creation

**Rule:** New tables MUST declare cross-domain relationships at creation time.

**Enforcement:**

```python
# Migration template requirement
"""
GUARDRAIL: Every new table migration must include:
1. Domain ownership declaration
2. Cross-domain FK declarations (if any)
3. Propagation requirements (if any)

Example:
# Domain: Analytics
# Cross-Domain FKs: incident_id -> incidents, run_id -> runs
# Propagations: On HIGH severity -> create_incident
"""

# CI scanner validates migration files
def check_migration_declarations(migration_file: str):
    content = read_file(migration_file)
    if "CREATE TABLE" in content:
        if "# Domain:" not in content:
            raise ViolationError(f"Migration {migration_file} missing domain declaration")
```

---

## 5. Limits Guardrails

### LIMITS-001: Single Source of Truth

**Rule:** There is ONE limits system for enforcement. No parallel enforcement tables.
Observational analytics budgets are allowed if they do not gate execution.

**Forbidden:**
- Creating `tenant_quotas` separate from `limits`
- Creating `rate_limits` separate from `limits`

**Allowed (Analytics, observational only):**
- `cost_budgets` (analytics spend tracking, no enforcement)

**Enforcement:**

```python
# scripts/ci/check_limit_tables.py
ALLOWED_LIMIT_TABLES = ["limits", "limit_breaches", "cost_budgets"]

def check_no_parallel_limits():
    all_tables = get_all_tables()
    for table in all_tables:
        if "limit" in table.lower() or "quota" in table.lower() or "budget" in table.lower():
            if table not in ALLOWED_LIMIT_TABLES:
                raise ViolationError(
                    f"Parallel limit table detected: {table}. Use unified 'limits' table."
                )
```

---

### LIMITS-002: Pre-Execution Check Required

**Rule:** Every run creation MUST check limits BEFORE execution.

**Enforcement:**

```python
# backend/app/api/runs.py

@router.post("/runs")
async def create_run(request: RunRequest, ctx: AuthContext):
    # GUARDRAIL: Limit check is MANDATORY before run creation
    limit_check = await limits_service.check_all_limits(
        tenant_id=ctx.tenant_id,
        estimated_cost=request.estimated_cost,
        estimated_tokens=request.estimated_tokens
    )

    if not limit_check.allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "limit_exceeded",
                "blocking_limits": limit_check.blocking_limits,
                "recommendations": limit_check.recommendations
            }
        )

    # Only proceed if limits check passes
    return await run_service.create_run(request)
```

**CI Check:**

```python
# Verify all run creation paths include limit check
def check_run_creation_has_limit_check():
    run_creation_files = find_files_with("create_run")
    for file in run_creation_files:
        content = read_file(file)
        if "create_run" in content and "check_all_limits" not in content:
            raise ViolationError(f"{file} creates runs without limit check")
```

---

### LIMITS-003: Limit Changes Require Audit

**Rule:** Every limit change MUST emit an audit entry.

**Enforcement:**

```python
# backend/app/services/limits_service.py

class LimitsService:
    def __init__(self, audit_service: AuditLedgerService):
        self.audit = audit_service

    async def update_limit(self, limit_id: str, new_value: Decimal, actor: Actor):
        old_limit = await self.get_limit(limit_id)

        # Update limit
        await self._do_update(limit_id, new_value)

        # GUARDRAIL: Audit entry is MANDATORY
        await self.audit.emit(
            event_type="LIMIT_UPDATED",
            entity_type="LIMIT",
            entity_id=limit_id,
            actor=actor,
            changes={
                "old_value": str(old_limit.max_value),
                "new_value": str(new_value)
            }
        )
```

---

## 6. Audit Guardrails

### AUDIT-001: Governance Actions Must Emit Audit

**Rule:** These actions MUST create audit entries:

| Action | Entity Type | Required Fields |
|--------|-------------|-----------------|
| Policy rule created/updated/deleted | POLICY_RULE | rule_id, changes, actor |
| Limit created/updated/deleted | LIMIT | limit_id, changes, actor |
| Incident acknowledged/resolved | INCIDENT | incident_id, action, actor |
| API key created/revoked/frozen | API_KEY | key_id, action, actor |
| User role changed | USER | user_id, old_role, new_role, actor |

**Enforcement:**

```python
# backend/app/core/audit_guard.py

AUDITABLE_ACTIONS = {
    "policy_rule": ["create", "update", "delete"],
    "limit": ["create", "update", "delete"],
    "incident": ["acknowledge", "resolve", "reopen"],
    "api_key": ["create", "revoke", "freeze", "unfreeze"],
    "user": ["role_change", "invite", "remove"],
}

class AuditGuard:
    def __init__(self):
        self.pending_audits = []

    def action_performed(self, entity_type: str, action: str, entity_id: str):
        if action in AUDITABLE_ACTIONS.get(entity_type, []):
            self.pending_audits.append((entity_type, action, entity_id))

    def audit_emitted(self, entity_type: str, action: str, entity_id: str):
        try:
            self.pending_audits.remove((entity_type, action, entity_id))
        except ValueError:
            pass

    def verify_all_audited(self):
        if self.pending_audits:
            raise AuditViolation(
                f"Actions not audited: {self.pending_audits}"
            )
```

---

### AUDIT-002: Audit Entries Must Be Complete

**Rule:** Every audit entry must have all required fields.

**Enforcement:**

```python
# backend/app/services/audit_ledger_service.py

REQUIRED_AUDIT_FIELDS = ["event_type", "entity_type", "entity_id", "actor_type", "actor_id", "timestamp"]

class AuditLedgerService:
    async def emit(self, **kwargs):
        # GUARDRAIL: Validate all required fields present
        for field in REQUIRED_AUDIT_FIELDS:
            if field not in kwargs or kwargs[field] is None:
                raise AuditValidationError(f"Audit entry missing required field: {field}")

        # Create the audit entry
        entry = AuditLedger(**kwargs)
        await self.repository.create(entry)
```

---

## 7. Capability Guardrails

### CAP-001: Capability Must Match Endpoint

**Rule:** Capability registry endpoint must match actual API endpoint.

**Enforcement:**

```python
# scripts/ci/check_capability_endpoints.py

def check_capabilities():
    capabilities = load_capability_registry()
    for cap in capabilities:
        endpoint = cap["endpoint"]
        method = cap.get("method", "GET")

        # Verify endpoint actually exists
        if not endpoint_exists(endpoint, method):
            raise ViolationError(
                f"Capability '{cap['name']}' references non-existent endpoint: {method} {endpoint}"
            )

        # Verify endpoint is in correct facade
        expected_facade = get_expected_facade(cap["domain"])
        if not endpoint.startswith(expected_facade):
            raise ViolationError(
                f"Capability '{cap['name']}' endpoint {endpoint} not in facade {expected_facade}"
            )
```

---

### CAP-002: No Wrong Console Bindings

**Rule:** Customer console capabilities must NOT bind to founder/ops endpoints.

**Forbidden Patterns:**
- `/fdr/*`
- `/ops/*`
- `/admin/*`

**Enforcement:**

```python
# scripts/ci/check_console_boundaries.py

FORBIDDEN_PREFIXES_FOR_CUSTOMER = ["/fdr/", "/ops/", "/admin/"]

def check_customer_capabilities():
    capabilities = load_capability_registry()
    for cap in capabilities:
        if cap["console"] == "customer":
            endpoint = cap["endpoint"]
            for forbidden in FORBIDDEN_PREFIXES_FOR_CUSTOMER:
                if endpoint.startswith(forbidden):
                    raise ViolationError(
                        f"Customer capability '{cap['name']}' binds to forbidden endpoint: {endpoint}"
                    )
```

---

### CAP-003: Capability Status Progression

**Rule:** Capabilities must progress through states correctly.

```
DECLARED → OBSERVED → TRUSTED → DEPRECATED
    ↓
  (delete if never observed)
```

**Enforcement:**

```python
# scripts/ci/check_capability_status.py

VALID_TRANSITIONS = {
    "DECLARED": ["OBSERVED", None],  # Can be deleted if never observed
    "OBSERVED": ["TRUSTED", "DEPRECATED"],
    "TRUSTED": ["DEPRECATED"],
    "DEPRECATED": [],  # Terminal state
}

def check_capability_transitions():
    current = load_capability_registry()
    previous = load_previous_capability_registry()  # From git history

    for cap_name, cap in current.items():
        if cap_name in previous:
            old_status = previous[cap_name]["status"]
            new_status = cap["status"]
            if new_status not in VALID_TRANSITIONS.get(old_status, []):
                raise ViolationError(
                    f"Invalid capability transition: {cap_name} {old_status} -> {new_status}"
                )
```

---

## 8. API Guardrails

### API-001: Domain Facade Required

**Rule:** All domain data MUST be accessed through unified facade.

| Domain | Facade | Forbidden Direct Access |
|--------|--------|-------------------------|
| Activity | `/api/v1/activity/*` | Direct table queries in other routers |
| Incidents | `/api/v1/incidents/*` | Direct table queries in other routers |
| Policies | `/api/v1/policies/*` | Direct table queries in other routers |
| Logs | `/api/v1/logs/*` | Direct table queries in other routers |
| Analytics | `/api/v1/analytics/*` | `/cost/*` directly |
| Overview | `/api/v1/overview/*` | Direct aggregation queries |

**Enforcement:**

```python
# scripts/ci/check_facade_usage.py

def check_no_direct_table_access():
    api_files = glob("backend/app/api/*.py")
    for file in api_files:
        domain = get_domain_from_file(file)
        content = read_file(file)

        # Check for direct imports of other domain models
        for other_domain in ALL_DOMAINS:
            if other_domain != domain:
                model_import = f"from app.models.{other_domain.lower()}"
                if model_import in content:
                    # Allowed if using service, not direct query
                    if f"{other_domain}Service" not in content:
                        raise ViolationError(
                            f"{file} directly accesses {other_domain} domain models"
                        )
```

---

### API-002: Consistent Response Envelope

**Rule:** All API endpoints must return responses wrapped in a standard envelope.

```python
# Standard envelope format
{
    "success": true,
    "data": { ... },
    "meta": {
        "timestamp": "...",
        "request_id": "..."
    }
}

# List endpoint format
{
    "items": [...],
    "total": int,
    "has_more": bool,
    "filters_applied": dict
}
```

#### Risk Vectors & Counter-Rules

**RISK-001: "Just wrap it" mentality**

```python
# ❌ VIOLATION - Wrapping internal/partial objects
return wrap_dict(some_partial_or_internal_object)
return wrap_dict(domain_entity)  # Raw SQLModel/ORM object
return wrap_dict(intermediate_result)  # Partial computation

# ✅ CORRECT - Only wrap finalized outputs
return wrap_dict(result.model_dump())  # Pydantic model → dict
return wrap_dict({"key": "value", ...})  # Fully constructed dict
```

**Counter-rule (API-002-CR-001):**
> `wrap_dict()` must ONLY receive:
> 1. `model_dump()` output from Pydantic models
> 2. Fully constructed response dictionaries
>
> **Never** internal domain objects, ORM entities, or partial results.

---

**RISK-002: Ad-hoc total computation**

```python
# ⚠️ CORRECT FOR NON-PAGINATED ONLY
return wrap_dict({"items": [...], "total": len(results)})
```

This pattern is **correct for non-paginated endpoints** but becomes a lie when:
- Pagination is later added (total ≠ len(current_page))
- Results are pre-filtered (total reflects filtered, not actual)
- DB-level counts diverge from in-memory counts

**Counter-rule (API-002-CR-002):**
> The `{"items": [...], "total": len(results)}` pattern is valid ONLY for:
> - Non-paginated endpoints
> - Endpoints where `results` represents the complete dataset
>
> For paginated endpoints, `total` MUST come from a separate `COUNT(*)` query.

---

**Enforcement:**

```python
# scripts/ci/check_response_envelopes.py

def check_list_endpoints():
    openapi_spec = load_openapi_spec()
    for path, methods in openapi_spec["paths"].items():
        if "get" in methods:
            response_schema = methods["get"]["responses"]["200"]["content"]["application/json"]["schema"]
            if is_list_endpoint(path, response_schema):
                required_fields = ["items", "total", "has_more"]
                for field in required_fields:
                    if field not in response_schema.get("properties", {}):
                        raise ViolationError(
                            f"List endpoint {path} missing envelope field: {field}"
                        )
```

---

## 9. CI Pipeline Integration

### Required CI Jobs

```yaml
# .github/workflows/architecture-guardrails.yml

name: Architecture Guardrails

on: [push, pull_request]

jobs:
  domain-boundaries:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check domain ownership
        run: python scripts/ci/check_domain_writes.py
      - name: Check account boundaries
        run: bash scripts/ci/check_account_boundaries.sh
      - name: Check overview readonly
        run: python scripts/ci/check_overview_readonly.py

  data-integrity:
    runs-on: ubuntu-latest
    steps:
      - name: Check foreign keys
        run: python scripts/ci/check_foreign_keys.py
      - name: Check tenant isolation
        run: python scripts/ci/check_tenant_queries.py

  cross-domain:
    runs-on: ubuntu-latest
    steps:
      - name: Check bidirectional queries
        run: python scripts/ci/check_bidirectional_queries.py
      - name: Check propagation requirements
        run: python scripts/ci/check_propagations.py

  limits:
    runs-on: ubuntu-latest
    steps:
      - name: Check no parallel limit tables
        run: python scripts/ci/check_limit_tables.py
      - name: Check pre-execution limit checks
        run: python scripts/ci/check_limit_enforcement.py

  capabilities:
    runs-on: ubuntu-latest
    steps:
      - name: Check capability endpoints
        run: python scripts/ci/check_capability_endpoints.py
      - name: Check console boundaries
        run: python scripts/ci/check_console_boundaries.py
      - name: Check capability status
        run: python scripts/ci/check_capability_status.py

  api:
    runs-on: ubuntu-latest
    steps:
      - name: Check facade usage
        run: python scripts/ci/check_facade_usage.py
      - name: Check response envelopes
        run: python scripts/ci/check_response_envelopes.py
```

---

## 10. Runtime Enforcement

### Middleware Stack

```python
# backend/app/main.py

app.add_middleware(TenantIsolationMiddleware)      # DATA-002
app.add_middleware(PropagationEnforcementMiddleware)  # CROSS-001
app.add_middleware(AuditEnforcementMiddleware)     # AUDIT-001
app.add_middleware(LimitEnforcementMiddleware)     # LIMITS-002
```

### Database Triggers

```sql
-- Immutable audit ledger (DATA-003)
CREATE TRIGGER audit_ledger_immutable
BEFORE UPDATE OR DELETE ON audit_ledger
FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

-- Tenant isolation (DATA-002)
CREATE POLICY tenant_isolation ON runs
FOR ALL USING (tenant_id = current_setting('app.tenant_id'));
```

---

## 11. Violation Response Matrix

| Guardrail | Violation Type | CI Response | Runtime Response |
|-----------|----------------|-------------|------------------|
| DOMAIN-001 | Cross-domain write | ❌ BLOCK merge | 500 + alert |
| DOMAIN-002 | Account boundary | ❌ BLOCK merge | N/A |
| DOMAIN-003 | Overview mutation | ❌ BLOCK merge | 500 + alert |
| DATA-001 | Missing FK | ❌ BLOCK merge | N/A |
| DATA-002 | Missing tenant filter | ⚠️ Warning | 500 + CRITICAL alert |
| DATA-003 | Audit mutation | N/A | 500 + DB rollback |
| CROSS-001 | Missing propagation | ⚠️ Warning | 500 + alert |
| CROSS-002 | Missing reverse query | ⚠️ Warning | N/A |
| LIMITS-001 | Parallel limit table | ❌ BLOCK merge | N/A |
| LIMITS-002 | No pre-execution check | ❌ BLOCK merge | 403 + log |
| AUDIT-001 | Unaudited action | ⚠️ Warning | 500 + alert |
| CAP-001 | Wrong endpoint | ❌ BLOCK merge | N/A |
| CAP-002 | Wrong console | ❌ BLOCK merge | N/A |
| API-001 | Facade bypass | ❌ BLOCK merge | N/A |

---

## 12. Guardrail Checklist for New Features

Before implementing ANY new feature, verify:

```
ARCHITECTURE GUARDRAIL CHECKLIST

□ Domain Ownership
  - Which domain owns this feature?
  - Which tables will be written to?
  - Are all tables owned by this domain?

□ Cross-Domain
  - Does this feature need data from other domains?
  - If yes, are you using the service/facade (not direct query)?
  - Does this create events that must propagate?
  - Have you added the propagation requirement?

□ Data Integrity
  - Are all cross-domain references using FKs?
  - Is tenant_id included in all queries?
  - Are audit entries emitted for governance actions?

□ Limits
  - Does this feature consume resources (cost, tokens, runs)?
  - Is pre-execution limit check in place?
  - Does limit change emit audit entry?

□ Capabilities
  - Is there a capability for this endpoint?
  - Does capability endpoint match actual endpoint?
  - Is capability in correct console (customer vs founder)?

□ API
  - Is endpoint under correct facade?
  - Does list endpoint return standard envelope?
  - Is response model documented in OpenAPI?
```

---

## 13. Enforcement Scripts

All enforcement scripts are located in `scripts/ci/`:

### Main Runner

```bash
# Run all guardrail checks
python scripts/ci/run_guardrails.py

# Strict mode - stop on first failure
python scripts/ci/run_guardrails.py --strict

# Generate markdown report
python scripts/ci/run_guardrails.py --report
```

### Individual Scripts by Category

| Rule ID | Script | Description |
|---------|--------|-------------|
| **DOMAIN-001** | `check_domain_writes.py` | Domain ownership enforcement |
| **DOMAIN-002** | `check_account_boundaries.py` | Account domain boundaries |
| **DOMAIN-003** | `check_overview_readonly.py` | Overview read-only enforcement |
| **DATA-001** | `check_foreign_keys.py` | Cross-domain FK requirements |
| **DATA-002** | `check_tenant_queries.py` | Tenant isolation in queries |
| **CROSS-001** | `check_cross_domain_propagation.py` | Mandatory event propagation |
| **CROSS-002** | `check_bidirectional_queries.py` | Bidirectional query endpoints |
| **LIMITS-001** | `check_limit_tables.py` | Single limit source of truth |
| **LIMITS-002** | `check_limit_enforcement.py` | Pre-execution limit check |
| **LIMITS-003** | `check_limit_audit.py` | Audit on limit change |
| **AUDIT-001** | `check_governance_audit.py` | Governance actions emit audit |
| **AUDIT-002** | `check_audit_completeness.py` | Audit entry completeness |
| **CAP-001** | `check_capability_endpoints.py` | Capability-endpoint match |
| **CAP-002** | `check_console_boundaries.py` | Console capability boundaries |
| **CAP-003** | `check_capability_status.py` | Capability status progression |
| **API-001** | `check_facade_usage.py` | Domain facade required |
| **API-002** | `check_response_envelopes.py` | Consistent response envelope |

### Script Directory Structure

```
scripts/ci/
├── run_guardrails.py              # Main runner for all checks
├── check_domain_writes.py         # DOMAIN-001
├── check_account_boundaries.py    # DOMAIN-002
├── check_overview_readonly.py     # DOMAIN-003
├── check_foreign_keys.py          # DATA-001
├── check_tenant_queries.py        # DATA-002
├── check_cross_domain_propagation.py  # CROSS-001
├── check_bidirectional_queries.py # CROSS-002
├── check_limit_tables.py          # LIMITS-001
├── check_limit_enforcement.py     # LIMITS-002
├── check_limit_audit.py           # LIMITS-003
├── check_governance_audit.py      # AUDIT-001
├── check_audit_completeness.py    # AUDIT-002
├── check_capability_endpoints.py  # CAP-001
├── check_console_boundaries.py    # CAP-002
├── check_capability_status.py     # CAP-003
├── check_facade_usage.py          # API-001
└── check_response_envelopes.py    # API-002
```

### CI Integration

Add to `.github/workflows/architecture-governance.yml`:

```yaml
name: Architecture Governance

on: [push, pull_request]

jobs:
  guardrails:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run Guardrail Checks
        run: python scripts/ci/run_guardrails.py --report

      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: guardrail-report
          path: docs/architecture/GUARDRAIL_CHECK_REPORT.md
```

---

## 14. Summary

| Category | Guardrails | Blocking CI | Runtime |
|----------|------------|-------------|---------|
| Domain | 3 | 3 | 1 |
| Data | 3 | 2 | 2 |
| Cross-Domain | 3 | 1 | 1 |
| Limits | 3 | 2 | 1 |
| Audit | 2 | 0 | 2 |
| Capability | 3 | 3 | 0 |
| API | 2 | 2 | 0 |
| **Total** | **19** | **13** | **7** |

**Principle:** 13 guardrails block at CI (prevent merge). 7 guardrails enforce at runtime (prevent execution). Together they create a closed enforcement loop.
