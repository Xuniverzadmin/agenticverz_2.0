# hoc_cus_policies_L6_drivers_recovery_matcher

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/recovery_matcher.py` |
| Layer | L6 — Domain Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Match failure patterns and generate recovery suggestions — L6 DOES NOT COMMIT

## Intent

**Role:** Match failure patterns and generate recovery suggestions — L6 DOES NOT COMMIT
**Reference:** PIN-470, PIN-240, TRANSACTION_BYPASS_REMEDIATION_CHECKLIST.md
**Callers:** L5 engines (must provide session, must own transaction boundary)

## Purpose

_No module docstring._

---

## Classes

### `MatchResult`
- **Docstring:** Result from matching a failure to a recovery suggestion.
- **Class Variables:** matched_entry: Optional[Dict[str, Any]], suggested_recovery: Optional[str], confidence: float, candidate_id: Optional[int], explain: Dict[str, Any], failure_match_id: str, error_code: str, error_signature: str

### `RecoveryMatcher`
- **Docstring:** Matches failures to recovery suggestions using pattern matching
- **Methods:** __init__, _normalize_error, _calculate_time_weight, _compute_confidence, _generate_suggestion, _find_similar_failures, _count_occurrences, _get_cached_recovery, _set_cached_recovery, _find_similar_by_embedding, _escalate_to_llm, suggest_hybrid, _upsert_candidate, suggest, get_candidates, approve_candidate

## Attributes

- `FEATURE_INTENT` (line 32)
- `RETRY_POLICY` (line 33)
- `logger` (line 65)
- `HALF_LIFE_DAYS` (line 68)
- `EMBEDDING_SIMILARITY_THRESHOLD` (line 69)
- `LLM_ESCALATION_THRESHOLD` (line 70)
- `CACHE_TTL_SECONDS` (line 71)
- `LAMBDA` (line 72)
- `ALPHA` (line 73)
- `MIN_CONFIDENCE_THRESHOLD` (line 74)
- `NO_HISTORY_CONFIDENCE` (line 75)
- `EXACT_MATCH_CONFIDENCE` (line 76)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.infra`, `app.memory.vector_store`, `app.security.sanitize`, `httpx`, `redis`, `sqlalchemy`, `sqlmodel` |

## Callers

L5 engines (must provide session, must own transaction boundary)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: MatchResult
      methods: []
    - name: RecoveryMatcher
      methods: [suggest_hybrid, suggest, get_candidates, approve_candidate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
