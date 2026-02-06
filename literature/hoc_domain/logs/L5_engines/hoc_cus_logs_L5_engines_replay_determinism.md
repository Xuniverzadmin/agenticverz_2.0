# hoc_cus_logs_L5_engines_replay_determinism

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/replay_determinism.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Replay determinism validation for LLM calls — CANONICAL DEFINITIONS

## Intent

**Role:** Replay determinism validation for LLM calls — CANONICAL DEFINITIONS
**Reference:** PIN-470, HOC_logs_analysis_v1.md
**Callers:** logs_facade.py, evidence services, other domains (read-only)

## Purpose

Replay Determinism Service - Defines and Enforces Determinism Semantics

---

## Classes

### `DeterminismLevel(str, Enum)`
- **Docstring:** Levels of determinism for replay validation.

### `ModelVersion`
- **Docstring:** Track the model version used for a call.
- **Methods:** to_dict, from_dict
- **Class Variables:** provider: str, model_id: str, model_version: Optional[str], temperature: Optional[float], seed: Optional[int], timestamp: datetime

### `PolicyDecision`
- **Docstring:** Record of a policy enforcement decision.
- **Methods:** to_dict
- **Class Variables:** guardrail_id: str, guardrail_name: str, passed: bool, action: Optional[str], reason: Optional[str], confidence: float

### `ReplayMatch(str, Enum)`
- **Docstring:** Result of replay comparison.

### `ReplayResult`
- **Docstring:** Result of replay validation.
- **Methods:** to_dict
- **Class Variables:** match_level: ReplayMatch, passed: bool, level_required: DeterminismLevel, details: Dict[str, Any], original_model: Optional[ModelVersion], replay_model: Optional[ModelVersion], model_drift_detected: bool, original_policies: List[PolicyDecision], replay_policies: List[PolicyDecision], policy_match: bool, content_hash_original: Optional[str], content_hash_replay: Optional[str], content_match: bool

### `CallRecord`
- **Docstring:** Record of a call for replay validation.
- **Methods:** to_dict
- **Class Variables:** call_id: str, request_hash: str, response_hash: str, model_version: ModelVersion, policy_decisions: List[PolicyDecision], request_content: Optional[str], response_content: Optional[str], timestamp: datetime, duration_ms: Optional[int], tokens_used: Optional[int]

### `ReplayValidator`
- **Docstring:** Validates replay determinism at configurable levels.
- **Methods:** __init__, validate_replay, _detect_model_drift, _compare_policies, _semantic_equivalent, _level_meets_requirement, hash_content

### `ReplayContextBuilder`
- **Docstring:** Builds replay context from API calls.
- **Methods:** __init__, build_call_record

## Attributes

- `logger` (line 62)
- `__all__` (line 510)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

logs_facade.py, evidence services, other domains (read-only)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: DeterminismLevel
      methods: []
    - name: ModelVersion
      methods: [to_dict, from_dict]
    - name: PolicyDecision
      methods: [to_dict]
    - name: ReplayMatch
      methods: []
    - name: ReplayResult
      methods: [to_dict]
    - name: CallRecord
      methods: [to_dict]
    - name: ReplayValidator
      methods: [validate_replay, hash_content]
    - name: ReplayContextBuilder
      methods: [build_call_record]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
