# AURORA SDSR Scenario Synthesis & Validation System

**Status:** ACTIVE
**Version:** 1.1.0
**Last Updated:** 2026-01-19
**Reference:** PIN-370, CAP-E2E-001

---

## Overview

The AURORA SDSR (Scenario-Driven System Realization) system provides automated capability verification through a 3-layer invariant architecture. This document describes how to use the system to generate, execute, and validate SDSR scenarios.

### Purpose

SDSR answers the question: **"Does this capability actually work?"**

- **Claim ≠ Truth**: Code existing is not proof it works correctly
- **Scenarios inject causes**: Real API calls with real parameters
- **Invariants verify effects**: Domain-owned validation rules
- **Observations record truth**: Immutable evidence of capability state

### HISAR Integration

SDSR is integrated into the HISAR pipeline (Human Intent → SDSR → Aurora → Rendering). **You should not run SDSR tools manually** unless debugging. Use HISAR instead:

```bash
# Run HISAR for a single panel (recommended)
./scripts/tools/run_hisar.sh OVR-SUM-HL-O1

# Run HISAR for all panels
./scripts/tools/run_hisar.sh --all

# Dry run (see what would execute)
./scripts/tools/run_hisar.sh --dry-run OVR-SUM-HL-O1
```

HISAR executes SDSR in Phases 4.0 → 4.1 → 4.5 automatically.

---

## Architecture: 3-Layer Invariant Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    SDSR 3-LAYER MODEL                           │
├─────────────────────────────────────────────────────────────────┤
│  L0 — Transport (synth-owned)                                   │
│      • Endpoint reachable                                       │
│      • Auth works (no 401/403)                                  │
│      • Response exists and is valid shape                       │
│      • Status code is success (2xx)                             │
│      • Response time acceptable                                 │
├─────────────────────────────────────────────────────────────────┤
│  L1 — Domain (domain-owned)                                     │
│      • ACTIVITY: policy_context, evaluation_outcome, thresholds │
│      • LOGS: EvidenceMetadata, source_domain, timestamps        │
│      • INCIDENTS: severity, status, source_run_linkage          │
│      • POLICIES: rules structure, proposals, violations         │
├─────────────────────────────────────────────────────────────────┤
│  L2 — Capability (optional)                                     │
│      • Specific business rules                                  │
│      • Custom assertions per capability                         │
│      • Added manually to scenario YAML                          │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principle

> **Synth ATTACHES invariants, does not INVENT them.**
>
> Domain invariants are defined in `backend/sdsr/invariants/` and owned by domain experts. The synth tool simply references them by ID.

---

## File Locations

| Component | Location | Purpose |
|-----------|----------|---------|
| **Synth Tool** | `backend/aurora_l2/tools/aurora_sdsr_synth.py` | Generate scenario YAML |
| **Runner Tool** | `backend/scripts/sdsr/aurora_sdsr_runner.py` | Execute scenarios |
| **Promotion Guard** | `backend/scripts/sdsr/aurora_promotion_guard.py` | CI enforcement |
| **Invariants** | `backend/sdsr/invariants/` | Domain-owned validation |
| **Scenarios** | `backend/scripts/sdsr/scenarios/` | Generated scenario YAMLs |
| **Observations** | `backend/scripts/sdsr/observations/` | Execution results |
| **Intents** | `design/l2_1/intents/` | Panel intent definitions |

---

## HISAR Pipeline Integration (Primary Method)

SDSR is executed as part of the HISAR pipeline. This is the **recommended and primary** method for running SDSR.

### HISAR SDSR Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HISAR PIPELINE (SDSR PHASES)                        │
└─────────────────────────────────────────────────────────────────────────────┘

[S] 3.5  Coherency Gate (BLOCKING)
         └─ aurora_coherency_check.py
         └─ Verifies intent ↔ capability ↔ endpoint alignment
         └─ BLOCKS if incoherent
                    │
                    ▼
[S] 4.0  SDSR Synthesis
         └─ aurora_sdsr_synth.py --panel $PANEL_ID
         └─ Generates: scenarios/SDSR-{PANEL_ID}-001.yaml
         └─ Attaches: invariant IDs (L0 transport + L1 domain)
                    │
                    ▼
[S] 4.1  SDSR Execution
         └─ aurora_sdsr_runner.py --scenario SDSR-{PANEL_ID}-001
         └─ Executes API call (inject)
         └─ Validates response against invariants
         └─ Outputs: observations/SDSR_OBSERVATION_*.json
                    │
                    ▼
