# hoc_cus_incidents_L5_engines_recovery_rule_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/recovery_rule_engine.py` |
| Layer | L5 — Domain Engine (System Truth) |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Rule-based evaluation engine for recovery suggestions

## Intent

**Role:** Rule-based evaluation engine for recovery suggestions
**Reference:** PIN-470, PIN-240
**Callers:** recovery_evaluator.py (worker)

## Purpose

Rule-based evaluation engine for recovery suggestions.

---

## Functions

### `combine_confidences(rule_confidence: float, match_confidence: float) -> float`
- **Async:** No
- **Docstring:** Combine rule and matcher confidence scores.  This is an L4 domain decision. L5 workers must NOT implement their own formulas.

### `should_select_action(combined_confidence: float) -> bool`
- **Async:** No
- **Docstring:** Determine if an action should be selected based on combined confidence.  This is an L4 domain decision. L5 workers must NOT hardcode thresholds.

### `should_auto_execute(confidence: float) -> bool`
- **Async:** No
- **Docstring:** Determine if a recovery action should be auto-executed based on confidence.  This is an L4 domain decision. L5 workers must NOT hardcode thresholds.

### `classify_error_category(error_codes: List[str]) -> str`
- **Async:** No
- **Docstring:** Classify error codes into a category.  This is an L4 domain decision. L5 workers must NOT implement their own heuristics.
- **Calls:** any, items, join, lower

### `suggest_recovery_mode(error_codes: List[str]) -> str`
- **Async:** No
- **Docstring:** Suggest a recovery mode based on error codes.  This is an L4 domain decision. L5 workers must NOT implement their own heuristics.
- **Calls:** any, items, join, lower

### `evaluate_rules(error_code: str, error_message: str, skill_id: Optional[str], tenant_id: Optional[str], occurrence_count: int, historical_matches: Optional[List[Dict[str, Any]]], custom_rules: Optional[List[Rule]]) -> EvaluationResult`
- **Async:** No
- **Docstring:** Convenience function to evaluate rules against a failure.  Args:
- **Calls:** RecoveryRuleEngine, RuleContext, add_rule, evaluate

## Classes

### `RuleContext`
- **Docstring:** Context provided to rules for evaluation.
- **Methods:** to_dict
- **Class Variables:** error_code: str, error_message: str, skill_id: Optional[str], tenant_id: Optional[str], agent_id: Optional[str], occurrence_count: int, historical_matches: List[Dict[str, Any]], metadata: Dict[str, Any], timestamp: datetime

### `RuleResult`
- **Docstring:** Result from evaluating a single rule.
- **Methods:** to_dict
- **Class Variables:** rule_id: str, rule_name: str, matched: bool, score: float, action_code: Optional[str], explanation: str, confidence_adjustment: float, metadata: Dict[str, Any]

### `EvaluationResult`
- **Docstring:** Complete result from rule evaluation.
- **Methods:** to_dict
- **Class Variables:** rules_evaluated: List[RuleResult], recommended_action: Optional[str], total_score: float, confidence: float, explanation: str, duration_ms: int

### `Rule`
- **Docstring:** Base class for recovery rules.
- **Methods:** __init__, evaluate, __repr__

### `ErrorCodeRule(Rule)`
- **Docstring:** Match based on error code patterns.
- **Methods:** __init__, evaluate

### `HistoricalPatternRule(Rule)`
- **Docstring:** Match based on historical success patterns.
- **Methods:** __init__, evaluate

### `SkillSpecificRule(Rule)`
- **Docstring:** Rules specific to certain skills.
- **Methods:** __init__, evaluate

### `OccurrenceThresholdRule(Rule)`
- **Docstring:** Escalate based on occurrence count.
- **Methods:** __init__, evaluate

### `CompositeRule(Rule)`
- **Docstring:** Combine multiple rules with AND/OR logic.
- **Methods:** __init__, evaluate

### `RecoveryRuleEngine`
- **Docstring:** Evaluates rules against failure context to recommend recovery actions.
- **Methods:** __init__, add_rule, remove_rule, evaluate

## Attributes

- `logger` (line 45)
- `DEBUG_MODE` (line 47)
- `DEFAULT_RULES: List[Rule]` (line 380)
- `AUTO_EXECUTE_CONFIDENCE_THRESHOLD: float` (line 605)
- `ACTION_SELECTION_THRESHOLD: float` (line 610)
- `ERROR_CATEGORY_RULES: Dict[str, List[str]]` (line 665)
- `RECOVERY_MODE_RULES: Dict[str, List[str]]` (line 698)
- `__all__` (line 778)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

recovery_evaluator.py (worker)

## Export Contract

```yaml
exports:
  functions:
    - name: combine_confidences
      signature: "combine_confidences(rule_confidence: float, match_confidence: float) -> float"
    - name: should_select_action
      signature: "should_select_action(combined_confidence: float) -> bool"
    - name: should_auto_execute
      signature: "should_auto_execute(confidence: float) -> bool"
    - name: classify_error_category
      signature: "classify_error_category(error_codes: List[str]) -> str"
    - name: suggest_recovery_mode
      signature: "suggest_recovery_mode(error_codes: List[str]) -> str"
    - name: evaluate_rules
      signature: "evaluate_rules(error_code: str, error_message: str, skill_id: Optional[str], tenant_id: Optional[str], occurrence_count: int, historical_matches: Optional[List[Dict[str, Any]]], custom_rules: Optional[List[Rule]]) -> EvaluationResult"
  classes:
    - name: RuleContext
      methods: [to_dict]
    - name: RuleResult
      methods: [to_dict]
    - name: EvaluationResult
      methods: [to_dict]
    - name: Rule
      methods: [evaluate]
    - name: ErrorCodeRule
      methods: [evaluate]
    - name: HistoricalPatternRule
      methods: [evaluate]
    - name: SkillSpecificRule
      methods: [evaluate]
    - name: OccurrenceThresholdRule
      methods: [evaluate]
    - name: CompositeRule
      methods: [evaluate]
    - name: RecoveryRuleEngine
      methods: [add_rule, remove_rule, evaluate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
