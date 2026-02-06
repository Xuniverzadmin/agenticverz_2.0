# logs_handler.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/logs_handler.py`
**Layer:** L4 — HOC Spine (Handler)
**Component:** Orchestrator / Handler
**Created:** 2026-02-03
**Reference:** PIN-491 (L2-L4-L5 Construction Plan), PIN-520 (L4 Uniformity Initiative)

---

## Placement Card

```
File:            logs_handler.py
Lives in:        orchestrator/handlers/
Role:            Logs domain handler — routes logs operations to L5 engines via L4 registry
Inbound:         OperationRegistry (L4)
Outbound:        logs/L5_engines/*, logs/L6_drivers/* (lazy imports)
Transaction:     none (dispatch only)
Cross-domain:    yes (incidents L2 -> logs L5 for PDF rendering)
Purpose:         Route logs domain operations to L5 engines and L4 coordinators
Violations:      none
```

## Purpose

Domain handler for logs operations. Routes L2 HTTP requests to L5 engines and L4 coordinators
via the L4 operation registry. Implements the Dispatch Pattern (Law 5 - PIN-507):

- Explicit dispatch maps (no getattr reflection)
- Lazy imports inside execute()
- Session binding at handler level
- Error semantics preserved per facade

## Registered Operations

| Operation | Handler Class | L5/L4 Target | Methods |
|-----------|---------------|--------------|---------|
| `logs.query` | LogsQueryHandler | LogsFacade | 18 async methods |
| `logs.evidence` | LogsEvidenceHandler | EvidenceFacade | 8 async methods |
| `logs.certificate` | LogsCertificateHandler | CertificateService | 4 sync methods |
| `logs.replay` | LogsReplayHandler | ReplayValidator + ReplayCoordinator | 2 sync + 2 async |
| `logs.evidence_report` | LogsEvidenceReportHandler | generate_evidence_report() | 1 sync function |
| `logs.pdf` | LogsPdfHandler | PDFRenderer | 3 sync methods |
| `logs.capture` | LogsCaptureHandler | capture_driver | 1 async method (PIN-520) |

## Handler Details

### LogsQueryHandler

Dispatches to LogsFacade (27 async endpoints):
- `list_llm_run_records`, `get_llm_run_envelope`, `get_llm_run_trace`
- `get_llm_run_governance`, `get_llm_run_replay`, `get_llm_run_export`
- `list_system_records`, `get_system_snapshot`, `get_system_telemetry`
- `get_system_events`, `get_system_replay`, `get_system_audit`
- `list_audit_entries`, `get_audit_entry`, `get_audit_identity`
- `get_audit_authorization`, `get_audit_access`, `get_audit_exports`
- `get_audit_integrity` (sync)

### LogsEvidenceHandler

Dispatches to EvidenceFacade (8 async endpoints):
- `list_chains`, `get_chain`, `create_chain`, `add_evidence`
- `verify_chain`, `create_export`, `get_export`, `list_exports`

### LogsCertificateHandler

Dispatches to CertificateService (4 sync endpoints):
- `create_replay_certificate`, `create_policy_audit_certificate`
- `verify_certificate`, `export_certificate`

### LogsReplayHandler

Mixed dispatch to L5 validators and L4 coordinator:

**Validation methods (sync, L5):**
- `build_call_record` -> ReplayContextBuilder
- `validate_replay` -> ReplayValidator

**Enforcement methods (async, L4 - PIN-520):**
- `enforce_step` -> ReplayCoordinator
- `enforce_trace` -> ReplayCoordinator

### LogsEvidenceReportHandler

Dispatches to `generate_evidence_report()` function (sync, returns PDF bytes).

### LogsPdfHandler

Dispatches to PDFRenderer (3 sync methods):
- `render_evidence_pdf`, `render_soc2_pdf`, `render_executive_debrief_pdf`

Cross-domain operation: incidents L2 -> logs L5 (L4 registry mediates).

### LogsCaptureHandler (PIN-520 Phase 1)

Dispatches to capture_driver for evidence capture. Used by workers.py for Evidence Architecture v1.0.

**Methods:**
- `capture_environment`: Capture environment evidence at run creation

**Parameters:**
- `run_id` (required): Run identifier
- `trace_id` (required): Trace identifier
- `source` (optional): EvidenceSource enum value (default: "SDK")
- `is_synthetic` (optional): Whether this is a synthetic run
- `synthetic_scenario_id` (optional): Synthetic scenario identifier
- `sdk_mode` (optional): SDK mode (default: "api")
- `execution_environment` (optional): Execution environment (default: "prod")
- `telemetry_delivery_status` (optional): Telemetry status (default: "connected")
- `capture_confidence_score` (optional): Confidence score (default: 1.0)

**Usage:**

```python
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_operation_registry

registry = get_operation_registry()
result = await registry.execute(
    "logs.capture",
    tenant_id="t-123",
    session=session,
    params={
        "method": "capture_environment",
        "run_id": "run-456",
        "trace_id": "trace-789",
        "source": "SDK",
        "sdk_mode": "api",
        "execution_environment": "prod",
    }
)
```

## PIN-520 Phase 1

The LogsCaptureHandler was added as part of PIN-520 Phase 1 (workers.py migration).
It absorbs the evidence capture logic that was previously done directly in workers.py,
routing it through the L4 operation registry for proper layer compliance.

This enables:
1. Evidence capture at run creation time
2. Proper L4->L6 routing (no direct L2->L6 imports)
3. Evidence Architecture v1.0 compliance

---

*Generated: 2026-02-03*
