# control_registry.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/control_registry.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            control_registry.py
Lives in:        services/
Role:            Services
Inbound:         services/soc2/mapper.py, services/export_bundle_service.py
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Module: control_registry
Violations:      none
```

## Purpose

Module: control_registry
Purpose: Registry of SOC2 Trust Service Criteria controls.

SOC2 Trust Service Categories:
    - CC (Common Criteria): Security-related controls
    - A (Availability): System availability controls
    - PI (Processing Integrity): Processing accuracy controls
    - C (Confidentiality): Data confidentiality controls
    - P (Privacy): Privacy-related controls

Key Controls for AI Agent Governance:
    - CC7.x: System Operations (Incident Response)
    - CC6.x: Logical and Physical Access Controls
    - CC8.x: Change Management
    - PI1.x: Processing Integrity
    - A1.x: Availability

Exports:
    - SOC2Category: Enum of trust service categories
    - SOC2ComplianceStatus: Enum of compliance states
    - SOC2Control: Control definition
    - SOC2ControlMapping: Mapping with evidence
    - SOC2ControlRegistry: Registry singleton

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_control_registry() -> SOC2ControlRegistry`

Get or create the singleton control registry.

## Classes

### `SOC2Category(str, Enum)`

SOC2 Trust Service Categories.

### `SOC2ComplianceStatus(str, Enum)`

Compliance status for a control mapping.

### `SOC2Control`

SOC2 Trust Service Criteria control definition.

Represents a single SOC2 control with its ID, name, description,
and the category it belongs to.

#### Methods

- `__post_init__()` — Set default evidence types based on control category.

### `SOC2ControlMapping`

Mapping of incident/evidence to a SOC2 control.

Contains the control, the evidence provided, and compliance status.

#### Methods

- `to_dict() -> dict[str, Any]` — Convert to dictionary for API responses (GAP-025).

### `SOC2ControlRegistry`

Registry of SOC2 Trust Service Criteria controls.

Provides lookup and management of SOC2 controls relevant to
AI agent governance and incident response.

GAP-025: Complete SOC2 control objective mapping.

#### Methods

- `__init__()` — Initialize registry with all controls.
- `_register_all_controls() -> None` — Register all SOC2 controls relevant to AI governance.
- `_register_incident_response_controls() -> None` — Register CC7.x Incident Response controls.
- `_register_access_controls() -> None` — Register CC6.x Access Controls.
- `_register_change_management_controls() -> None` — Register CC8.x Change Management controls.
- `_register_processing_integrity_controls() -> None` — Register PI1.x Processing Integrity controls.
- `_register_availability_controls() -> None` — Register A1.x Availability controls.
- `_register_communication_controls() -> None` — Register CC2.x Communication controls.
- `_register_risk_controls() -> None` — Register CC9.x Risk controls.
- `get_control(control_id: str) -> Optional[SOC2Control]` — Get a control by ID.
- `get_controls_by_category(category: SOC2Category) -> list[SOC2Control]` — Get all controls in a category.
- `get_controls_by_prefix(prefix: str) -> list[SOC2Control]` — Get all controls with a given prefix (e.g., 'CC7').
- `get_all_controls() -> list[SOC2Control]` — Get all registered controls.
- `get_incident_response_controls() -> list[SOC2Control]` — Get all incident response controls (CC7.x).

## Domain Usage

**Callers:** services/soc2/mapper.py, services/export_bundle_service.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_control_registry
      signature: "get_control_registry() -> SOC2ControlRegistry"
      consumers: ["orchestrator"]
  classes:
    - name: SOC2Category
      methods: []
      consumers: ["orchestrator"]
    - name: SOC2ComplianceStatus
      methods: []
      consumers: ["orchestrator"]
    - name: SOC2Control
      methods:
      consumers: ["orchestrator"]
    - name: SOC2ControlMapping
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: SOC2ControlRegistry
      methods:
        - get_control
        - get_controls_by_category
        - get_controls_by_prefix
        - get_all_controls
        - get_incident_response_controls
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

