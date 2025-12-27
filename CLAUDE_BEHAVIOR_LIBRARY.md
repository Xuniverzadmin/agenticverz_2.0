# AgenticVerz — Claude Behavior Library

**Version:** 1.0.0
**Effective:** 2025-12-27
**Status:** ACTIVE (Auto-Enforced)

---

## Purpose

This is a **machine-readable** set of behavior rules that Claude must follow.
These rules are **not prose** — they are structured constraints derived from real incidents.

Each rule answers:
> "What behavior would have prevented this class of bug from existing?"

---

## Rule Format

```yaml
- id: BL-XXX-NNN
  name: Rule Name
  class: Incident class this prevents
  triggers:
    - When to apply this rule
  requires:
    - Mandatory steps before proceeding
  forbid:
    - Actions that are never allowed
  violation: What happens if rule is broken
```

---

## Active Rules

### BL-ENV-001: Runtime Sync Before Test

**Class:** Environment-Behavior Drift after Code Change

**Problem:** Claude fixes code assuming runtime has updated, but the execution environment is still running old state.

```yaml
id: BL-ENV-001
name: Runtime Sync Before Test
class: environment_drift
severity: BLOCKING

triggers:
  - Any change to API endpoints
  - Any change to auth/RBAC logic
  - Any change to worker/execution lifecycle
  - Any change to retry behavior
  - Any migration applied

requires:
  step_1:
    action: "Enumerate docker compose services"
    command: "docker compose config --services"
    reason: "Know which services exist"
  step_2:
    action: "Identify target service name"
    command: "docker ps --format '{{.Names}}'"
    reason: "Map container names to services"
  step_3:
    action: "Rebuild target service explicitly"
    command: "docker compose up -d --build <service>"
    reason: "Ensure code changes are deployed"
  step_4:
    action: "Wait for health check"
    command: "curl -s http://localhost:PORT/health"
    condition: "status == healthy"
    reason: "Service must be ready before testing"
  step_5:
    action: "Verify auth contract for endpoint"
    check: "Which headers does this endpoint expect?"
    reason: "Auth mismatch causes false failures"

forbid:
  - Testing before container rebuild
  - Assuming rebuild happened
  - Ignoring health check failures
  - Testing with wrong auth headers

violation:
  type: BLOCKING
  message: "BL-ENV-001 VIOLATION: Runtime not synced before test"
  action: "STOP. Complete runtime sync before proceeding."

output_required: |
  RUNTIME SYNC CHECK
  - Services enumerated: YES / NO
  - Target service: <name>
  - Rebuild command: <command executed>
  - Health status: <healthy / unhealthy>
  - Auth headers verified: <list>
```

---

### BL-DB-001: Timestamp Semantics Alignment

**Class:** Timezone mismatch between Python and PostgreSQL

**Problem:** Python `datetime.now(timezone.utc)` produces timezone-aware datetime, but PostgreSQL `TIMESTAMP WITHOUT TIME ZONE` requires naive datetime.

```yaml
id: BL-DB-001
name: Timestamp Semantics Alignment
class: timezone_mismatch
severity: BLOCKING

triggers:
  - Any datetime helper function created
  - Any model with timestamp fields
  - Any field with `default_factory` returning datetime
  - Any migration adding timestamp columns

requires:
  step_1:
    action: "Check PostgreSQL column type"
    query: |
      SELECT column_name, data_type
      FROM information_schema.columns
      WHERE table_name = '<table>' AND column_name LIKE '%_at';
    check: "WITH TIME ZONE or WITHOUT TIME ZONE?"
  step_2:
    action: "Match Python datetime to column type"
    rule: |
      TIMESTAMP WITHOUT TIME ZONE → datetime.utcnow() (naive)
      TIMESTAMP WITH TIME ZONE → datetime.now(timezone.utc) (aware)
  step_3:
    action: "Add explicit comment explaining choice"
    example: |
      def utc_now() -> datetime:
          """Return naive UTC datetime for TIMESTAMP WITHOUT TIME ZONE columns."""
          return datetime.utcnow()

forbid:
  - Using timezone-aware datetime with WITHOUT TIME ZONE columns
  - Using naive datetime with WITH TIME ZONE columns
  - Mixing datetime semantics in same table
  - Implicit timezone assumptions

violation:
  type: BLOCKING
  message: "BL-DB-001 VIOLATION: Timestamp semantics mismatch"
  error: "asyncpg.exceptions.DataError: can't subtract offset-naive and offset-aware datetimes"
  action: "STOP. Align datetime helper with column type."

output_required: |
  TIMESTAMP SEMANTICS CHECK
  - Table: <name>
  - Column type: WITH TIME ZONE / WITHOUT TIME ZONE
  - Python helper: datetime.utcnow() / datetime.now(timezone.utc)
  - Alignment verified: YES / NO
```

