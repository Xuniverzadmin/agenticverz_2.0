# Logs — L5 Other (1 files)

**Domain:** logs  
**Layer:** L5_other  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## audit_engine.py
**Path:** `backend/app/hoc/cus/logs/L5_support/CRM/engines/audit_engine.py`  
**Layer:** L5_other | **Domain:** logs | **Lines:** 888

**Docstring:** Part-2 Governance Audit Service (L8)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CheckResult` |  | Result of an individual audit check. |
| `AuditCheck` |  | Result of a single audit check. |
| `AuditInput` |  | Input to the audit process. |
| `AuditResult` |  | Complete audit result with all checks and final verdict. |
| `AuditChecks` | check_scope_compliance, check_health_preservation, _is_health_degraded, check_execution_fidelity, check_timing_compliance, check_rollback_availability, check_signal_consistency, check_no_unauthorized_mutations | Individual audit check implementations. |
| `AuditService` | __init__, version, audit, _run_all_checks, _determine_verdict | Part-2 Governance Audit Service (L8) |
| `RolloutGate` | is_rollout_authorized, get_rollout_status | Gate that determines if rollout is authorized. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `audit_result_to_record` | `(result: AuditResult) -> dict[str, Any]` | no | Convert AuditResult to database record format. |
| `create_audit_input_from_evidence` | `(job_id: UUID, contract_id: UUID, job_status: str, contract_scope: list[str], pr` | no | Create AuditInput from job execution evidence. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID, uuid4 | no |
| `app.models.contract` | AuditVerdict | no |

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.contract import AuditVerdict` | L5 MUST NOT import L7 models directly | Route through L6 driver | 64 |

### Constants
`AUDIT_SERVICE_VERSION`

---
