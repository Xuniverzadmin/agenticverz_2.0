# CUS L2 → hoc_spine Component Coverage (Evidence Scan)

**Scope:** `backend/app/hoc/api/cus/**` (APIRouter token files only)  
**Date:** 2026-02-07  
**Purpose:** Reality map of which hoc_spine components are referenced by CUS L2, grouped by canonical domain folder.

**Audience cleansing note:** non-domain CUS surfaces (`general/`, `agent/`, `ops/`, `recovery/`) were re-homed to `int/` or `fdr/`. This report covers **only** canonical CUS domains.

---

## Canonical CUS Domains (10)

`overview`, `activity`, `incidents`, `policies`, `controls`, `logs`, `analytics`, `integrations`, `api_keys`, `account`

---

## Coverage by Domain Folder

**account** (1 file)
- `registry.execute`: 1 (100.0%)
- `get_operation_registry`: 1 (100.0%)
- `OperationContext`: 1 (100.0%)
- `get_session_dep`: 1 (100.0%)

**activity** (1 file)
- `registry.execute`: 1 (100.0%)
- `get_operation_registry`: 1 (100.0%)
- `OperationContext`: 1 (100.0%)
- `get_session_dep`: 1 (100.0%)

**analytics** (4 files)
- `registry.execute`: 3 (75.0%)
- `get_operation_registry`: 3 (75.0%)
- `OperationContext`: 3 (75.0%)
- `get_session_dep`: 2 (50.0%)
- `get_async_session_context`: 1 (25.0%)

**api_keys** (2 files)
- No hoc_spine components detected in these L2 files.

**controls** (1 file)
- `registry.execute`: 1 (100.0%)
- `get_operation_registry`: 1 (100.0%)
- `OperationContext`: 1 (100.0%)

**incidents** (2 files)
- `registry.execute`: 2 (100.0%)
- `get_operation_registry`: 2 (100.0%)
- `OperationContext`: 2 (100.0%)
- `get_session_dep`: 1 (50.0%)
- `get_sync_session_dep`: 1 (50.0%)

**integrations** (4 files)
- `registry.execute`: 3 (75.0%)
- `get_operation_registry`: 3 (75.0%)
- `OperationContext`: 3 (75.0%)
- `get_session_dep`: 1 (25.0%)
- `get_sync_session_dep`: 1 (25.0%)

**logs** (4 files)
- `registry.execute`: 2 (50.0%)
- `get_operation_registry`: 2 (50.0%)
- `OperationContext`: 2 (50.0%)
- `get_session_dep`: 1 (25.0%)
- `get_sync_session_dep`: 2 (50.0%)
- `get_async_session_context`: 1 (25.0%)
- `get_integrations_driver_bridge`: 1 (25.0%)

**overview** (1 file)
- `registry.execute`: 1 (100.0%)
- `get_operation_registry`: 1 (100.0%)
- `OperationContext`: 1 (100.0%)
- `get_session_dep`: 1 (100.0%)

**policies** (37 files)
- `registry.execute`: 29 (78.4%)
- `get_operation_registry`: 29 (78.4%)
- `OperationContext`: 29 (78.4%)
- `get_session_dep`: 13 (35.1%)
- `get_sync_session_dep`: 4 (10.8%)
- `get_async_session_context`: 4 (10.8%)
- `get_account_bridge`: 1 (2.7%)
- `get_policies_engine_bridge`: 3 (8.1%)

---

## Overall Coverage (All 57 CUS L2 token files)

| Component | Files | % |
|----------|------:|---:|
| `registry.execute` | 43 | 75.4% |
| `get_operation_registry` | 43 | 75.4% |
| `OperationContext` | 43 | 75.4% |
| `get_session_dep` | 21 | 36.8% |
| `get_sync_session_dep` | 8 | 14.0% |
| `get_async_session_context` | 6 | 10.5% |
| `get_integrations_driver_bridge` | 1 | 1.8% |
| `get_account_bridge` | 1 | 1.8% |
| `get_policies_engine_bridge` | 3 | 5.3% |

