# W4 Phase: L4 Service Facades

This document describes the L4 service facades created for the W4 phase (GAP-090 to GAP-136).

## Architecture Overview

The W4 facades follow a two-layer architecture:

```
L2 API Facades (app/api/*.py)
    │
    └── L4 Service Facades (app/services/*/facade.py)
            │
            └── L6 Platform (DB, external services)
```

**Key Principles:**
- L4 facades are the ONLY entry point for domain operations
- L2 APIs are thin REST projection layers (no business logic)
- All responses use `wrap_dict()` for consistent envelopes
- Singleton pattern via `get_*_facade()` accessors

## Facades Created

### MonitorsFacade (GAP-120, GAP-121)

**Location:** `app/services/monitors/facade.py`
**API:** `app/api/monitors.py`
**Prefix:** `/api/v1/monitors`

Provides health monitoring operations:
- Create/list/get/update/delete monitors
- Run health checks
- Get check history
- Status summary

**Key Classes:**
- `MonitorConfig` - Monitor configuration
- `HealthCheckResult` - Health check outcome
- `MonitorStatusSummary` - Overall status

### LimitsFacade (GAP-122)

**Location:** `app/services/limits/facade.py`
**API:** `app/api/rate_limits.py`
**Prefix:** `/api/v1/rate-limits`

Provides rate limit and quota operations:
- List/get/update rate limits
- Check limit (with auto-increment)
- Get usage summary
- Reset usage

**Note:** Distinct from PIN-LIM policy limits (`app/api/limits/`).

**Key Classes:**
- `LimitConfig` - Rate limit configuration
- `LimitCheckResult` - Check outcome (allowed/denied)
- `UsageSummary` - Aggregated usage

### ControlsFacade (GAP-123)

**Location:** `app/services/controls/facade.py`
**API:** `app/api/controls.py`
**Prefix:** `/api/v1/controls`

Provides system control operations:
- List/get/update controls
- Enable/disable controls
- Get overall status
- Killswitch and maintenance mode

**Control Types:**
- `KILLSWITCH` - Global kill switch
- `CIRCUIT_BREAKER` - API circuit breaker
- `FEATURE_FLAG` - Feature flags
- `THROTTLE` - Execution throttling
- `MAINTENANCE` - Maintenance mode

**Key Classes:**
- `ControlConfig` - Control configuration
- `ControlStatusSummary` - Overall status

### LifecycleFacade (GAP-131-136)

**Location:** `app/services/lifecycle/facade.py`
**API:** `app/api/lifecycle.py`
**Prefix:** `/api/v1/lifecycle`

Provides agent and run lifecycle operations:
- Agent: create/list/get/start/stop/terminate
- Run: create/list/get/pause/resume/cancel
- Lifecycle summary

**Agent States:**
- `CREATED` → `STARTING` → `RUNNING` → `STOPPING` → `STOPPED` → `TERMINATED`
- `ERROR` (from any state)

**Run States:**
- `PENDING` → `RUNNING` → `COMPLETED`
- `PAUSED` (from RUNNING, can resume)
- `CANCELLED` / `FAILED` (terminal)

**Key Classes:**
- `AgentLifecycle` - Agent lifecycle info
- `RunLifecycle` - Run lifecycle info
- `LifecycleSummary` - Summary statistics

## Usage

```python
# Import the singleton accessor
from app.services.monitors.facade import get_monitors_facade

# Get the facade instance
facade = get_monitors_facade()

# Use facade methods
monitors = await facade.list_monitors(tenant_id="...")
result = await facade.run_check(monitor_id="...", tenant_id="...")
```

## API Endpoints Summary

| Domain | Prefix | GAP |
|--------|--------|-----|
| Monitors | `/api/v1/monitors` | GAP-120, GAP-121 |
| Rate Limits | `/api/v1/rate-limits` | GAP-122 |
| Controls | `/api/v1/controls` | GAP-123 |
| Lifecycle | `/api/v1/lifecycle` | GAP-131-136 |

## Layer Compliance

All facades follow the layer model:

- **L2 (API)**: REST endpoints, request validation, response wrapping
- **L4 (Domain)**: Business logic, state management, audit logging
- **L6 (Platform)**: Database access, external services

**Forbidden:**
- L2 importing L4 internal modules directly
- L4 importing L1 (UI) or L5 (Workers)
- Business logic in L2

## Verification & Testing