---

### BL-AUTH-001: Auth Contract Enumeration

**Class:** Auth path mismatch causing false 401/403 errors

**Problem:** Endpoint tested with wrong auth headers because auth contract not enumerated first.

```yaml
id: BL-AUTH-001
name: Auth Contract Enumeration Before Endpoint Test
class: auth_mismatch
severity: BLOCKING

triggers:
  - Testing any authenticated endpoint
  - Adding new endpoint with auth dependency
  - Debugging 401/403/422 errors
  - Any RBAC-protected route

requires:
  step_1:
    action: "Identify auth dependency in endpoint"
    check: "What does Depends(...) require?"
    example: "Depends(verify_api_key) → needs X-AOS-Key header"
  step_2:
    action: "Identify RBAC middleware requirements"
    check: "What roles/tokens does middleware accept?"
    options:
      - "X-Machine-Token → machine role"
      - "Authorization: Bearer <JWT> → role from token"
      - "X-Roles → testing override"
  step_3:
    action: "Enumerate all required headers"
    output: "List of headers needed for this endpoint"
  step_4:
    action: "Test with correct headers"
    verify: "Response is not 401/403/422 for auth reasons"

forbid:
  - Testing endpoint without knowing auth contract
  - Assuming headers from other endpoints work
  - Ignoring middleware layer
  - Guessing auth headers

violation:
  type: BLOCKING
  message: "BL-AUTH-001 VIOLATION: Auth contract not enumerated"
  action: "STOP. Enumerate auth contract before testing."

output_required: |
  AUTH CONTRACT CHECK
  - Endpoint: <path>
  - Endpoint auth: <Depends(...)>
  - RBAC policy: <resource:action>
  - Required headers: <list>
  - Test command: <curl with all headers>
```

---

### BL-MIG-001: Migration Head Verification

**Class:** Multiple alembic heads causing migration chaos

**Problem:** Creating migration without checking current heads creates branch forks.

```yaml
id: BL-MIG-001
name: Migration Head Verification
class: migration_fork
severity: BLOCKING

triggers:
  - Creating any new migration
  - Running alembic upgrade
  - Any schema change task

requires:
  step_1:
    action: "Check current migration state"
    command: "alembic current"
    output: "Current revision(s)"
  step_2:
    action: "Check all heads"
    command: "alembic heads"
    output: "List of head revisions"
  step_3:
    action: "Verify single head"
    condition: "Only ONE head should exist"
    if_multiple: "Create merge migration first"
  step_4:
    action: "Identify parent revision"
    value: "Parent for new migration"

forbid:
  - Creating migration without checking heads
  - Assuming parent revision
  - Ignoring multiple heads warning
  - Running upgrade with multiple heads

violation:
  type: BLOCKING
  message: "BL-MIG-001 VIOLATION: Migration heads not verified"
  action: "STOP. Resolve multiple heads before proceeding."

output_required: |
  MIGRATION HEAD CHECK
  - Current: <revision>
  - Heads: <list>
  - Single head: YES / NO
  - Parent for new migration: <revision>
```

---

### BL-DOCKER-001: Service Name Resolution

**Class:** Wrong service/container name causing rebuild failures

**Problem:** Docker service names differ from container names, causing confusion.

```yaml
id: BL-DOCKER-001
name: Docker Service Name Resolution
class: service_name_mismatch
severity: BLOCKING

triggers:
  - Any docker compose command
  - Any container restart
  - Any service rebuild

requires:
  step_1:
    action: "List compose services"
    command: "docker compose config --services"
    output: "Service names as defined in compose file"
  step_2:
    action: "List running containers"
    command: "docker ps --format '{{.Names}}'"
    output: "Actual container names"
  step_3:
    action: "Map service to container"
    example: |
      Service: backend → Container: nova_agent_manager
      Service: worker → Container: nova_worker
  step_4:
    action: "Use correct name for command"
    rule: |
      docker compose commands → use SERVICE name
      docker exec/logs → use CONTAINER name

forbid:
  - Assuming service name equals container name
  - Using container name in compose commands
  - Using service name in docker exec

violation:
  type: WARNING
  message: "BL-DOCKER-001 VIOLATION: Service/container name mismatch"
  action: "Verify correct name type for command."

output_required: |
  DOCKER NAME CHECK
  - Compose services: <list>
  - Running containers: <list>
  - Target service: <name>
  - Target container: <name>
  - Command uses: SERVICE / CONTAINER (correct?)
```

