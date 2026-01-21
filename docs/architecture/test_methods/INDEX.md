# Test Methods Documentation Index

**Last Updated:** 2026-01-19
**Location:** `docs/architecture/test_methods/`

---

## Overview

This directory consolidates all test methodology, verification, and validation documentation for the AOS/AgenticVerz system.

### Primary Testing Method: HISAR Pipeline

For capability verification, use the HISAR pipeline:

```bash
./scripts/tools/run_hisar.sh <PANEL_ID>    # Single panel
./scripts/tools/run_hisar.sh --all          # All panels
```

HISAR orchestrates: Human Intent → SDSR → Aurora → Rendering

---

## Document Inventory

### SDSR (Scenario-Driven System Realization)

| Document | Description | Status |
|----------|-------------|--------|
| [aurora_sdsr_synth.md](aurora_sdsr_synth.md) | SDSR scenario synthesis and validation system - comprehensive guide | ACTIVE |

### Test Architecture & Methodology

| Document | Description | Status |
|----------|-------------|--------|
| [AOS_TEST_HANDBOOK.md](AOS_TEST_HANDBOOK.md) | Comprehensive testing guide covering all test types | ACTIVE |
| [test_architecture.md](test_architecture.md) | Test architecture, auth test layers, terminology rules | ACTIVE |
| [FAILURE_LEDGER.md](FAILURE_LEDGER.md) | Test failure classification and cleanup audit | REFERENCE |

### Acceptance & Verification

| Document | Description | Status |
|----------|-------------|--------|
| [acceptance_runtime.md](acceptance_runtime.md) | M1 runtime interface acceptance checklist | REFERENCE |
| [SMOKE_TEST_R3-2.md](SMOKE_TEST_R3-2.md) | Smoke test checklist for E2E handoff | REFERENCE |

---

## Test Method Categories

### 1. SDSR Testing (Capability Verification)

The SDSR system provides automated capability verification through the HISAR pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                    HISAR SDSR PHASES                            │
├─────────────────────────────────────────────────────────────────┤
│  [S] 4.0  SDSR Synthesis    → Generate scenario YAML            │
│  [S] 4.1  SDSR Execution    → Run API + invariants              │
│  [S] 4.5  Promotion Guard   → Enforce L0 all + L1 ≥1 (BLOCKING) │
│  [S] 5.0  Observation Apply → DECLARED → OBSERVED               │
└─────────────────────────────────────────────────────────────────┘
```

**Key Files:**
- `aurora_sdsr_synth.md` - Complete SDSR guide with HISAR integration
- `scripts/tools/run_hisar.sh` - HISAR pipeline orchestrator
- `backend/scripts/sdsr/aurora_sdsr_runner.py` - Scenario executor
- `backend/scripts/sdsr/aurora_promotion_guard.py` - Promotion enforcement
- `backend/sdsr/invariants/` - Domain invariant definitions (L0 + L1)

**Quick Start (Use HISAR):**
```bash
# Run HISAR for a single panel (recommended)
./scripts/tools/run_hisar.sh OVR-SUM-HL-O1

# Run HISAR for all panels
./scripts/tools/run_hisar.sh --all

# Dry run (preview)
./scripts/tools/run_hisar.sh --dry-run OVR-SUM-HL-O1
```

**Manual Commands (Debugging Only):**
```bash
# Generate scenario
python backend/aurora_l2/tools/aurora_sdsr_synth.py --panel <PANEL_ID>

# Execute scenario
python backend/scripts/sdsr/aurora_sdsr_runner.py --scenario <SCENARIO_ID>

# CI validation
python backend/scripts/sdsr/aurora_promotion_guard.py --all --ci
```

### 2. Unit Testing

Located in `backend/tests/unit/`:
- Pure function testing
- No external dependencies
- Fast execution

### 3. Integration Testing

Located in `backend/tests/integration/`:
- Component interaction tests
- Database operations
- Service layer validation

### 4. E2E Testing

Located in `backend/tests/e2e/`:
- Full system flow validation
- Real API calls
- Cross-domain verification

### 5. Acceptance Testing

Milestone-based acceptance criteria:
- `acceptance_runtime.md` - Runtime interface acceptance
- Checklist-driven validation

### 6. Smoke Testing

Quick health verification:
- `SMOKE_TEST_R3-2.md` - Handoff smoke tests
- Critical path validation

---

## Related Resources

### Pipeline Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| HISAR Pipeline | `scripts/tools/run_hisar.sh` | Primary orchestrator |
| HISAR Governance | `docs/governance/HISAR.md` | HISAR rules and invariants |
| HISAR UI Plan Sync | `docs/architecture/HISAR_UI_PLAN_SYNC.md` | UI synchronization |

### Governance Documents

| Document | Location | Purpose |
|----------|----------|---------|
| SDSR System Contract | `docs/governance/SDSR_SYSTEM_CONTRACT.md` | SDSR governance rules |
| SDSR E2E Testing Protocol | `docs/governance/SDSR_E2E_TESTING_PROTOCOL.md` | E2E testing guardrails |
| Capability Status Gate | CAP-E2E-001 | Promotion rules |

### Test Reports

| Location | Purpose |
|----------|---------|
| `docs/test_reports/` | Individual test execution reports |
| `docs/test_reports/REGISTER.md` | Test report registry |

### Test Infrastructure

| Location | Purpose |
|----------|---------|
| `backend/tests/README.md` | Test suite running instructions |
| `backend/tests/conftest.py` | Pytest fixtures |
| `.github/workflows/ci.yml` | CI test pipeline |

---

## Document Maintenance

### Adding New Test Methods

1. Create documentation in this directory
2. Update this INDEX.md
3. Link from relevant governance docs

### Updating Existing Docs

1. Update the document
2. Update "Last Updated" date
3. Update INDEX.md if status changes

---

## Quick Links

- **[Run HISAR](../../scripts/tools/run_hisar.sh)** - Primary method for capability testing
- [SDSR Synth Guide](aurora_sdsr_synth.md) - SDSR documentation with HISAR integration
- [Test Handbook](AOS_TEST_HANDBOOK.md) - Comprehensive test reference
- [Test Architecture](test_architecture.md) - Test structure and patterns

### One-Liner

```bash
./scripts/tools/run_hisar.sh --all   # Run full pipeline for all panels
```
