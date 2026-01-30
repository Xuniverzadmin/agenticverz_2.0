# hoc_cus_policies_L5_engines_claim_decision_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/claim_decision_engine.py` |
| Layer | L4 — Domain Engine (System Truth) |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Domain engine for recovery claim decisions.

## Intent

**Reference:** PIN-257 Phase R-4 (L5→L4 Violation Fix)
**Callers:** L4 services (L5 no longer imports this module)

## Purpose

Domain engine for recovery claim decisions.

---

## Functions

### `is_candidate_claimable(confidence: Optional[float]) -> bool`
- **Async:** No
- **Docstring:** Determine if a candidate is eligible for claiming based on confidence.  This is an L4 domain decision. L5 workers must NOT hardcode thresholds.

### `determine_claim_status(evaluation_result: Dict[str, Any]) -> str`
- **Async:** No
- **Docstring:** Determine the execution status from an evaluation result.  This is an L4 domain decision. L5 workers must NOT implement status logic.
- **Calls:** get

### `get_result_confidence(evaluation_result: Dict[str, Any]) -> float`
- **Async:** No
- **Docstring:** Extract confidence from evaluation result with default fallback.  This is an L4 domain decision for confidence extraction.
- **Calls:** get

## Attributes

- `CLAIM_ELIGIBILITY_THRESHOLD: float` (line 44)
- `__all__` (line 118)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

L4 services (L5 no longer imports this module)

## Export Contract

```yaml
exports:
  functions:
    - name: is_candidate_claimable
      signature: "is_candidate_claimable(confidence: Optional[float]) -> bool"
    - name: determine_claim_status
      signature: "determine_claim_status(evaluation_result: Dict[str, Any]) -> str"
    - name: get_result_confidence
      signature: "get_result_confidence(evaluation_result: Dict[str, Any]) -> float"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
