# cross_domain.py

**Path:** `backend/app/hoc/cus/hoc_spine/drivers/cross_domain.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            cross_domain.py
Lives in:        drivers/
Role:            Drivers
Inbound:         cost_anomaly_detector, budget services, worker runtime
Outbound:        none
Transaction:     Flush only (no commit)
Cross-domain:    none
Purpose:         Cross-Domain Governance Functions (Mandatory)
Violations:      none
```

## Purpose

Cross-Domain Governance Functions (Mandatory)

PIN: design/CROSS_DOMAIN_GOVERNANCE.md

These functions implement mandatory governance for customer-facing paths.
They MUST succeed or raise GovernanceError. Silent failures are forbidden.

DOCTRINE:
- Rule 1: Governance must throw
- Rule 2: No optional dependencies
- Rule 3: Learning is downstream only

DOMAINS:
- Analytics → Incidents: Cost anomalies MUST create incidents
- Policies ↔ Analytics: Limit breaches MUST be recorded

COROLLARY: GovernanceError must surface - never catch and ignore.

## Import Analysis

**L7 Models:**
- `app.models.killswitch`
- `app.models.policy_control_plane`

**External:**
- `sqlalchemy.ext.asyncio`
- `sqlmodel`
- `app.errors.governance`
- `app.metrics`
- `sqlalchemy`

## Transaction Boundary

- **Commits:** no
- **Flushes:** yes
- **Rollbacks:** no

## Functions

### `utc_now() -> datetime`

Return timezone-aware UTC datetime.

### `generate_uuid() -> str`

Generate a UUID string.

### `async create_incident_from_cost_anomaly(session: AsyncSession, tenant_id: str, anomaly_id: str, anomaly_type: str, severity: str, current_value_cents: int, expected_value_cents: int, entity_type: Optional[str], entity_id: Optional[str], description: Optional[str]) -> str`

Create an incident from a cost anomaly. MANDATORY.

This function MUST succeed or raise GovernanceError.
It cannot be skipped based on optional configuration.

Args:
    session: Database session
    tenant_id: Tenant scope
    anomaly_id: ID of the cost anomaly
    anomaly_type: Type of anomaly (BUDGET_EXCEEDED, USER_SPIKE, etc.)
    severity: Anomaly severity (CRITICAL, HIGH, MEDIUM, LOW)
    current_value_cents: Actual cost in cents
    expected_value_cents: Expected cost in cents
    entity_type: Optional entity type (user, tenant, etc.)
    entity_id: Optional entity ID
    description: Optional description

Returns:
    incident_id

Raises:
    GovernanceError: If incident cannot be created

Example:
    incident_id = await create_incident_from_cost_anomaly(
        session=session,
        tenant_id="tenant-123",
        anomaly_id="anomaly-456",
        anomaly_type="BUDGET_EXCEEDED",
        severity="HIGH",
        current_value_cents=15000,
        expected_value_cents=10000,
    )

### `async record_limit_breach(session: AsyncSession, tenant_id: str, limit_id: str, breach_type: str, value_at_breach: Decimal, limit_value: Decimal, run_id: Optional[str], incident_id: Optional[str], details: Optional[dict]) -> str`

Record a limit breach. MANDATORY.

This function MUST succeed or raise GovernanceError.
Every budget/rate/threshold breach MUST be recorded.

Args:
    session: Database session
    tenant_id: Tenant scope
    limit_id: ID of the limit that was breached
    breach_type: Type of breach (BREACHED, EXHAUSTED, THROTTLED, VIOLATED)
    value_at_breach: The value that caused the breach
    limit_value: The limit value that was exceeded
    run_id: Optional ID of the run that caused the breach
    incident_id: Optional ID of resulting incident
    details: Optional additional context

Returns:
    breach_id

Raises:
    GovernanceError: If breach cannot be recorded

Example:
    breach_id = await record_limit_breach(
        session=session,
        tenant_id="tenant-123",
        limit_id="limit-456",
        breach_type="BREACHED",
        value_at_breach=Decimal("150.00"),
        limit_value=Decimal("100.00"),
        run_id="run-789",
    )

### `async table_exists(session: AsyncSession, table_name: str) -> bool`

Check if a table exists in the database.

Used by Overview for defensive queries that should degrade gracefully.

Args:
    session: Database session
    table_name: Name of the table to check

Returns:
    True if table exists, False otherwise

### `create_incident_from_cost_anomaly_sync(session: Session, tenant_id: str, anomaly_id: str, anomaly_type: str, severity: str, current_value_cents: int, expected_value_cents: int, entity_type: Optional[str], entity_id: Optional[str], description: Optional[str]) -> str`

Create an incident from a cost anomaly (SYNC version). MANDATORY.

Same as create_incident_from_cost_anomaly but for sync sessions.
See async version for full documentation.

Raises:
    GovernanceError: If incident cannot be created

### `record_limit_breach_sync(session: Session, tenant_id: str, limit_id: str, breach_type: str, value_at_breach: Decimal, limit_value: Decimal, run_id: Optional[str], incident_id: Optional[str], details: Optional[dict]) -> str`

Record a limit breach (SYNC version). MANDATORY.

Same as record_limit_breach but for sync sessions.
See async version for full documentation.

Raises:
    GovernanceError: If breach cannot be recorded

## Domain Usage

**Callers:** cost_anomaly_detector, budget services, worker runtime

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
      consumers: ["orchestrator"]
    - name: generate_uuid
      signature: "generate_uuid() -> str"
      consumers: ["orchestrator"]
    - name: create_incident_from_cost_anomaly
      signature: "async create_incident_from_cost_anomaly(session: AsyncSession, tenant_id: str, anomaly_id: str, anomaly_type: str, severity: str, current_value_cents: int, expected_value_cents: int, entity_type: Optional[str], entity_id: Optional[str], description: Optional[str]) -> str"
      consumers: ["orchestrator"]
    - name: record_limit_breach
      signature: "async record_limit_breach(session: AsyncSession, tenant_id: str, limit_id: str, breach_type: str, value_at_breach: Decimal, limit_value: Decimal, run_id: Optional[str], incident_id: Optional[str], details: Optional[dict]) -> str"
      consumers: ["orchestrator"]
    - name: table_exists
      signature: "async table_exists(session: AsyncSession, table_name: str) -> bool"
      consumers: ["orchestrator"]
    - name: create_incident_from_cost_anomaly_sync
      signature: "create_incident_from_cost_anomaly_sync(session: Session, tenant_id: str, anomaly_id: str, anomaly_type: str, severity: str, current_value_cents: int, expected_value_cents: int, entity_type: Optional[str], entity_id: Optional[str], description: Optional[str]) -> str"
      consumers: ["orchestrator"]
    - name: record_limit_breach_sync
      signature: "record_limit_breach_sync(session: Session, tenant_id: str, limit_id: str, breach_type: str, value_at_breach: Decimal, limit_value: Decimal, run_id: Optional[str], incident_id: Optional[str], details: Optional[dict]) -> str"
      consumers: ["orchestrator"]
  classes: []
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.services.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: ['app.models.killswitch', 'app.models.policy_control_plane']
    external: ['sqlalchemy.ext.asyncio', 'sqlmodel', 'app.errors.governance', 'app.metrics', 'sqlalchemy']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