[S] 4.5  Promotion Guard (BLOCKING)
         └─ aurora_promotion_guard.py --capability $CAP_ID --ci
         └─ Enforces: L0 ALL PASS + L1 ≥1 PASS
         └─ BLOCKS if promotion rule fails
                    │
                    ▼
[S] 5.0  Observation Application
         └─ aurora_apply_observation.py --capability $CAP_ID
         └─ Updates: DECLARED → OBSERVED (if 4.5 passed)
```

### Running HISAR

```bash
# Single panel (most common)
./scripts/tools/run_hisar.sh OVR-SUM-HL-O1

# All panels
./scripts/tools/run_hisar.sh --all

# Dry run (preview without execution)
./scripts/tools/run_hisar.sh --dry-run OVR-SUM-HL-O1

# Help
./scripts/tools/run_hisar.sh --help
```

### HISAR Failure Semantics

| Phase | Failure Meaning | Resolution |
|-------|-----------------|------------|
| 3.5 Coherency | Intent ↔ backend mismatch | Fix endpoint or intent YAML |
| 4.0 Synthesis | Intent missing required fields | Complete intent YAML |
| 4.1 Execution | API call failed or invariants failed | Fix backend to match contract |
| 4.5 Promotion | L0 or L1 invariants failed | Fix backend, not invariants |
| 5.0 Apply | Observation file missing | Re-run Phase 4.1 |

### Invariant Immutability Law

> **When SDSR fails, the BACKEND is wrong, not the invariant.**

- Report failures as backend gaps
- Fix backend to satisfy intent
- Re-run HISAR after backend fix
- **NEVER** modify invariants to make tests pass

---

## Manual Usage (Debugging Only)

The following manual steps are provided for debugging. **Use HISAR for normal operations.**

---

## Step-by-Step Usage Guide (Manual)

### Step 1: Create Intent YAML (Prerequisites)

Before generating a scenario, ensure the panel intent YAML exists:

```bash
# Check if intent exists
ls design/l2_1/intents/AURORA_L2_INTENT_<panel_id>.yaml

# Example for OVR-SUM-HL-O1
ls design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O1.yaml
```

The intent YAML must contain:
- `capability.id` - Capability ID (e.g., `CAP-ACT-LLM-RUNS-LIVE`)
- `capability.endpoint` or `capability.assumed_endpoint` - API endpoint
- `capability.method` or `capability.assumed_method` - HTTP method
- `panel_class` - Panel type (execution, interpretation, evidence)
- `metadata.domain` - Domain (ACTIVITY, LOGS, INCIDENTS, POLICIES)

### Step 2: Generate Scenario YAML

```bash
cd /root/agenticverz2.0

# Basic generation
python backend/aurora_l2/tools/aurora_sdsr_synth.py --panel OVR-SUM-HL-O1

# Dry run (preview without writing)
python backend/aurora_l2/tools/aurora_sdsr_synth.py --panel OVR-SUM-HL-O1 --dry-run

# Force overwrite existing scenario
python backend/aurora_l2/tools/aurora_sdsr_synth.py --panel OVR-SUM-HL-O1 --force
```

**Output:** Creates `backend/scripts/sdsr/scenarios/SDSR-OVR-SUM-HL-O1-001.yaml`

### Step 3: Review Generated Scenario

The generated scenario contains:

```yaml
scenario_id: SDSR-OVR-SUM-HL-O1-001
version: '1.0.0'
name: Observe OVR-SUM-HL-O1 capability
capability: CAP-OVR-SYSTEM-HEALTH
panel_id: OVR-SUM-HL-O1
domain: OVERVIEW

auth:
  mode: OBSERVER  # OBSERVER | SERVICE | USER

inject:
  type: api_call
  endpoint: /api/v1/overview/health
  method: GET
  headers:
    Content-Type: application/json
  params: {}

expect:
  status_code: 200
  response_type: json
  response_shape:
    _note: Define expected response structure here

# Invariant IDs - executed at runtime
invariant_ids:
  - INV-L0-001  # response_exists
  - INV-L0-002  # response_is_dict_or_list
  - INV-L0-003  # status_code_success
  - INV-L0-004  # auth_not_rejected
  # ... domain-specific invariants
