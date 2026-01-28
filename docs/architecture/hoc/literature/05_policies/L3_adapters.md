# Policies — L3 Adapters (2 files)

**Domain:** policies  
**Layer:** L3_adapters  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

---

## founder_contract_review_adapter.py
**Path:** `backend/app/hoc/cus/policies/L3_adapters/founder_contract_review_adapter.py`  
**Layer:** L3_adapters | **Domain:** policies | **Lines:** 307

**Docstring:** Founder Review Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FounderContractSummaryView` |  | Founder-facing contract summary for the review queue. |
| `FounderContractDetailView` |  | Founder-facing contract detail for review. |
| `FounderReviewQueueResponse` |  | Response for GET /fdr/contracts/review-queue. |
| `FounderReviewDecision` |  | Input for founder review decision. |
| `FounderReviewResult` |  | Result of a founder review action. |
| `FounderReviewAdapter` | to_summary_view, to_detail_view, to_queue_response, to_review_result | Boundary adapter for Founder Review contract views. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Any, List, Optional | no |
| `app.hoc.cus.general.L5_workflow.contracts.engines.contract_engine` | ContractState | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

---

## policy_adapter.py
**Path:** `backend/app/hoc/cus/policies/L3_adapters/policy_adapter.py`  
**Layer:** L3_adapters | **Domain:** policies | **Lines:** 267

**Docstring:** Policy Boundary Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyAdapter` | simulate_cost, check_policy_violations, evaluate_policy, record_approval_created, record_approval_outcome, record_escalation, record_webhook_used | Boundary adapter for policy operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_adapter` | `() -> PolicyAdapter` | no | Get the singleton PolicyAdapter instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `app.commands.policy_command` | PolicyEvaluationResult, PolicyViolation, check_policy_violations, evaluate_policy, record_approval_created (+4) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### __all__ Exports
`PolicyAdapter`, `get_policy_adapter`, `PolicyEvaluationResult`, `PolicyViolation`

---
