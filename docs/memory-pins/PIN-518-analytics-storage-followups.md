# PIN-518: Analytics Storage Follow-ups

**Status:** COMPLETE
**Date:** 2026-02-03
**Predecessor:** PIN-517 (cus_vault Authority Refactor)
**Reference:** Analytics Storage Wiring Audit

---

## Problem Statement

Audit of analytics storage wiring revealed 3 authority gaps:

1. **Gap 1:** L2 API (`costsim.py`) calling L6 driver directly (L2→L6 bypass)
2. **Gap 2:** Provenance and Canary report functions shared a single driver (authority blur)
3. **Gap 3:** Canary report write had no artifact-before-DB invariant guard

---

## Gap Analysis & Fixes

### Gap 1: L2→L6 Bypass

**Problem:** `/canary/reports` endpoint in `api/cus/analytics/costsim.py` was importing and calling `provenance_driver` directly, bypassing L4 authority.

**Architecture Violation:**
```
L2 API → L6 Driver (WRONG)
```

**Correct Flow:**
```
L2 API → L4 Handler → L5 Engine/L6 Driver (CORRECT)
```

**Fix:** Route through L4 handler via OperationRegistry.

| Layer | File | Change |
|-------|------|--------|
| L2 | `api/cus/analytics/costsim.py` | Calls `registry.execute("analytics.canary_reports", ctx)` |
| L4 | `hoc_spine/orchestrator/handlers/analytics_handler.py` | Added `CanaryReportHandler` |

### Gap 2: Authority Blur (Provenance + Canary)

**Problem:** `provenance_driver.py` handled both:
- Provenance logging (immutable audit trail)
- Canary report persistence (deployable artifact storage)

These are distinct concerns with different lifecycles and access patterns.

**Fix:** Split into dedicated drivers.

| File | Purpose |
|------|---------|
| `L6_drivers/provenance_driver.py` | Provenance logging only |
| `L6_drivers/canary_report_driver.py` *(NEW)* | Canary report persistence |

**canary_report_driver.py Interface:**
```python
async def write_canary_report(session: AsyncSession, report: CanaryReport) -> str
async def query_canary_reports(session: AsyncSession, tenant_id: str, filters: dict) -> List[CanaryReportRow]
async def get_canary_report_by_run_id(session: AsyncSession, tenant_id: str, run_id: str) -> Optional[CanaryReportRow]
```

### Gap 3: Missing Invariant Guard

**Problem:** `canary_engine.py` could persist reports to database without artifacts being written first. This violates the artifact-before-DB invariant (artifacts are the source of truth; DB is index).

**Risk:** Database could contain references to non-existent artifacts.

**Fix:** Added explicit invariant check in `_persist_report_to_db()`.

```python
async def _persist_report_to_db(self, report: CanaryReport) -> None:
    if self.config.save_artifacts and not report.artifact_paths:
        raise RuntimeError(
            "Canary artifacts missing; refusing DB write. "
            "Write artifacts first via _write_artifacts()."
        )
    # ... proceed with DB write
```

---

## Files Changed

| Action | File |
|--------|------|
| MODIFY | `app/hoc/api/cus/analytics/costsim.py` |
| MODIFY | `app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_handler.py` |
| CREATE | `app/hoc/cus/analytics/L6_drivers/canary_report_driver.py` |
| MODIFY | `app/hoc/cus/analytics/L5_engines/canary_engine.py` |

---

## L4 Handler Registration

**File:** `hoc_spine/orchestrator/handlers/analytics_handler.py`

```python
class CanaryReportHandler:
    """L4 handler for canary report operations."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L6_drivers.canary_report_driver import (
            query_canary_reports,
            get_canary_report_by_run_id,
        )

        method = ctx.params.get("method", "list")

        if method == "list":
            reports = await query_canary_reports(
                ctx.session,
                ctx.tenant_id,
                ctx.params.get("filters", {}),
            )
            return OperationResult(success=True, data={"reports": reports})

        elif method == "get":
            run_id = ctx.params.get("run_id")
            report = await get_canary_report_by_run_id(
                ctx.session,
                ctx.tenant_id,
                run_id,
            )
            return OperationResult(success=True, data={"report": report})

        return OperationResult(success=False, error="Unknown method")
```

**Registration:** Operation `analytics.canary_reports` → `CanaryReportHandler`

---

## Updated Analytics L4 Operations

| Operation | Handler Class | Target |
|-----------|--------------|--------|
| analytics.query | AnalyticsQueryHandler | AnalyticsFacade |
| analytics.detection | AnalyticsDetectionHandler | DetectionFacade |
| analytics.canary_reports | CanaryReportHandler | canary_report_driver *(NEW)* |

---

## Verification

```bash
# 1. Verify canary_report_driver exists and imports
PYTHONPATH=. python3 -c "
from app.hoc.cus.analytics.L6_drivers.canary_report_driver import (
    write_canary_report,
    query_canary_reports,
    get_canary_report_by_run_id,
)
print('OK: canary_report_driver imports clean')
"

# 2. Verify L4 handler registration
PYTHONPATH=. python3 -c "
from app.hoc.cus.hoc_spine.orchestrator.handlers.analytics_handler import CanaryReportHandler
print('OK: CanaryReportHandler exists')
"

# 3. Verify invariant guard in canary_engine
PYTHONPATH=. python3 -c "
import inspect
from app.hoc.cus.analytics.L5_engines.canary_engine import CanaryEngine
source = inspect.getsource(CanaryEngine)
assert 'refusing DB write' in source, 'Invariant guard missing'
print('OK: Artifact-before-DB invariant guard present')
"
```

---

## Architecture Invariants Enforced

1. **L2→L4→L5/L6 Flow:** All L2 API endpoints route through L4 handlers
2. **Single Responsibility Drivers:** Each L6 driver has one concern
3. **Artifact-Before-DB:** Artifacts written before database indexing
4. **OperationRegistry Routing:** All cross-layer calls via registry dispatch