```

### Step 4: (Optional) Customize Scenario

You may optionally edit the scenario to:
- Add custom invariants to `invariant_ids`
- Refine `expect.response_shape`
- Add specific `inject.params`
- Define `inject.body` for POST/PUT requests

### Step 5: Execute Scenario

```bash
cd /root/agenticverz2.0

# Basic execution
python backend/scripts/sdsr/aurora_sdsr_runner.py --scenario SDSR-OVR-SUM-HL-O1-001

# With verbose output
python backend/scripts/sdsr/aurora_sdsr_runner.py --scenario SDSR-OVR-SUM-HL-O1-001 --verbose

# Dry run (validate scenario without API call)
python backend/scripts/sdsr/aurora_sdsr_runner.py --scenario SDSR-OVR-SUM-HL-O1-001 --dry-run

# Custom base URL
python backend/scripts/sdsr/aurora_sdsr_runner.py --scenario SDSR-OVR-SUM-HL-O1-001 \
    --base-url http://staging.example.com

# JSON output (for CI)
python backend/scripts/sdsr/aurora_sdsr_runner.py --scenario SDSR-OVR-SUM-HL-O1-001 --json
```

**Output:**
- Console output with pass/fail results
- Observation JSON in `backend/scripts/sdsr/observations/`

### Step 6: Review Results

The runner outputs:
1. **Inject results**: Status code, response time, errors
2. **Invariant results**: Pass/fail for each invariant
3. **Promotion check**: Whether capability can be promoted to OBSERVED

```
======================================================================
SDSR Scenario: SDSR-OVR-SUM-HL-O1-001
======================================================================
Capability: CAP-OVR-SYSTEM-HEALTH
Panel: OVR-SUM-HL-O1
Domain: OVERVIEW
Endpoint: /api/v1/overview/health
Method: GET
Invariants: 12

--- Executing Inject ---
Status: 200
Response Time: 45.23ms

--- Executing Invariants ---
Total: 12
Passed: 11
Failed: 1
L0 Passed: 8, Failed: 0
L1 Passed: 3, Failed: 1

--- Promotion Check ---
L0 All Pass: True
L1 At Least One: True
OBSERVED Eligible: True

✅ PROMOTION: Capability may be promoted to OBSERVED

Observation: backend/scripts/sdsr/observations/SDSR_OBSERVATION_SDSR-OVR-SUM-HL-O1-001_20260119_143022.json
```

### Step 7: Apply Observation (Update Capability Status)

```bash
# Apply the observation to update capability status
python backend/aurora_l2/tools/AURORA_L2_apply_sdsr_observations.py \
    --observation backend/scripts/sdsr/observations/SDSR_OBSERVATION_*.json
```

### Step 8: Run Promotion Guard (CI Enforcement)

```bash
cd /root/agenticverz2.0

# Validate a single capability
python backend/scripts/sdsr/aurora_promotion_guard.py --capability CAP-OVR-SYSTEM-HEALTH

# Validate all capabilities
python backend/scripts/sdsr/aurora_promotion_guard.py --all

# CI mode (exit 1 on violations)
python backend/scripts/sdsr/aurora_promotion_guard.py --all --ci

# Verbose output
python backend/scripts/sdsr/aurora_promotion_guard.py --all --verbose
```

---

## OBSERVED Promotion Rule (MANDATORY)

A capability may **NOT** move from DECLARED to OBSERVED unless:

| Requirement | Rule |
|-------------|------|
| **L0 All Pass** | All transport invariants must pass |
| **L1 At Least One** | At least ONE domain invariant must pass |
| **Observation Exists** | SDSR scenario was executed and observation emitted |
| **Observation Applied** | `apply_sdsr_observations.py` was run |

```
Capability Lifecycle:
    DECLARED → OBSERVED → TRUSTED → DEPRECATED
         ↑
         └── Requires SDSR validation
```

**Hard Failure:**
```
CAP-E2E-001 VIOLATION: Capability status requires E2E validation.

Capability: CAP-ACT-LLM-RUNS-LIVE
Current status: OBSERVED
E2E validation: NOT FOUND / FAILED

