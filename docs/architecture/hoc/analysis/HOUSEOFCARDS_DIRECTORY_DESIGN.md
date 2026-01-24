# Houseofcards Directory Design

**Status:** ACTIVE
**Created:** 2026-01-22
**Reference:** First-principles directory reorganization

---

## Overview

The `app/houseofcards/` namespace provides a first-principles directory structure where **the path tells you what it does**. This reorganization addresses the flat structure problem in `app/services/` where 200+ files lived without clear organization.

## Design Principles

1. **Path = Purpose**: `customer/policies/engines/limits_engine.py` immediately tells you:
   - WHO: customer-facing
   - WHAT: policies domain
   - HOW: engine (business logic)

2. **Audience-First**: Top-level split by who consumes the code
3. **Domain-Driven**: Second level groups by business domain
4. **Role-Based**: Leaf level indicates architectural role

---

## Directory Structure

```
app/houseofcards/
├── customer/           # Customer-facing (Console, SDK, APIs)
│   ├── account/        # Account management, users, profile
│   │   ├── support/CRM/engines/  # CRM workflow (imported by founder ops)
│   │   ├── engines/
│   │   ├── facades/
│   │   ├── drivers/
│   │   └── schemas/
│   ├── activity/       # Runs, traces, execution history
│   ├── analytics/      # Cost analysis, predictions, patterns
│   ├── api_keys/       # API key management
│   ├── general/        # Cross-cutting, imported by all domains
│   │   ├── cross-domain/engines/  # Cross-domain operations
│   │   ├── runtime/engines/       # Runtime orchestration
│   │   ├── ui/engines/            # UI projections
│   │   ├── workflow/contracts/engines/  # Contract state machine
│   │   └── engines/               # General utilities
│   ├── incidents/      # Incident management, recovery
│   ├── integrations/   # External integrations, connectors
│   │   └── vault/engines/  # Credential encryption
│   ├── logs/           # Traces, audit, evidence
│   ├── overview/       # Dashboard, health status
│   └── policies/       # Rules, limits, controls
│       └── controls/   # Kill switch, runtime switches
│           └── KillSwitch/engines/
├── internal/           # Internal infrastructure (workers, adapters)
│   ├── agent/          # AI console panel adapter, workers
│   ├── platform/       # Platform-level services
│   │   └── governance/engines/  # Governance signals
│   └── recovery/       # Scoped execution, recovery actions
└── founder/            # Founder/Admin-only (ops tools)
    └── ops/            # Ops console, founder actions
```

---

## Audiences

| Audience | Description | Examples |
|----------|-------------|----------|
| **customer** | Customer-facing code | Console APIs, SDK, facades |
| **internal** | Internal infrastructure | Workers, adapters, platform services |
| **founder** | Founder/Admin only | Ops console, founder actions |

---

## Domains (Customer)

| Domain | Question Answered | Key Files |
|--------|-------------------|-----------|
| **account** | Who is the user? | tenant_service, user_write_service, profile |
| **activity** | What ran/is running? | activity_facade, llm_failure_service |
| **analytics** | What patterns exist? | cost_anomaly_detector, prediction, pattern_detection |
| **api_keys** | What keys exist? | keys_service, api_keys_facade |
| **general** | Cross-cutting utilities | runtime orchestration, cross-domain, contracts |
| **incidents** | What went wrong? | incident_aggregator, guard_write_service |
| **integrations** | What external connections? | http_connector, mcp_connector, sql_gateway |
| **logs** | What is the raw truth? | logs_facade, evidence_report, replay_determinism |
| **overview** | Is the system OK? | overview_facade, health services |
| **policies** | How is behavior defined? | policies_facade, limits, controls |

---

## Roles

| Role | Layer | Responsibility |
|------|-------|----------------|
| **facades** | L4 | External interface, orchestrates engines |
| **engines** | L4 | Business logic, domain rules |
| **drivers** | L3 | Thin adapters, external communication |
| **schemas** | L6 | Data transfer objects, validation |

---

## File Count Summary

| Location | Files |
|----------|-------|
| customer/ | 133 |
| internal/ | 30 |
| founder/ | 7 |
| **Total** | **170** |

*Verified 2026-01-22 via deep audit*

---

## Migration Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Structure | ✅ COMPLETE | Directory structure created |
| Phase 2: Copy | ✅ COMPLETE | 167 files copied, 15 facades renamed |
| Phase 3: BLCA | ✅ PASS | 0 violations (1452 files scanned) |
| Phase 4: Consolidate | PENDING | Remove duplicates |
| Phase 5: Wire Imports | PENDING | Update import statements |
| Phase 6: Deprecate | PENDING | Mark app/services/ as deprecated |

### Deep Audit (2026-01-22)

- **Coverage:** 100% (0 files missing)
- **40 subdirectories:** All covered
- **Facade renames:** 15 (`facade.py` → `{domain}_facade.py`)

---

## Related Documents

- `HOUSEOFCARDS_IMPLEMENTATION_PLAN.md` - Step-by-step migration plan
- `AUDIENCE_REGISTRY.yaml` - Audience classification rules
