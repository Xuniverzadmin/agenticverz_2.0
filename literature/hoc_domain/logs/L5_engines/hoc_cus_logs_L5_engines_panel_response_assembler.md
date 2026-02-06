# hoc_cus_logs_L5_engines_panel_response_assembler

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/panel_response_assembler.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Assemble final panel response envelope

## Intent

**Role:** Assemble final panel response envelope
**Reference:** PIN-470, L2_1_PANEL_ADAPTER_SPEC.yaml
**Callers:** Panel adapters

## Purpose

Panel Response Assembler — Assemble spec-compliant response envelope

---

## Functions

### `create_response_assembler(adapter_version: Optional[str], schema_version: Optional[str]) -> PanelResponseAssembler`
- **Async:** No
- **Docstring:** Create response assembler.
- **Calls:** PanelResponseAssembler

## Classes

### `PanelResponseAssembler`
- **Docstring:** Assembles the final panel response envelope.
- **Methods:** __init__, assemble, _slot_to_dict, _aggregate_verification, _determine_panel_state, _determine_panel_authority, assemble_error

## Attributes

- `logger` (line 38)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `panel_consistency_checker`, `panel_types` |

## Callers

Panel adapters

## Export Contract

```yaml
exports:
  functions:
    - name: create_response_assembler
      signature: "create_response_assembler(adapter_version: Optional[str], schema_version: Optional[str]) -> PanelResponseAssembler"
  classes:
    - name: PanelResponseAssembler
      methods: [assemble, assemble_error]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
