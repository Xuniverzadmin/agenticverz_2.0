# alert_delivery.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/alert_delivery.py`  
**Layer:** L5 — HOC Spine (Services)  
**Component:** Services

---

## Placement Card

```
File:            alert_delivery.py
Lives in:        services/
Role:            Services
Inbound:         alert_worker.py (L4 engine)
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Alert Delivery Adapter (L2)
Violations:      none
```

## Purpose

Alert Delivery Adapter (L2)

Pure HTTP delivery to Alertmanager.
All business logic stays in L4 engine.
All database operations stay in L6 driver.

Operations:
- Send alert payload to Alertmanager
- Handle HTTP errors and timeouts
- Report delivery result

NO business logic:
- NO retry decisions (L4)
- NO status updates (L6)
- NO queue management (L6)

Reference: Phase-2.5A Analytics Extraction

## Import Analysis

**External:**
- `httpx`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_alert_delivery_adapter(alertmanager_url: Optional[str], timeout_seconds: float) -> AlertDeliveryAdapter`

Factory function to get AlertDeliveryAdapter instance.

## Classes

### `DeliveryResult`

Result of alert delivery attempt.

### `AlertDeliveryAdapter`

Adapter for HTTP alert delivery.

Pure HTTP operations - no business logic, no database.

#### Methods

- `__init__(alertmanager_url: Optional[str], timeout_seconds: float)` — Initialize adapter with Alertmanager configuration.
- `async _get_client() -> httpx.AsyncClient` — Get or create HTTP client.
- `async close() -> None` — Close HTTP client.
- `async send_alert(payload: List[Dict[str, Any]]) -> DeliveryResult` — Send alert payload to Alertmanager.

## Domain Usage

**Callers:** alert_worker.py (L4 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_alert_delivery_adapter
      signature: "get_alert_delivery_adapter(alertmanager_url: Optional[str], timeout_seconds: float) -> AlertDeliveryAdapter"
      consumers: ["orchestrator"]
  classes:
    - name: DeliveryResult
      methods: []
      consumers: ["orchestrator"]
    - name: AlertDeliveryAdapter
      methods:
        - close
        - send_alert
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
    external: ['httpx']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

