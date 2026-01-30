# hoc_cus_analytics_L5_engines_datasets

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/datasets.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim V2 reference datasets (validation samples)

## Intent

**Role:** CostSim V2 reference datasets (validation samples)
**Reference:** PIN-470
**Callers:** canary runner, divergence engine

## Purpose

Reference datasets for V2 validation.

---

## Functions

### `get_dataset_validator() -> DatasetValidator`
- **Async:** No
- **Docstring:** Get the global dataset validator.
- **Calls:** DatasetValidator

### `async validate_dataset(dataset_id: str) -> ValidationResult`
- **Async:** Yes
- **Docstring:** Convenience function to validate a dataset.
- **Calls:** get_dataset_validator, validate_dataset

### `async validate_all_datasets() -> Dict[str, ValidationResult]`
- **Async:** Yes
- **Docstring:** Convenience function to validate all datasets.
- **Calls:** get_dataset_validator, validate_all

## Classes

### `DatasetSample`
- **Docstring:** A single sample in a reference dataset.
- **Class Variables:** id: str, plan: List[Dict[str, Any]], budget_cents: int, expected_cost_cents: Optional[int], expected_feasible: Optional[bool], expected_confidence_min: Optional[float], tags: List[str]

### `ReferenceDataset`
- **Docstring:** A reference dataset for validation.
- **Methods:** to_dict
- **Class Variables:** id: str, name: str, description: str, samples: List[DatasetSample], validation_thresholds: Dict[str, float]

### `DatasetValidator`
- **Docstring:** Validator for V2 against reference datasets.
- **Methods:** __init__, _build_datasets, _build_low_variance_dataset, _build_high_variance_dataset, _build_mixed_city_dataset, _build_noise_injected_dataset, _build_historical_dataset, list_datasets, get_dataset, validate_dataset, _calculate_drift_score, validate_all

## Attributes

- `logger` (line 46)
- `_validator: Optional[DatasetValidator]` (line 703)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.costsim.models`, `app.costsim.v2_adapter`, `random` |

## Callers

canary runner, divergence engine

## Export Contract

```yaml
exports:
  functions:
    - name: get_dataset_validator
      signature: "get_dataset_validator() -> DatasetValidator"
    - name: validate_dataset
      signature: "async validate_dataset(dataset_id: str) -> ValidationResult"
    - name: validate_all_datasets
      signature: "async validate_all_datasets() -> Dict[str, ValidationResult]"
  classes:
    - name: DatasetSample
      methods: []
    - name: ReferenceDataset
      methods: [to_dict]
    - name: DatasetValidator
      methods: [list_datasets, get_dataset, validate_dataset, validate_all]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