Correct action: Keep status as DECLARED until E2E passes.
```

---

## Domain Invariants Reference

### L0 Transport Invariants (8 total)

| ID | Name | Description | Required |
|----|------|-------------|----------|
| INV-L0-001 | response_exists | Response exists and is not empty | Yes |
| INV-L0-002 | response_is_dict_or_list | Response is dict or list | Yes |
| INV-L0-003 | status_code_success | Status code is 2xx | Yes |
| INV-L0-004 | auth_not_rejected | Not 401 or 403 | Yes |
| INV-L0-005 | no_server_error | Not 5xx | Yes |
| INV-L0-006 | response_time_acceptable | Under 10s | No |
| INV-L0-007 | provenance_present | Has provenance metadata | No |
| INV-L0-008 | items_envelope_present | Has items array | No |

### L1 ACTIVITY Invariants (10 total)

| ID | Name | Description | Required |
|----|------|-------------|----------|
| INV-ACT-001 | policy_context_present | policy_context in all items | Yes |
| INV-ACT-002 | evaluation_outcome_valid | Valid outcome enum | Yes |
| INV-ACT-003 | threshold_values_present | threshold_value in policy_context | Yes |
| INV-ACT-004 | actual_values_present | actual_value in policy_context | Yes |
| INV-ACT-005 | policy_id_present | policy_id in policy_context | Yes |
| INV-ACT-006 | run_id_present | run_id in all items | Yes |
| INV-ACT-007 | tenant_id_present | tenant_id in all items | Yes |
| INV-ACT-008 | timestamps_present | started_at, completed_at present | Yes |
| INV-ACT-009 | status_valid | Valid status enum | No |
| INV-ACT-010 | cost_fields_present | cost/token fields present | No |

### L1 LOGS Invariants (8 total)

| ID | Name | Description | Required |
|----|------|-------------|----------|
| INV-LOG-001 | evidence_metadata_present | EvidenceMetadata in items | Yes |
| INV-LOG-002 | evidence_metadata_required_fields | Required metadata fields | Yes |
| INV-LOG-003 | source_domain_valid | Valid source_domain enum | Yes |
| INV-LOG-004 | origin_valid | Valid origin enum | No |
| INV-LOG-005 | immutable_flag_true | immutable=True | Yes |
| INV-LOG-006 | tenant_id_present | tenant_id present | Yes |
| INV-LOG-007 | timestamps_present | occurred_at, recorded_at | Yes |
| INV-LOG-008 | correlation_spine_present | trace_id, policy_ids | No |

### L1 INCIDENTS Invariants (9 total)

| ID | Name | Description | Required |
|----|------|-------------|----------|
| INV-INC-001 | incident_required_fields | id, severity, status present | Yes |
| INV-INC-002 | severity_valid | Valid severity enum | Yes |
| INV-INC-003 | status_valid | Valid status enum | Yes |
| INV-INC-004 | source_run_linkage | source_run_id present | No |
| INV-INC-005 | category_valid | Valid category enum | No |
| INV-INC-006 | tenant_id_present | tenant_id present | Yes |
| INV-INC-007 | created_at_present | created_at timestamp | Yes |
| INV-INC-008 | items_envelope_present | items array present | Yes |
| INV-INC-009 | pagination_present | Pagination metadata | No |

### L1 POLICIES Invariants (11 total)

| ID | Name | Description | Required |
|----|------|-------------|----------|
| INV-POL-001 | policy_required_fields | id, name, type present | Yes |
| INV-POL-002 | policy_type_valid | Valid policy type enum | Yes |
| INV-POL-003 | policy_status_valid | Valid policy status | Yes |
| INV-POL-004 | policy_rules_structure | rules array valid | No |
| INV-POL-005 | proposal_required_fields | id, policy_id, status | Yes |
| INV-POL-006 | proposal_status_valid | Valid proposal status | Yes |
| INV-POL-007 | proposal_has_rationale | rationale present | No |
| INV-POL-008 | violation_required_fields | id, policy_id, severity | Yes |
| INV-POL-009 | violation_severity_valid | Valid severity enum | Yes |
| INV-POL-010 | violation_has_context | context present | No |
| INV-POL-011 | tenant_id_present | tenant_id present | Yes |

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AOS_API_KEY` | API key for SERVICE/OBSERVER mode | - |
| `AOS_OBSERVER_KEY` | Read-only API key for OBSERVER mode | Falls back to AOS_API_KEY |
| `SDSR_TENANT_ID` | Tenant ID for SERVICE mode | Falls back to AOS_TENANT_ID |
| `AUTH_TOKEN` | Clerk JWT for USER mode | - |

---

## CI Integration

### Option 1: Full HISAR Pipeline (Recommended)

