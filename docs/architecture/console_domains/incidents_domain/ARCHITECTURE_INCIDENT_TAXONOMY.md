# Architecture Incident Taxonomy

**Status:** FROZEN
**Effective:** 2025-12-30
**Reference:** PIN-246

---

## Overview

This document defines the classification system for architecture incidents.
All incidents are logged to `logs/architecture_incidents.log`.

---

## Tier Classification

| Tier | Name | Definition | Response |
|------|------|------------|----------|
| **A** | Structural Violation | Layer, temporal, or intent contract breach | Build blocked, must resolve |
| **B** | Integration Violation | LIT or BIT test failure | Merge blocked, must fix |
| **C** | Governance Friction | False positive, rule tension, heuristic miss | Log and review periodically |

---

## Tier A: Structural Violations

These are hard failures. Code cannot proceed.

### Temporal Violations (TV-*)

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| TV-001 | Sync Importing Async | Sync layer (L1-L3) imports from L5 | BLOCKING |
| TV-002 | API Awaiting Worker | API handler blocks on worker execution | BLOCKING |
| TV-003 | Hidden Deferred | Deferred execution masked behind sync API | BLOCKING |
| TV-004 | Background in L1-L2 | Background task creation in UI/API layers | BLOCKING |
| TV-005 | Undeclared Temporal | No temporal execution declaration | BLOCKING |
| TV-006 | Async Leak Upward | Async semantics leaking into sync layers | BLOCKING |

### Intent Violations (INTENT-*)

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| INTENT-001 | Missing Intent | No ARTIFACT_INTENT.yaml or file header | BLOCKING |
| INTENT-002 | Incomplete Intent | Required fields missing (owner, role) | BLOCKING |
| INTENT-003 | Missing Temporal | Temporal trigger/execution not declared | BLOCKING |

### Layer Violations (LAYER-*)

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| LAYER-001 | Missing Layer | No layer declaration (L1-L8) | BLOCKING |
| LAYER-002 | Low Confidence | Layer confidence declared as LOW | BLOCKING |
| LAYER-003 | Invalid Layer | Layer value not in L1-L8 | BLOCKING |
| LAYER-004 | Import Violation | Forbidden layer import detected | BLOCKING |

---

## Tier B: Integration Violations

These block merge but not local development.

### LIT Violations (LIT-*)

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| LIT-FAIL | LIT Test Failure | Layer Integration Test failed | BLOCKING |
| LIT-MISS | LIT Coverage Gap | New API without LIT test | WARNING |

### BIT Violations (BIT-*)

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| BIT-FAIL | BIT Test Failure | Browser Integration Test failed | BLOCKING |
| BIT-CONSOLE | Console Error | console.error detected on page | BLOCKING |
| BIT-5XX | Server Error | 5xx response during navigation | BLOCKING |

---

## Tier C: Governance Friction

These are logged but do not block. Reviewed periodically.

| Code | Name | Description | Severity |
|------|------|-------------|----------|
| FALSE-POS | False Positive | Heuristic flagged valid code | INFO |
| HEURISTIC | Heuristic Gap | Valid violation missed by heuristic | INFO |
| RULE-TENSION | Rule Tension | Two rules conflict, manual resolution needed | WARNING |

---

## Incident Log Schema

Each incident is recorded as a JSON line:

```json
{
  "incident_id": "ARCH-20251230-143022-TV-001",
  "timestamp": "2025-12-30T14:30:22Z",
  "violation_code": "TV-001",
  "file": "backend/app/api/runs.py",
  "layer": "L2",
  "author": "unknown",
  "summary": "Sync layer L2 imports from L5 module: app.worker.executor",
  "source": "temporal_detector"
}
```

---

## Log Location

```
logs/architecture_incidents.log
```

---

## Commands

```bash
# Log an incident manually
python scripts/ops/architecture_incident_logger.py log \
    --code TV-001 \
    --file backend/app/api/runs.py \
    --layer L2 \
    --summary "Sync layer importing async worker"

# View recent incidents
python scripts/ops/architecture_incident_logger.py view --last 10

# Generate report
python scripts/ops/architecture_incident_logger.py report
```

---

## Evolution Policy

1. **New codes require evidence** — 3+ incidents of same pattern before adding
2. **Tier changes require review** — Moving violations between tiers requires PIN
3. **Heuristic tuning requires data** — No tuning without incident log analysis

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial taxonomy created |