---

### BL-TEST-001: Test Execution Prerequisites

**Class:** Test failures due to missing prerequisites

**Problem:** Tests run before environment is ready, causing false failures.

```yaml
id: BL-TEST-001
name: Test Execution Prerequisites
class: test_prerequisites
severity: BLOCKING

triggers:
  - Running any test suite
  - Debugging test failures
  - CI pipeline execution

requires:
  step_1:
    action: "Verify database accessible"
    command: "psql $DATABASE_URL -c 'SELECT 1'"
    condition: "Returns 1"
  step_2:
    action: "Verify backend healthy"
    command: "curl -s localhost:8000/health"
    condition: "status == healthy"
  step_3:
    action: "Verify migrations applied"
    command: "alembic current"
    condition: "At expected head"
  step_4:
    action: "Verify test data exists (if needed)"
    check: "Required fixtures present"

forbid:
  - Running tests with unhealthy backend
  - Running tests with pending migrations
  - Running tests without database access
  - Assuming prerequisites are met

violation:
  type: BLOCKING
  message: "BL-TEST-001 VIOLATION: Test prerequisites not verified"
  action: "STOP. Complete prerequisites before testing."

output_required: |
  TEST PREREQUISITES CHECK
  - Database accessible: YES / NO
  - Backend healthy: YES / NO
  - Migrations current: YES / NO
  - Required fixtures: <present / missing>
```

---

## Rule Application Protocol

### When Rules Trigger

1. Claude detects trigger condition in task
2. Claude MUST complete all `requires` steps
3. Claude MUST NOT perform any `forbid` actions
4. Claude MUST include `output_required` in response

### Violation Handling

- **BLOCKING violations**: Claude must STOP and report
- **WARNING violations**: Claude may proceed with caution

### Adding New Rules

When an incident repeats or a new class is identified:

1. Classify the incident (what class of failure?)
2. Extract the behavior rule (what would have prevented it?)
3. Add rule to this library with unique ID
4. Update validator to check for rule compliance

---

## Rule Index

| ID | Name | Class | Severity |
|----|------|-------|----------|
| BL-ENV-001 | Runtime Sync Before Test | environment_drift | BLOCKING |
| BL-DB-001 | Timestamp Semantics Alignment | timezone_mismatch | BLOCKING |
| BL-AUTH-001 | Auth Contract Enumeration | auth_mismatch | BLOCKING |
| BL-MIG-001 | Migration Head Verification | migration_fork | BLOCKING |
| BL-DOCKER-001 | Service Name Resolution | service_name_mismatch | WARNING |
| BL-TEST-001 | Test Execution Prerequisites | test_prerequisites | BLOCKING |

---

## Incident → Rule Conversion Template

When a new incident occurs:

```yaml
# New Rule Template
id: BL-XXX-NNN
name: <Descriptive Name>
class: <incident_class>
severity: BLOCKING / WARNING

# What was the incident?
incident:
  date: YYYY-MM-DD
  description: <What happened>
  root_cause: <Why it happened>
  time_wasted: <Debugging time>

# What would have prevented it?
prevention:
  trigger: <When should this rule apply?>
  check: <What should be verified?>
  output: <What evidence is required?>

# Structured rule
triggers:
  - <condition 1>
  - <condition 2>

requires:
  - <step 1>
  - <step 2>

forbid:
  - <forbidden action 1>
  - <forbidden action 2>

violation:
  type: BLOCKING
  message: "<ID> VIOLATION: <description>"
  action: "STOP. <what to do>"
```

---

## Related Documents

- `CLAUDE_BOOT_CONTRACT.md` — Session initialization
- `CLAUDE_PRE_CODE_DISCIPLINE.md` — Pre-code task checklist
- `scripts/ops/claude_response_validator.py` — Automated validation
- `docs/LESSONS_ENFORCED.md` — Failure prevention rules

---

*This library is machine-enforced. Non-compliant responses will be rejected.*
