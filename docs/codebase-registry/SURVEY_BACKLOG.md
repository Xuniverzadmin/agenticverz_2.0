# Codebase Registry Survey Backlog

**Created:** 2025-12-29
**Reference:** PIN-237
**Schema:** v1 (FROZEN)

---

## Overview

This document tracks artifacts identified during the initial survey but not yet registered. Items are organized into waves for systematic registration.

---

## Registration Waves

### Wave 1: Initial Survey (COMPLETE)

| Category | Count | Status |
|----------|-------|--------|
| Backend API Routes | 28 | REGISTERED |
| Backend Workers | 5 | REGISTERED |
| Backend Services (Key) | 4 | REGISTERED |
| Frontend Pages | 17 | REGISTERED |
| SDK Packages | 4 | REGISTERED |
| **Total** | **58** | **COMPLETE** |

---

### Wave 2: Backend Services (COMPLETE)

**Priority:** HIGH
**Registered Artifacts:** 20
**Status:** Full backend service coverage achieved

#### Platform Core Services

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `worker_registry_service.py` | AOS-BE-SVC-WRG-001 | M21 worker discovery | P1 |
| `tenant_service.py` | AOS-BE-SVC-TNT-001 | M21 tenant CRUD, quotas | P1 |
| `worker_service.py` | AOS-BE-SVC-WKS-001 | M12 job item claiming | P1 |

#### Cost & Anomaly Services

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `cost_anomaly_detector.py` | AOS-BE-SVC-CAD-001 | M29 anomaly detection | P1 |

#### Evidence & Incident Services

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `evidence_report.py` | AOS-BE-SVC-EVD-001 | Legal-grade PDF export | P2 |
| `incident_aggregator.py` | AOS-BE-SVC-INC-001 | Anti-explosion grouping | P1 |
| `event_emitter.py` | AOS-BE-SVC-EMT-001 | PIN-105 ops events | P2 |

#### Failure & Recovery Services

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `llm_failure_service.py` | AOS-BE-SVC-LLF-001 | S4 failure truth | P1 |
| `orphan_recovery.py` | AOS-BE-SVC-ORP-001 | PB-S2 crash recovery | P1 |
| `pattern_detection.py` | AOS-BE-SVC-PTN-001 | PB-S3 pattern detection | P2 |
| `prediction.py` | AOS-BE-SVC-PRD-001 | PB-S5 advisory predictions | P2 |
| `recovery_rule_engine.py` | AOS-BE-SVC-RRE-001 | M10 rule evaluation | P1 |
| `recovery_matcher.py` | AOS-BE-SVC-RMT-001 | M10 pattern matching | P1 |

#### Security & Verification Services

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `certificate.py` | AOS-BE-SVC-CRT-001 | M23 cryptographic evidence | P1 |
| `policy_violation_service.py` | AOS-BE-SVC-PVS-001 | S3 violations | P1 |
| `replay_determinism.py` | AOS-BE-SVC-RPD-001 | Determinism validation | P2 |
| `email_verification.py` | AOS-BE-SVC-EML-001 | OTP verification | P2 |

#### Multi-Agent Coordination Services (M12)

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `job_service.py` | AOS-BE-SVC-JOB-001 | M12 job lifecycle | P1 |
| `message_service.py` | AOS-BE-SVC-MSG-001 | M12 P2P messaging | P2 |
| `blackboard_service.py` | AOS-BE-SVC-BBD-001 | M12 shared state | P2 |
| `registry_service.py` | AOS-BE-SVC-REG-001 | M12 agent registry | P1 |
| `invoke_audit_service.py` | AOS-BE-SVC-IAD-001 | M12.1 audit trail | P2 |

---

### Wave 3: BudgetLLM Module (COMPLETE)

**Priority:** MEDIUM
**Registered Artifacts:** 9
**Status:** BudgetLLM core modules registered

#### Core Modules

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `budget.py` | AOS-LIB-BLL-BGT-001 | Budget enforcement | P1 |
| `cache.py` | AOS-LIB-BLL-CCH-001 | Prompt caching | P1 |
| `client.py` | AOS-LIB-BLL-CLT-001 | OpenAI-compatible client | P1 |
| `safety.py` | AOS-LIB-BLL-SFT-001 | Safety governance | P1 |
| `output_analysis.py` | AOS-LIB-BLL-OAN-001 | Risk signal detection | P2 |
| `prompt_classifier.py` | AOS-LIB-BLL-PCL-001 | Prompt categorization | P2 |
| `risk_formula.py` | AOS-LIB-BLL-RSK-001 | Risk scoring | P2 |

#### Backend Modules

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `backends/memory.py` | AOS-LIB-BLL-BMM-001 | In-memory cache | P2 |
| `backends/redis.py` | AOS-LIB-BLL-BRD-001 | Redis cache | P2 |

---

### Wave 4: Scripts (COMPLETE)

