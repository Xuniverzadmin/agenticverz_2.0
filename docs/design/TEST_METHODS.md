# AOS Test Methods

**Status:** ACTIVE
**Last Updated:** 2026-01-18
**Reference:** PIN-443, SDSR_SYSTEM_CONTRACT.md

---

## Overview

AOS uses a multi-layered testing strategy that ensures system correctness from unit tests through end-to-end validation. The core principle is:

> **Scenarios inject causes. Engines create effects. UI reveals truth.**

---

## Test Method Taxonomy

| Method | Layer | Purpose | Scope |
|--------|-------|---------|-------|
| Unit Tests | L8 | Function correctness | Single function/class |
| Integration Tests (LIT) | L8 | Cross-layer seams | L2↔L3, L2↔L6 |
| Browser Integration Tests (BIT) | L8 | UI page rendering | L1 pages |
| SDSR Scenarios | L8 | End-to-end realization | Full system |
| Preflight Checks | L8 | Pre-merge validation | CI gates |

---

## 1. SDSR (Scenario-Driven System Realization)

### What is SDSR?

SDSR is the primary E2E testing methodology for AOS. It validates that the system behaves correctly by:

1. **Injecting causes** (runs, failures, thresholds)
2. **Observing effects** (incidents, traces, policy proposals)
3. **Verifying invariants** (response shapes, data consistency)

### SDSR Pipeline

```
Scenario YAML (Human Intent)
        ↓
inject_synthetic.py --wait
        ↓
Real System Execution (Workers, Engines)
        ↓
SDSR_OBSERVATION_*.json (Evidence)
        ↓
AURORA_L2_apply_sdsr_observations.py
        ↓
Capability Status: DECLARED → OBSERVED
```

### Scenario Types

| Type | inject.type | Purpose |
|------|-------------|---------|
| API Observation | `api_call` | Verify endpoint responses |
| Run Injection | `create_run` | Trigger worker execution |
| State Injection | `create_run` + `status: failed` | Test failure paths without execution |

### SDSR Execution Modes

#### Mode 1: WORKER_EXECUTION

```yaml
steps:
  - step_id: INJECT-FAILURE
    action: create_run
    data:
      goal: "Test failure handling"
      failure_code: EXECUTION_TIMEOUT
      failure_message: "Simulated timeout"
```

- Creates run with `status: queued`
- Worker picks up and executes
- Worker fails with synthetic trigger
- IncidentEngine reacts to completion

#### Mode 2: STATE_INJECTION

```yaml
steps:
  - step_id: INJECT-FAILED-STATE
    action: create_run
    data:
      goal: "Test failed run display"
      status: failed
      failure_message: "BUDGET_EXCEEDED: Resource limit"
```

- Creates run with `status: failed` directly
- Worker ignores (terminal state)
- IncidentEngine triggered by post-injection hook

### Attribution in SDSR (PIN-443)

All SDSR-injected runs comply with attribution rules:

```yaml
# Default (SYSTEM actor)
steps:
  - step_id: INJECT-RUN
    action: create_run
    data:
      goal: "System-initiated test"
      # actor_type defaults to SYSTEM
      # origin_system_id defaults to sdsr-inject-synthetic

# Explicit HUMAN actor
steps:
  - step_id: INJECT-HUMAN-RUN
    action: create_run
    data:
      goal: "User-initiated test"
      actor_type: HUMAN
      actor_id: "test-user-001"
      origin_system_id: "customer-console"

# SERVICE actor
steps:
  - step_id: INJECT-SERVICE-RUN
    action: create_run
    data:
      goal: "Service-initiated test"
      actor_type: SERVICE
      origin_system_id: "worker-process-001"
```

### Running SDSR Scenarios

```bash
# Dry run (preview writes)
python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml --dry-run

# Execute and wait for completion
python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml --wait

# Cleanup synthetic data
python inject_synthetic.py --scenario scenarios/SDSR-E2E-001.yaml --cleanup
```

### SDSR Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (execution + truth materialized) |
| 1 | Validation failure (schema, missing fields) |
| 2 | Truth not materialized (execution terminal but effects missing) |
| 3 | Execution not terminal (timeout) |
| 4 | Scenario invalid (preconditions failed) |
| 5 | Internal injector error |
| 7 | Identity reuse violation (run_id already exists) |

---

## 2. Unit Tests

### Location

```
backend/tests/unit/
```

### Conventions

- One test file per module: `test_<module>.py`
- Use pytest fixtures for setup
- Mock external dependencies (DB, Redis, LLMs)

### Example

