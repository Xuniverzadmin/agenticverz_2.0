# alert_driver.py

**Path:** `backend/app/hoc/cus/hoc_spine/drivers/alert_driver.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            alert_driver.py
Lives in:        drivers/
Role:            Drivers
Inbound:         alert_worker.py (L5 engine)
Outbound:        none
Transaction:     Flush only (no commit)
Cross-domain:    none
Purpose:         Alert Driver (L6)
Violations:      none
```

## Purpose

Alert Driver (L6)

Pure database operations for alert queue management.
All business logic stays in L4 engine.
All HTTP delivery stays in adapter.

Operations:
- Read pending alerts from queue
- Update alert status (sent, retry, failed)
- Update incident alert_sent flag
- Queue statistics
- Enqueue new alerts
- Retry/purge operations

NO business logic:
- NO retry decision logic (L4)
- NO backoff calculation (L4)
- NO HTTP operations (adapter)

Reference: Phase-2.5A Analytics Extraction

## Import Analysis

**L7 Models:**
- `app.models.costsim_cb`

**External:**
- `sqlalchemy`
- `sqlalchemy.ext.asyncio`

## Transaction Boundary

- **Commits:** no
- **Flushes:** yes
- **Rollbacks:** no

## Functions

### `get_alert_driver(session: AsyncSession) -> AlertDriver`

Factory function to get AlertDriver instance.

## Classes

### `AlertDriver`

L6 driver for alert queue data access.

Pure database access - no business logic, no HTTP.
Transaction management is delegated to caller (L4 engine).

#### Methods

- `__init__(session: AsyncSession)` — Initialize with async database session.
- `async fetch_pending_alerts(now: datetime, batch_size: int) -> List[CostSimAlertQueueModel]` — Fetch pending alerts ready to send.
- `async fetch_queue_stats() -> Dict[str, Any]` — Fetch alert queue statistics.
- `async update_alert_sent(alert: CostSimAlertQueueModel, sent_at: datetime) -> None` — Mark alert as successfully sent.
- `async update_alert_retry(alert: CostSimAlertQueueModel, last_attempt_at: datetime, next_attempt_at: datetime, last_error: Optional[str]) -> None` — Schedule alert for retry.
- `async update_alert_failed(alert: CostSimAlertQueueModel, last_attempt_at: datetime, last_error: Optional[str]) -> None` — Mark alert as permanently failed.
- `async mark_incident_alert_sent(incident_id: str, sent_at: datetime) -> None` — Mark incident as having alert sent.
- `async insert_alert(payload: List[Dict[str, Any]], alert_type: str, circuit_breaker_name: Optional[str], incident_id: Optional[str]) -> CostSimAlertQueueModel` — Insert new alert into queue.
- `async retry_failed_alerts(max_retries: int, now: datetime) -> int` — Reset failed alerts to pending for retry.
- `async purge_old_alerts(cutoff: datetime, statuses: List[str]) -> int` — Delete old alerts from queue.

## Domain Usage

**Callers:** alert_worker.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_alert_driver
      signature: "get_alert_driver(session: AsyncSession) -> AlertDriver"
      consumers: ["orchestrator"]
  classes:
    - name: AlertDriver
      methods:
        - fetch_pending_alerts
        - fetch_queue_stats
        - update_alert_sent
        - update_alert_retry
        - update_alert_failed
        - mark_incident_alert_sent
        - insert_alert
        - retry_failed_alerts
        - purge_old_alerts
      consumers: ["orchestrator"]
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
    l7_model: ['app.models.costsim_cb']
    external: ['sqlalchemy', 'sqlalchemy.ext.asyncio']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