```yaml
# .github/workflows/hisar.yml
name: HISAR Pipeline

on:
  push:
    branches: [main]
    paths:
      - 'design/l2_1/intents/**'
      - 'backend/AURORA_L2_CAPABILITY_REGISTRY/**'
  pull_request:

jobs:
  hisar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml requests

      - name: Run HISAR (All Panels)
        run: |
          ./scripts/tools/run_hisar.sh --all
```

### Option 2: Promotion Guard Only (Faster)

Use this for quick validation without running full pipeline:

```yaml
# .github/workflows/sdsr-guard.yml
name: SDSR Promotion Guard

on:
  push:
    branches: [main]
  pull_request:

jobs:
  sdsr-guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml requests

      - name: Run Promotion Guard
        run: |
          python backend/scripts/sdsr/aurora_promotion_guard.py --all --ci
```

### CI Failure Response

If CI fails at promotion guard:

```
CAP-E2E-001 VIOLATION: Capability status requires E2E validation.

Capability: CAP-ACT-LLM-RUNS-LIVE
Current status: OBSERVED
E2E validation: FAILED

Fix: Keep status as DECLARED until backend satisfies invariants.
```

---

## Troubleshooting

### Scenario Generation Fails

**Error:** `Intent YAML not found`
- Ensure intent file exists: `design/l2_1/intents/AURORA_L2_INTENT_<panel_id>.yaml`

**Error:** `No valid capability ID`
- Check intent YAML has `capability.id` field (not `[TODO:...]`)

**Error:** `No valid endpoint`
- Check intent YAML has `capability.endpoint` or `capability.assumed_endpoint`

### Runner Fails

**Error:** `Invariant system not available`
- Check `backend/sdsr/invariants/__init__.py` exists
- Run from repo root with proper PYTHONPATH

**Error:** `Connection error`
- Verify backend is running: `curl http://localhost:8000/health`
- Check `--base-url` parameter

**Error:** `Auth not rejected but response empty`
- Check environment variables (AOS_API_KEY, etc.)
- Verify auth mode in scenario matches your credentials

### Invariant Failures

**L0 failures (transport):**
- Endpoint doesn't exist → Backend route missing
- Auth rejected → Check credentials and auth mode
- Server error → Backend has a bug

**L1 failures (domain):**
- Missing required fields → Backend response doesn't match contract
- Invalid enum values → Data doesn't conform to domain schema
- Empty response → Endpoint returns empty data

---

## Related Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| SDSR System Contract | `docs/governance/SDSR_SYSTEM_CONTRACT.md` | Governance rules |
| SDSR E2E Testing Protocol | `docs/governance/SDSR_E2E_TESTING_PROTOCOL.md` | E2E testing rules |
| Capability Status Gate | CAP-E2E-001 in `SDSR_SYSTEM_CONTRACT.md` | Promotion rules |
| Intent Ledger | `design/l2_1/INTENT_LEDGER.md` | Panel intent registry |
| Capability Registry | `backend/AURORA_L2_CAPABILITY_REGISTRY/` | Capability definitions |

---

## Quick Reference Commands

### Primary Method: HISAR (Recommended)

```bash
# Run full pipeline for a panel
./scripts/tools/run_hisar.sh <PANEL_ID>

# Run full pipeline for all panels
./scripts/tools/run_hisar.sh --all

# Preview what would run
./scripts/tools/run_hisar.sh --dry-run <PANEL_ID>
```

### Manual Commands (Debugging Only)

```bash
# Generate scenario
python backend/aurora_l2/tools/aurora_sdsr_synth.py --panel <PANEL_ID>

# Run scenario
python backend/scripts/sdsr/aurora_sdsr_runner.py --scenario <SCENARIO_ID>

# Validate promotion eligibility
python backend/scripts/sdsr/aurora_promotion_guard.py --capability <CAP_ID> --ci

# Validate all capabilities
python backend/scripts/sdsr/aurora_promotion_guard.py --all --ci

# Apply observations
python backend/aurora_l2/tools/AURORA_L2_apply_sdsr_observations.py --observation <PATH>
```

### Pipeline Flow Summary

```
Intent YAML → [HISAR] → Scenario YAML → API Call → Invariants → Observation → OBSERVED
     │                        │              │           │            │
     │         Phase 4.0      │   Phase 4.1  │  Phase 4.1 │  Phase 4.5 │  Phase 5.0
     └────────────────────────┴──────────────┴────────────┴────────────┴───────────
```
