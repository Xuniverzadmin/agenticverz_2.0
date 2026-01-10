# PIN-386: SDSR → AURORA_L2 Observation Schema Contract

**Status:** LOCKED
**Created:** 2026-01-10
**Category:** SDSR / Schema Contract
**Related:** PIN-370, PIN-379

---

## Purpose

Define the canonical schema for SDSR observation artifacts that bridge scenario execution to AURORA_L2 capability state.

This schema is the **single source of truth** for observation JSON structure. All producers and consumers MUST conform.

---

## Schema Location

```
sdsr/SDSR_OBSERVATION_SCHEMA.json
```

---

## Canonical Field Names (LOCKED)

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scenario_id` | string | YES | SDSR scenario identifier (e.g., `SDSR-E2E-004`) |
| `status` | enum | YES | `PASSED` only (observations only emitted for PASSED scenarios) |
| `observed_at` | datetime | YES | ISO 8601 timestamp when observation was recorded |
| `capabilities_observed` | array | YES | List of capabilities exercised |
| `environment` | enum | NO | `preflight` or `production` |
| `metadata` | object | NO | Additional traceability info |

### Capability Fields (`capabilities_observed[]`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `capability_id` | string | YES | Capability ID from registry (e.g., `APPROVE`, `REJECT`) |
| `ui_panel` | string | YES | Panel ID where action was invoked (e.g., `POL-PR-PP-O2`) |
| `ui_action` | string | YES | Action name as displayed in UI |
| `endpoint` | string | YES | API endpoint invoked |
| `method` | enum | YES | HTTP method (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) |
| `response_status` | integer | NO | HTTP response status code (200-299) |
| `observed_effects` | array | YES | State transitions observed |

### Effect Fields (`observed_effects[]`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity` | string | YES | Entity type affected (e.g., `policy_proposal`, `incident`) |
| `field` | string | YES | Field that changed (e.g., `status`) |
| `from` | string | YES | Value before action |
| `to` | string | YES | Value after action |

### Metadata Fields (`metadata`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | NO | SDSR execution run ID |
| `runner_version` | string | NO | inject_synthetic.py version |
| `notes` | string | NO | Optional notes about the observation |

---

## Field Name Mapping (Internal → JSON)

These mappings are LOCKED. Do not deviate.

| Python Class Field | JSON Output Field | Notes |
|--------------------|-------------------|-------|
| `observed_at` | `observed_at` | NOT `observed_on` |
| `realized_capabilities` | `capabilities_observed` | List name differs |
| `effects` | `observed_effects` | List name differs |
| `before` | `from` | Effect value before |
| `after` | `to` | Effect value after |
| `status` | `status` | Required at top level |

---

## Example Observation

```json
{
  "scenario_id": "SDSR-TEST-001",
  "status": "PASSED",
  "observed_at": "2026-01-10T15:00:00Z",
  "environment": "preflight",
  "capabilities_observed": [
    {
      "capability_id": "APPROVE",
      "ui_panel": "POL-PR-PP-O2",
      "ui_action": "Approve",
      "endpoint": "/api/v1/policy-proposals/{id}/approve",
      "method": "POST",
      "response_status": 200,
      "observed_effects": [
        {
          "entity": "policy_proposal",
          "field": "status",
          "from": "PENDING",
          "to": "APPROVED"
        }
      ]
    }
  ],
  "metadata": {
    "run_id": "run-sdsr-test-001-20260110T150000Z",
    "runner_version": "inject_synthetic.py v1.0",
    "notes": "Test observation"
  }
}
```

---

## Producer/Consumer Matrix

| Component | Role | Location |
|-----------|------|----------|
| `Scenario_SDSR_output.py` | Internal data model | `backend/scripts/sdsr/` |
| `SDSR_output_emit_AURORA_L2.py` | JSON producer | `backend/scripts/sdsr/` |
| `AURORA_L2_apply_sdsr_observations.py` | JSON consumer | `scripts/tools/` |
| `SDSR_OBSERVATION_SCHEMA.json` | Canonical schema | `sdsr/` |

---

## Validation Rules

1. **PASSED only**: Only `status: PASSED` observations may be emitted
2. **Non-empty capabilities**: `capabilities_observed` must have at least 1 item
3. **Non-empty effects**: Each capability must have at least 1 `observed_effects`
4. **Valid capability_id**: Must match pattern `^[A-Z_]+$`
5. **Valid panel_id**: Must match pattern `^[A-Z]+-[A-Z]+-[A-Z]+-O[1-5]$`
6. **Valid endpoint**: Must start with `/api/`

---

## Pipeline Integration

```
inject_synthetic.py --wait
       │
       └─ ScenarioSDSROutputBuilder.from_execution()
              │
              └─ emit_aurora_l2_observation()
                     │
                     └─ SDSR_OBSERVATION_<id>.json  ← Schema enforced here
                            │
                            └─ AURORA_L2_apply_sdsr_observations.py
                                   │
                                   ├─ Capability YAML → OBSERVED
                                   └─ Intent YAML → observation_trace
```

---

## Bugs Fixed (2026-01-10)

| Bug | Wrong | Correct | Fixed In |
|-----|-------|---------|----------|
| BUG-1 | `observed_on` | `observed_at` | `Scenario_SDSR_output.py`, `SDSR_output_emit_AURORA_L2.py` |
| BUG-2 | `realized_capabilities` | `capabilities_observed` | `SDSR_output_emit_AURORA_L2.py` |
| BUG-3 | `effects` | `observed_effects` | `SDSR_output_emit_AURORA_L2.py` |
| BUG-4 | `before`/`after` | `from`/`to` | `SDSR_output_emit_AURORA_L2.py` |
| BUG-5 | Missing `status` | Added `status` | `SDSR_output_emit_AURORA_L2.py` |

---

## Invariants

1. **Schema is canonical**: `SDSR_OBSERVATION_SCHEMA.json` is the source of truth
2. **Producers adapt to schema**: Internal field names may differ, output MUST conform
3. **No schema inference**: Consumers validate against schema, not guessing
4. **Observation = witness**: Observations record truth, they do not decide it

---

## References

- Schema: `sdsr/SDSR_OBSERVATION_SCHEMA.json`
- Template: `sdsr/observations/_TEMPLATE_OBSERVATION.json`
- Producer: `backend/scripts/sdsr/SDSR_output_emit_AURORA_L2.py`
- Consumer: `scripts/tools/AURORA_L2_apply_sdsr_observations.py`
- Orchestrator: `scripts/sdsr/sdsr_e2e_apply.py`
