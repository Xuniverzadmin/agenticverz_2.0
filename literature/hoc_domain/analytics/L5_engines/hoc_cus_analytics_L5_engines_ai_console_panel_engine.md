# hoc_cus_analytics_L5_engines_ai_console_panel_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/ai_console_panel_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Main orchestration engine for panel evaluation

## Intent

**Role:** Main orchestration engine for panel evaluation
**Reference:** PIN-470, L2_1_PANEL_ADAPTER_SPEC.yaml
**Callers:** L2 APIs (ai-console)

## Purpose

AI Console Panel Engine — Main orchestration for panel evaluation

---

## Functions

### `async create_panel_engine(api_base_url: Optional[str]) -> AIConsolePanelEngine`
- **Async:** Yes
- **Docstring:** Create and initialize panel engine.
- **Calls:** AIConsolePanelEngine

### `async get_panel_engine() -> AIConsolePanelEngine`
- **Async:** Yes
- **Docstring:** Get singleton panel engine.
- **Calls:** create_panel_engine

## Classes

### `AIConsolePanelEngine`
- **Docstring:** Main orchestration engine for AI Console panel evaluation.
- **Methods:** __init__, evaluate_panel, _evaluate_panel_slots, _create_short_circuit_response, evaluate_all_panels, get_panel_ids, get_panel_spec, close

## Attributes

- `logger` (line 44)
- `_engine: Optional[AIConsolePanelEngine]` (line 330)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `panel_consistency_checker`, `panel_dependency_resolver`, `panel_metrics_emitter`, `panel_response_assembler`, `panel_signal_collector`, `panel_slot_evaluator`, `panel_spec_loader`, `panel_types`, `panel_verification_engine` |

## Callers

L2 APIs (ai-console)

## Export Contract

```yaml
exports:
  functions:
    - name: create_panel_engine
      signature: "async create_panel_engine(api_base_url: Optional[str]) -> AIConsolePanelEngine"
    - name: get_panel_engine
      signature: "async get_panel_engine() -> AIConsolePanelEngine"
  classes:
    - name: AIConsolePanelEngine
      methods: [evaluate_panel, evaluate_all_panels, get_panel_ids, get_panel_spec, close]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
