# hoc_cus_logs_L6_drivers_panel_consistency_checker

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/panel_consistency_checker.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Cross-slot consistency enforcement

## Intent

**Role:** Cross-slot consistency enforcement
**Reference:** PIN-470, L2_1_PANEL_ADAPTER_SPEC.yaml
**Callers:** Panel adapters

## Purpose

Panel Consistency Checker — Cross-slot consistency rules

---

## Functions

### `create_consistency_checker(rules: Optional[List[Dict[str, Any]]]) -> PanelConsistencyChecker`
- **Async:** No
- **Docstring:** Create consistency checker with optional custom rules.
- **Calls:** PanelConsistencyChecker

## Classes

### `ConsistencyViolation`
- **Docstring:** A consistency violation between slots.
- **Class Variables:** rule_id: str, rule_name: str, slots_involved: List[str], expected: str, actual: str, severity: str

### `ConsistencyCheckResult`
- **Docstring:** Result of consistency checking.
- **Class Variables:** panel_id: str, is_consistent: bool, violations: List[ConsistencyViolation], warnings: List[str]

### `PanelConsistencyChecker`
- **Docstring:** Checks cross-slot consistency within a panel.
- **Methods:** __init__, _default_rules, check, _check_rule, _evaluate_condition, _eval_expr

## Attributes

- `logger` (line 33)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `panel_types` |

## Callers

Panel adapters

## Export Contract

```yaml
exports:
  functions:
    - name: create_consistency_checker
      signature: "create_consistency_checker(rules: Optional[List[Dict[str, Any]]]) -> PanelConsistencyChecker"
  classes:
    - name: ConsistencyViolation
      methods: []
    - name: ConsistencyCheckResult
      methods: []
    - name: PanelConsistencyChecker
      methods: [check]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