```python
# backend/tests/unit/test_attribution.py
import pytest
from aos_sdk.aos_sdk_attribution import validate_attribution, AttributionContext

def test_system_attribution_valid():
    ctx = AttributionContext(
        agent_id="test-agent",
        actor_type="SYSTEM",
        origin_system_id="unit-test",
    )
    # Should not raise
    validate_attribution(ctx)

def test_human_attribution_requires_actor_id():
    ctx = AttributionContext(
        agent_id="test-agent",
        actor_type="HUMAN",
        origin_system_id="unit-test",
        actor_id=None,  # Missing!
    )
    with pytest.raises(AttributionError):
        validate_attribution(ctx)
```

### Running Unit Tests

```bash
cd backend
pytest tests/unit/ -v
```

---

## 3. Integration Tests (LIT)

### Location

```
backend/tests/lit/
```

### Purpose

Test cross-layer seams:
- L2↔L3 (API to Adapter)
- L2↔L6 (API to Platform)

### Example

```python
# backend/tests/lit/test_activity_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_activity_runs_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/activity/runs",
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
```

---

## 4. Browser Integration Tests (BIT)

### Location

```
website/app-shell/tests/bit/
```

### Purpose

Validate UI pages render correctly and consume projections.

### Framework

Playwright for browser automation.

---

## 5. Preflight Checks

### Location

```
scripts/preflight/
```

### Purpose

Pre-merge validation gates that run in CI.

### Key Checks

| Script | Purpose |
|--------|---------|
| `check_activity_domain.py` | Activity domain contract compliance |
| `check_auth_context.sh` | Auth configuration validation |
| `truth_preflight.sh` | S1-S6 truth gates |
| `run_all_checks.sh` | Orchestrator for all preflight checks |

### Running Preflight

```bash
./scripts/preflight/run_all_checks.sh
```

---

## 6. Test Database Authority

### Rule: DB-AUTH-001

Tests that require canonical truth MUST use Neon (authoritative database).

```bash
# Correct: Use Neon for SDSR
DB_AUTHORITY=neon python inject_synthetic.py --scenario ...

# Correct: Use local for unit tests
pytest tests/unit/ --db-url=postgresql://localhost/test
```

### Never

- Infer database from data age
- Switch databases mid-test
- Query Docker DB for canonical truth

---

## 7. Capability Validation

### Capability Lifecycle

```
DECLARED → OBSERVED → TRUSTED → DEPRECATED
```

| Status | Meaning | Panel State |
|--------|---------|-------------|
| DECLARED | Code exists, not validated | Disabled |
| OBSERVED | SDSR validation passed | Enabled |
| TRUSTED | Production-proven | Enabled |
| DEPRECATED | Being removed | Hidden |

### Promoting Capabilities

```bash
# 1. Create SDSR scenario
# 2. Run scenario
python inject_synthetic.py --scenario scenarios/SDSR-CAP-001.yaml --wait

# 3. Apply observation
python AURORA_L2_apply_sdsr_observations.py --observation observations/SDSR_OBSERVATION_*.json

# 4. Verify status changed
cat backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_<cap>.yaml
```

---

## 8. Test Principles (P1-P6)

| Principle | Rule |
|-----------|------|
| P1 | Real scenarios against real infrastructure first |
| P2 | Real LLMs, real databases, no simulations |
| P3 | Full data propagation verification |
| P4 | O-level (O1-O4) propagation verification |
| P5 | Human semantic verification required |
| P6 | Localhost fallback only when Neon blocked |

---

## 9. Quick Reference

### Test Commands

```bash
# Unit tests
cd backend && pytest tests/unit/ -v

# Integration tests
cd backend && pytest tests/lit/ -v

# SDSR scenario
DB_AUTHORITY=neon python inject_synthetic.py --scenario <yaml> --wait

# Preflight checks
./scripts/preflight/run_all_checks.sh

# Layer validator (BLCA)
python3 scripts/ops/layer_validator.py --backend --ci
```

### Key Files

| File | Purpose |
|------|---------|
| `backend/scripts/sdsr/inject_synthetic.py` | SDSR injector |
| `backend/scripts/sdsr/scenarios/*.yaml` | Scenario definitions |
| `scripts/preflight/check_activity_domain.py` | Activity domain validation |
| `docs/governance/SDSR_SYSTEM_CONTRACT.md` | SDSR contract |
| `docs/governance/SDSR_E2E_TESTING_PROTOCOL.md` | E2E testing rules |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `SDSR_SYSTEM_CONTRACT.md` | SDSR pipeline rules |
| `SDSR_E2E_TESTING_PROTOCOL.md` | E2E execution discipline |
| `RUN_VALIDATION_RULES.md` | Attribution validation rules |
| `CAPABILITY_SURFACE_RULES.md` | Capability lifecycle |
