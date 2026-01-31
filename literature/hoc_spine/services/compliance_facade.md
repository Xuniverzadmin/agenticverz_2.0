# compliance_facade.py

**Path:** `backend/app/hoc/hoc_spine/services/compliance_facade.py`  
**Layer:** L4 — HOC Spine (Facade)  
**Component:** Services

---

## Placement Card

```
File:            compliance_facade.py
Lives in:        services/
Role:            Services
Inbound:         L2 compliance.py API, SDK
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Compliance Facade (L4 Domain Logic)
Violations:      none
```

## Purpose

Compliance Facade (L4 Domain Logic)

This facade provides the external interface for compliance verification operations.
All compliance APIs MUST use this facade instead of directly importing
internal compliance modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes compliance verification logic
- Provides unified access to compliance checks and reports
- Single point for audit emission

L2 API Routes (GAP-103):
- POST /api/v1/compliance/verify (run compliance verification)
- GET /api/v1/compliance/reports (list compliance reports)
- GET /api/v1/compliance/reports/{id} (get compliance report)
- GET /api/v1/compliance/rules (list compliance rules)
- GET /api/v1/compliance/status (compliance status)

Usage:
    from app.services.compliance.facade import get_compliance_facade

    facade = get_compliance_facade()

    # Run compliance verification
    result = await facade.verify_compliance(tenant_id="...", scope="all")

    # List compliance reports
    reports = await facade.list_reports(tenant_id="...")

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_compliance_facade() -> ComplianceFacade`

Get the compliance facade instance.

This is the recommended way to access compliance operations
from L2 APIs and the SDK.

Returns:
    ComplianceFacade instance

## Classes

### `ComplianceScope(str, Enum)`

Compliance verification scope.

### `ComplianceStatus(str, Enum)`

Compliance status.

### `ComplianceRule`

Compliance rule definition.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `ComplianceViolation`

A compliance violation.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `ComplianceReport`

Compliance verification report.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `ComplianceStatusInfo`

Overall compliance status.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `ComplianceFacade`

Facade for compliance verification operations.

This is the ONLY entry point for L2 APIs and SDK to interact with
compliance services.

Layer: L4 (Domain Logic)
Callers: compliance.py (L2), aos_sdk

#### Methods

- `__init__()` — Initialize facade.
- `_init_default_rules() -> Dict[str, ComplianceRule]` — Initialize default compliance rules.
- `async verify_compliance(tenant_id: str, scope: str, actor: Optional[str]) -> ComplianceReport` — Run compliance verification.
- `_check_rule_compliance(tenant_id: str, rule: ComplianceRule) -> bool` — Check if tenant is compliant with a rule.
- `async list_reports(tenant_id: str, scope: Optional[str], status: Optional[str], limit: int, offset: int) -> List[ComplianceReport]` — List compliance reports.
- `async get_report(report_id: str, tenant_id: str) -> Optional[ComplianceReport]` — Get a specific compliance report.
- `async list_rules(scope: Optional[str], enabled_only: bool) -> List[ComplianceRule]` — List compliance rules.
- `async get_rule(rule_id: str) -> Optional[ComplianceRule]` — Get a specific compliance rule.
- `async get_compliance_status(tenant_id: str) -> ComplianceStatusInfo` — Get overall compliance status.

## Domain Usage

**Callers:** L2 compliance.py API, SDK

## Export Contract

```yaml
exports:
  functions:
    - name: get_compliance_facade
      signature: "get_compliance_facade() -> ComplianceFacade"
      consumers: ["orchestrator"]
  classes:
    - name: ComplianceScope
      methods: []
      consumers: ["orchestrator"]
    - name: ComplianceStatus
      methods: []
      consumers: ["orchestrator"]
    - name: ComplianceRule
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: ComplianceViolation
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: ComplianceReport
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: ComplianceStatusInfo
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: ComplianceFacade
      methods:
        - verify_compliance
        - list_reports
        - get_report
        - list_rules
        - get_rule
        - get_compliance_status
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