**Priority:** LOW
**Registered Artifacts:** 20 (selective)
**Status:** Key operational scripts registered

Scripts will be registered selectively based on:
- Operational criticality
- Frequency of use
- Documentation value

#### CI/CD Scripts (Selective)

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `ci/synthetic_alert.sh` | AOS-OP-CI-SYN-001 | Alert testing | P3 |
| `ci/check_env_misuse.sh` | AOS-OP-CI-ENV-001 | Env validation | P3 |

#### Operations Scripts (Selective)

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `ops/m10_orchestrator.py` | AOS-OP-OPS-M10-001 | Consolidated maintenance | P2 |
| `ops/rbac_enable.sh` | AOS-OP-OPS-RBC-001 | RBAC enablement | P2 |
| `ops/deploy_website.sh` | AOS-OP-OPS-DPL-001 | Website deployment | P3 |

#### Stress Testing Scripts (Selective)

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `stress/run_golden_stress.sh` | AOS-OP-STR-GLD-001 | Golden replay verification | P2 |
| `stress/run_fault_injection.sh` | AOS-OP-STR-FLT-001 | Fault injection | P2 |

#### Verification Scripts (Selective)

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `verification/truth_preflight.sh` | AOS-OP-VRF-TPF-001 | Truth preflight gate | P1 |
| `verification/tenant_isolation_test.py` | AOS-OP-VRF-TIS-001 | Tenant isolation | P2 |

#### Chaos Engineering Scripts

| File | Artifact ID (Proposed) | Purpose | Priority |
|------|------------------------|---------|----------|
| `chaos/cpu_spike.sh` | AOS-OP-CHS-CPU-001 | CPU spike experiment | P3 |
| `chaos/memory_pressure.sh` | AOS-OP-CHS-MEM-001 | Memory pressure | P3 |
| `chaos/redis_stall.sh` | AOS-OP-CHS-RDS-001 | Redis stall | P3 |

---

## Scripts Classification Summary

| Category | Location | Count | Registration Approach |
|----------|----------|-------|----------------------|
| CI/CD | `scripts/ci/` | 35 | Selective (2-5 key files) |
| Operations | `scripts/ops/` | 96 | Selective (5-10 key files) |
| Stress Testing | `scripts/stress/` | 13 | Selective (2-3 key files) |
| Smoke Testing | `scripts/smoke/` | 2 | Register all |
| Chaos Engineering | `scripts/chaos/` | 3 | Register all |
| Deployment | `scripts/deploy/` | 6 | Selective (2-3 key files) |
| Verification | `scripts/verification/` | 10 | Selective (3-5 key files) |
| Tools | `scripts/tools/` | 1 | Register all |
| Root Level | `scripts/` | 12 | Selective (3-5 key files) |

---

## Priority Definitions

| Priority | Description | Target Timeline |
|----------|-------------|-----------------|
| P1 | Critical infrastructure, high usage | Next sprint |
| P2 | Important but not blocking | Following sprint |
| P3 | Nice to have, low urgency | Backlog |

---

## Not Registered (By Design)

The following are explicitly excluded from registration:

| Category | Reason |
|----------|--------|
| Test files (`*_test.py`, `test_*.py`) | Test infrastructure, not executable artifacts |
| Mock files | Test support only |
| Documentation (`*.md`) | Not executable |
| Configuration examples (`.env.example`) | Templates only |
| Frontend components | Page-level registration sufficient |
| Package `__init__.py` | Structural only |

---

## Tracking

### Registration Progress

| Wave | Status | Registered | Total | Completion |
|------|--------|------------|-------|------------|
| Wave 1 | COMPLETE | 58 | 58 | 100% |
| Wave 2 | COMPLETE | 20 | 20 | 100% |
| Wave 3 | COMPLETE | 9 | 9 | 100% |
| Wave 4 | COMPLETE | 20 | 20 | 100% |
| **Total** | **COMPLETE** | **111** | **111** | **100%** |

### Last Updated

- **Date:** 2025-12-29
- **By:** PIN-237 Wave 2-4 Registration
- **Next Review:** On new artifact detection

---

## How to Register

1. Read source file to understand purpose
2. Assign artifact ID following naming convention
3. Create YAML file in `/docs/codebase-registry/artifacts/`
4. Follow schema-v1.yaml structure
5. Update this backlog document
6. Update SURVEY_REPORT.md totals

---

## Naming Convention

```
AOS-<LAYER>-<TYPE>-<DOMAIN>-<SEQ>

Layers:
- BE: Backend
- FE: Frontend
- SDK: SDK packages
- LIB: Libraries (e.g., BudgetLLM)
- OP: Operations/Scripts

Types:
- API: API routes
- SVC: Services
- WKR: Workers
- PG: Pages
- PKG: Packages
- CI: CI scripts
- OPS: Ops scripts
- STR: Stress scripts
- VRF: Verification scripts
- CHS: Chaos scripts
```
