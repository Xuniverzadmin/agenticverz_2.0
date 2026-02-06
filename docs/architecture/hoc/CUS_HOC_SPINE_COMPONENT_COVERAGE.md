# CUS L2 → hoc_spine Component Coverage (Evidence Scan)

**Scope:** `backend/app/hoc/api/cus/**` (APIRouter files only)  
**Date:** 2026-02-06  
**Purpose:** Reality map of which hoc_spine components are referenced by L2 per customer domain.

---

## Coverage by Domain

**account** (1 file)
- `get_operation_registry`: 1 (100%)
- `OperationContext`: 1 (100%)
- `get_session_dep`: 1 (100%)

**activity** (1 file)
- `get_operation_registry`: 1 (100%)
- `OperationContext`: 1 (100%)
- `get_session_dep`: 1 (100%)

**agent** (4 files)
- `get_sync_session_dep`: 2 (50.0%)
- `sql_text`: 2 (50.0%)

**analytics** (4 files)
- `get_operation_registry`: 1 (25.0%)
- `OperationContext`: 1 (25.0%)
- `get_session_dep`: 1 (25.0%)
- `get_async_session_context`: 2 (50.0%)
- `sql_text`: 2 (50.0%)

**api_keys** (2 files)
- No hoc_spine components detected in L2 files.

**general** (5 files)
- `get_async_session_context`: 2 (40.0%)
- `sql_text`: 1 (20.0%)

**incidents** (2 files)
- `get_operation_registry`: 1 (50.0%)
- `OperationContext`: 1 (50.0%)
- `get_session_dep`: 1 (50.0%)
- `get_sync_session_dep`: 1 (50.0%)
- `sql_text`: 2 (100.0%)

**integrations** (4 files)
- `get_operation_registry`: 2 (50.0%)
- `OperationContext`: 2 (50.0%)
- `get_session_dep`: 1 (25.0%)
- `get_sync_session_dep`: 1 (25.0%)
- `sql_text`: 1 (25.0%)

**logs** (4 files)
- `get_sync_session_dep`: 2 (50.0%)
- `get_async_session_context`: 1 (25.0%)
- `sql_text`: 2 (50.0%)
- `get_integrations_driver_bridge`: 1 (25.0%)

**ops** (1 file)
- `get_operation_registry`: 1 (100%)
- `OperationContext`: 1 (100%)
- `get_session_dep`: 1 (100%)

**overview** (1 file)
- `get_operation_registry`: 1 (100%)
- `OperationContext`: 1 (100%)
- `get_session_dep`: 1 (100%)

**policies** (38 files)
- `get_operation_registry`: 24 (63.2%)
- `OperationContext`: 24 (63.2%)
- `get_session_dep`: 12 (31.6%)
- `get_sync_session_dep`: 5 (13.2%)
- `get_async_session_context`: 4 (10.5%)
- `sql_text`: 9 (23.7%)
- `get_policies_engine_bridge`: 3 (7.9%)
- `get_account_bridge`: 1 (2.6%)

**recovery** (2 files)
- `get_sync_session_dep`: 2 (100%)
- `sql_text`: 1 (50.0%)
- `get_policies_bridge`: 2 (100%)

---

## Overall Coverage (69 L2 files)

- `get_operation_registry`: 32 (46.4%)
- `OperationContext`: 32 (46.4%)
- `get_session_dep`: 19 (27.5%)
- `get_sync_session_dep`: 13 (18.8%)
- `get_async_session_context`: 9 (13.0%)
- `sql_text`: 20 (29.0%)
- `get_policies_bridge`: 2 (2.9%)
- `get_policies_engine_bridge`: 3 (4.3%)
- `get_account_bridge`: 1 (1.4%)
- `get_integrations_bridge`: 0 (0.0%)
- `get_integrations_driver_bridge`: 1 (1.4%)
