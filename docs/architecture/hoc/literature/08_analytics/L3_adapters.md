# Analytics — L3 Adapters (2 files)

**Domain:** analytics  
**Layer:** L3_adapters  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

---

## alert_delivery.py
**Path:** `backend/app/hoc/cus/analytics/L3_adapters/alert_delivery.py`  
**Layer:** L3_adapters | **Domain:** analytics | **Lines:** 167

**Docstring:** Alert Delivery Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DeliveryResult` |  | Result of alert delivery attempt. |
| `AlertDeliveryAdapter` | __init__, _get_client, close, send_alert | L3 adapter for HTTP alert delivery. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_delivery_adapter` | `(alertmanager_url: Optional[str] = None, timeout_seconds: float = 30.0) -> Alert` | no | Factory function to get AlertDeliveryAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |
| `httpx` | httpx | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### __all__ Exports
`AlertDeliveryAdapter`, `DeliveryResult`, `get_alert_delivery_adapter`

---

## v2_adapter.py
**Path:** `backend/app/hoc/cus/analytics/L3_adapters/v2_adapter.py`  
**Layer:** L3_adapters | **Domain:** analytics | **Lines:** 431

**Docstring:** CostSim V2 Adapter - Enhanced simulation with confidence scoring.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `V2StepEstimate` |  | Enhanced step estimate with confidence. |
| `CostSimV2Adapter` | __init__, _get_coefficients, _estimate_step_v2, simulate, simulate_with_comparison, _compare_results | CostSim V2 Adapter with enhanced modeling. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `simulate_v2` | `(plan: List[Dict[str, Any]], budget_cents: int = 1000, allowed_skills: Optional[` | yes | Convenience function for V2 simulation. |
| `simulate_v2_with_comparison` | `(plan: List[Dict[str, Any]], budget_cents: int = 1000, allowed_skills: Optional[` | yes | Convenience function for V2 simulation with V1 comparison. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `time` | time | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.costsim.config` | get_commit_sha, get_config | no |
| `app.costsim.models` | ComparisonResult, ComparisonVerdict, V2SimulationResult, V2SimulationStatus | no |
| `app.costsim.provenance` | get_provenance_logger | no |
| `app.worker.simulate` | CostSimulator, SimulationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---
