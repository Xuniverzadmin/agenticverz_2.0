# hoc_cus_logs_L6_drivers_integrity

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/integrity.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Integrity computation with separated concerns

## Intent

**Role:** Integrity computation with separated concerns
**Reference:** PIN-470, Evidence Architecture v1.1
**Callers:** runner.py (at terminal), evidence.capture

## Purpose

Integrity Computation Module (v1.1)

---

## Functions

### `compute_integrity_v2(run_id: str) -> Dict[str, Any]`
- **Async:** No
- **Docstring:** Compute integrity using the new split architecture.  Returns dict compatible with the original compute_integrity().
- **Calls:** IntegrityAssembler, IntegrityEvaluator, evaluate, gather, to_dict

## Classes

### `IntegrityState(str, Enum)`
- **Docstring:** Evidence completeness state.

### `IntegrityGrade(str, Enum)`
- **Docstring:** Quality judgment on the evidence.

### `EvidenceClass(str, Enum)`
- **Docstring:** Taxonomy of evidence classes.

### `FailureResolution(str, Enum)`
- **Docstring:** Resolution semantics for capture failures.

### `CaptureFailure`
- **Docstring:** Structured representation of an evidence capture failure.
- **Methods:** to_dict
- **Class Variables:** evidence_class: EvidenceClass, failure_reason: str, error_message: Optional[str], resolution: FailureResolution

### `IntegrityFacts`
- **Docstring:** Raw facts gathered from evidence tables.
- **Methods:** has_required_evidence, has_capture_failures, unresolved_failures
- **Class Variables:** run_id: str, observed_evidence: List[EvidenceClass], missing_evidence: List[EvidenceClass], capture_failures: List[CaptureFailure], evidence_counts: Dict[str, int], gathered_at: datetime

### `IntegrityAssembler`
- **Docstring:** Gathers facts from evidence tables.
- **Methods:** __init__, gather, _count_evidence, _gather_failures, _resolve_superseded, _table_to_class, _string_to_class

### `IntegrityEvaluation`
- **Docstring:** Result of integrity policy evaluation.
- **Methods:** integrity_status
- **Class Variables:** state: IntegrityState, grade: IntegrityGrade, score: float, missing_reasons: Dict[str, str], explanation: str

### `IntegrityEvaluator`
- **Docstring:** Applies policy to integrity facts.
- **Methods:** evaluate, _find_failure, _compute_grade, _build_explanation

## Attributes

- `logger` (line 57)
- `DATABASE_URL` (line 59)
- `REQUIRED_EVIDENCE` (line 118)
- `EXPECTED_EVIDENCE` (line 125)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `sqlalchemy`, `sqlalchemy.exc` |

## Callers

runner.py (at terminal), evidence.capture

## Export Contract

```yaml
exports:
  functions:
    - name: compute_integrity_v2
      signature: "compute_integrity_v2(run_id: str) -> Dict[str, Any]"
  classes:
    - name: IntegrityState
      methods: []
    - name: IntegrityGrade
      methods: []
    - name: EvidenceClass
      methods: []
    - name: FailureResolution
      methods: []
    - name: CaptureFailure
      methods: [to_dict]
    - name: IntegrityFacts
      methods: [has_required_evidence, has_capture_failures, unresolved_failures]
    - name: IntegrityAssembler
      methods: [gather]
    - name: IntegrityEvaluation
      methods: [integrity_status]
    - name: IntegrityEvaluator
      methods: [evaluate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
