# Controls — L5 Engines (2 files)

**Domain:** controls  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## controls_facade.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/controls_facade.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 438

**Docstring:** Controls Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ControlType` |  | Types of controls. |
| `ControlState` |  | Control state. |
| `ControlConfig` | to_dict | Control configuration. |
| `ControlStatusSummary` | to_dict | Overall control status summary. |
| `ControlsFacade` | __init__, _ensure_default_controls, list_controls, get_control, update_control, enable_control, disable_control, get_status | Facade for control operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_controls_facade` | `() -> ControlsFacade` | no | Get the controls facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## threshold_engine.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/threshold_engine.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 694

**Docstring:** Threshold Decision Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ThresholdParams` | coerce_decimal_to_float | Validated threshold parameters for LLM run governance. |
| `ThresholdParamsUpdate` |  | Partial update for threshold params. |
| `ThresholdDriverProtocol` | get_active_threshold_limits | Protocol defining the interface for threshold drivers. |
| `ThresholdDriverSyncProtocol` | get_active_threshold_limits | Protocol defining the interface for sync threshold drivers. |
| `LLMRunThresholdResolver` | __init__, resolve | Resolves effective threshold params for an LLM run |
| `LLMRunEvaluator` | __init__, evaluate_live_run, evaluate_completed_run | Evaluates LLM runs against threshold params. |
| `LLMRunThresholdResolverSync` | __init__, resolve | Sync version of LLMRunThresholdResolver for worker context. |
| `LLMRunEvaluatorSync` | __init__, evaluate_completed_run | Sync version of LLMRunEvaluator for worker context. |
| `ThresholdSignalRecord` |  | Record of a threshold signal for activity domain. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_threshold_signal_record` | `(tenant_id: str, run_id: str, state: str, signal: ThresholdSignal, params_used: ` | no | Create a threshold signal record for activity domain. |
| `collect_signals_from_evaluation` | `(evaluation: ThresholdEvaluationResult, tenant_id: str, state: str) -> list[Thre` | no | Collect all signals from an evaluation result into records. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | TYPE_CHECKING, Optional, Protocol | no |
| `pydantic` | BaseModel, Field, field_validator | no |
| `app.hoc.cus.controls.L5_schemas.threshold_signals` | ThresholdEvaluationResult, ThresholdSignal | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DEFAULT_LLM_RUN_PARAMS`

---
