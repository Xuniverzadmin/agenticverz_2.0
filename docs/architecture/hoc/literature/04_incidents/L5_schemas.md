# Incidents — L5 Schemas (3 files)

**Domain:** incidents  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

---

## export_schemas.py
**Path:** `backend/app/hoc/cus/incidents/L5_schemas/export_schemas.py`  
**Layer:** L5_schemas | **Domain:** incidents | **Lines:** 52

**Docstring:** Export Schemas (PIN-511 Phase 2.1)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ExportBundleProtocol` | create_evidence_bundle, create_soc2_bundle, create_executive_debrief | Protocol for export bundle operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `typing` | Any, Optional, Protocol, runtime_checkable | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## incident_decision_port.py
**Path:** `backend/app/hoc/cus/incidents/L5_schemas/incident_decision_port.py`  
**Layer:** L5_schemas | **Domain:** incidents | **Lines:** 75

**Docstring:** Incident Decision Port (PIN-511 Option B)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentDecisionPort` | check_and_create_incident, create_incident_for_run, get_incidents_for_run | Behavioral contract for incident domain decisions. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `typing` | Any, Dict, List, Optional, Protocol (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## severity_policy.py
**Path:** `backend/app/hoc/cus/incidents/L5_schemas/severity_policy.py`  
**Layer:** L5_schemas | **Domain:** incidents | **Lines:** 203

**Docstring:** Incident Severity Policy (L5 Schema)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SeverityConfig` | default | Configuration for severity decisions. |
| `IncidentSeverityEngine` | __init__, get_initial_severity, calculate_severity_for_calls, should_escalate | Severity decision engine for incidents. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_incident_title` | `(trigger_type: str, trigger_value: str) -> str` | no | Generate human-readable incident title. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Dict, Tuple | no |
| `app.hoc.cus.hoc_spine.schemas.domain_enums` | IncidentSeverity | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### Constants
`DEFAULT_SEVERITY`

### __all__ Exports
`IncidentSeverityEngine`, `SeverityConfig`, `TRIGGER_SEVERITY_MAP`, `DEFAULT_SEVERITY`, `generate_incident_title`

---