### Test Date: 2026-01-21

### Import Tests: PASSED

All facade and API modules import correctly without errors:

```
Testing facade imports...
  monitors/facade.py: OK
  limits/facade.py: OK
  controls/facade.py: OK
  lifecycle/facade.py: OK

Testing API router imports...
  api/monitors.py: OK
  api/rate_limits.py: OK
  api/controls.py: OK
  api/lifecycle.py: OK

All imports successful!
```

### Route Registration Tests: PASSED

Main application imports successfully with all routes registered:

| Metric | Value |
|--------|-------|
| Total routes registered | 663 |
| New W4 routes added | 33 |

**W4 Routes Breakdown:**

| Domain | Route Count | Routes |
|--------|-------------|--------|
| Monitors | 8 | `/api/v1/monitors`, `/api/v1/monitors/status`, `/api/v1/monitors/{monitor_id}`, `/api/v1/monitors/{monitor_id}/check`, `/api/v1/monitors/{monitor_id}/history` |
| Rate Limits | 6 | `/api/v1/rate-limits`, `/api/v1/rate-limits/usage`, `/api/v1/rate-limits/check`, `/api/v1/rate-limits/{limit_id}`, `/api/v1/rate-limits/{limit_id}/reset` |
| Controls | 6 | `/api/v1/controls`, `/api/v1/controls/status`, `/api/v1/controls/{control_id}`, `/api/v1/controls/{control_id}/enable`, `/api/v1/controls/{control_id}/disable` |
| Lifecycle | 13 | `/api/v1/lifecycle/agents`, `/api/v1/lifecycle/agents/{agent_id}`, `/api/v1/lifecycle/agents/{agent_id}/start`, `/api/v1/lifecycle/agents/{agent_id}/stop`, `/api/v1/lifecycle/agents/{agent_id}/terminate`, `/api/v1/lifecycle/runs`, `/api/v1/lifecycle/runs/{run_id}`, `/api/v1/lifecycle/runs/{run_id}/pause`, `/api/v1/lifecycle/runs/{run_id}/resume`, `/api/v1/lifecycle/runs/{run_id}/cancel`, `/api/v1/lifecycle/summary` |

### Files Created

**L4 Service Facades:**
- `app/services/monitors/facade.py` - MonitorsFacade (GAP-120, 121)
- `app/services/monitors/__init__.py`
- `app/services/limits/facade.py` - LimitsFacade (GAP-122)
- `app/services/limits/__init__.py`
- `app/services/controls/facade.py` - ControlsFacade (GAP-123)
- `app/services/controls/__init__.py`
- `app/services/lifecycle/facade.py` - LifecycleFacade (GAP-131-136)
- `app/services/lifecycle/__init__.py`

**L2 API Routers:**
- `app/api/monitors.py` - Monitors API
- `app/api/rate_limits.py` - Rate Limits API (renamed from limits.py)
- `app/api/controls.py` - Controls API
- `app/api/lifecycle.py` - Lifecycle API

**Modified:**
- `app/main.py` - Added router imports and registrations

### Naming Notes

The rate limits API uses `/api/v1/rate-limits` (not `/api/v1/limits`) because `app/api/limits/` already exists for PIN-LIM policy limits:

| API | Purpose | Location |
|-----|---------|----------|
| Rate Limits (GAP-122) | Usage quotas, API call limits, token usage | `app/api/rate_limits.py` |
| Policy Limits (PIN-LIM) | Policy rule limits, simulation, overrides | `app/api/limits/` |

### Test Commands

To re-run verification:

```bash
cd /root/agenticverz2.0/backend

# Test facade imports
python3 -c "
from app.services.monitors.facade import get_monitors_facade
from app.services.limits.facade import get_limits_facade
from app.services.controls.facade import get_controls_facade
from app.services.lifecycle.facade import get_lifecycle_facade
print('All facade imports OK')
"

# Test API imports
python3 -c "
from app.api.monitors import router as monitors_router
from app.api.rate_limits import router as rate_limits_router
from app.api.controls import router as controls_router
from app.api.lifecycle import router as lifecycle_router
print('All API imports OK')
"

# Test full main.py (requires DATABASE_URL)
export DATABASE_URL="postgresql://test:test@localhost/test"
python3 -c "from app.main import app; print(f'Routes: {len([r for r in app.routes if hasattr(r, \"path\")])}')"
```
