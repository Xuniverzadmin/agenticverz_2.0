# Logs — L5 Schemas (2 files)

**Domain:** logs  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

---

## determinism_types.py
**Path:** `backend/app/hoc/cus/logs/L5_schemas/determinism_types.py`  
**Layer:** L5_schemas | **Domain:** logs | **Lines:** 34

**Docstring:** Determinism Types

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DeterminismLevel` |  | Determinism level for replay validation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `enum` | Enum | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`DeterminismLevel`

---

## traces_models.py
**Path:** `backend/app/hoc/cus/logs/L5_schemas/traces_models.py`  
**Layer:** L5_schemas | **Domain:** logs | **Lines:** 435

**Docstring:** Trace Models for AOS

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TraceStatus` |  | Status of a trace step. |
| `TraceStep` | to_dict, from_dict, determinism_hash | A single step in an execution trace. |
| `TraceSummary` | to_dict | Summary of a trace for listing purposes. |
| `TraceRecord` | total_cost_cents, total_duration_ms, success_count, failure_count, to_dict, from_dict, to_summary, determinism_signature | Complete trace record with all steps. |
| `ParityResult` | to_dict | Result of comparing two traces for replay parity. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_normalize_for_determinism` | `(value: Any) -> Any` | no | Normalize a value for deterministic hashing. |
| `compare_traces` | `(original: TraceRecord, replay: TraceRecord) -> ParityResult` | no | Compare two traces to verify replay parity. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, ClassVar | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`TraceStatus`, `TraceStep`, `TraceSummary`, `TraceRecord`, `ParityResult`, `compare_traces`, `_normalize_for_determinism`

---
