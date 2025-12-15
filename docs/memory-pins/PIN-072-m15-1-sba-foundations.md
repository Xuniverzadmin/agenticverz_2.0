# PIN-072: M15.1 SBA Foundations (Strategy-Bound Agents)

**Serial:** PIN-072
**Title:** M15.1 SBA Foundations - Strategy Cascade Enforcement Layer
**Category:** Milestone / Implementation / Governance
**Status:** **COMPLETE**
**Created:** 2025-12-14
**Updated:** 2025-12-14
**Depends On:** PIN-071 (M15 BudgetLLM A2A Integration)
**Supersedes:** None

---

## Executive Summary

M15.1 implements the **Strategy-Bound Agent (SBA)** governance layer - a hard enforcement mechanism that ensures every agent in the AOS multi-agent system operates within a defined Strategy Cascade before being allowed to spawn.

**Key Achievement:** Agents without valid Strategy Cascade are **blocked at spawn time**, not just flagged.

---

## Problem Statement

### Before M15.1

| Issue | Impact |
|-------|--------|
| Agents could spawn without governance contracts | Uncontrolled execution, no budget limits |
| No semantic validation of agent dependencies | Runtime failures when tools unavailable |
| Fulfillment metrics self-reported | Gaming, unreliable agent performance tracking |
| No version negotiation for schema evolution | Breaking changes would halt system |
| Duplicate validation logic in SQL and Python | Maintenance burden, logic divergence |

### After M15.1

| Solution | Benefit |
|----------|---------|
| **5-element Strategy Cascade** required | Every agent has explicit purpose, scope, tasks, dependencies, governance |
| **Spawn-time blocking** | Invalid agents never execute |
| **Semantic validation** | Tool/agent dependencies verified against catalogs |
| **Orchestrator-computed fulfillment** | Tamper-proof performance metrics |
| **Version negotiation** | Graceful schema evolution |
| **Simplified SQL** | Single source of truth in Python |

---

## Architecture

### The 5-Element Strategy Cascade

Every agent MUST define these elements:

```
┌─────────────────────────────────────────────────────────────────┐
│                     STRATEGY CASCADE (SBA)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. WINNING ASPIRATION                                          │
│     └─ WHY does this agent exist?                               │
│        (Purpose statement, NOT a task list)                     │
│                                                                  │
│  2. WHERE TO PLAY                                               │
│     └─ WHAT is the agent's scope?                               │
│        - domain: "web-scraping", "data-analysis"                │
│        - allowed_contexts: ["job", "p2p", "blackboard"]         │
│        - allowed_tools: ["http_fetch", "json_parse"]            │
│        - boundaries: What the agent MUST NOT do                 │
│                                                                  │
│  3. HOW TO WIN                                                  │
│     └─ WHAT will the agent accomplish?                          │
│        - tasks: List of task descriptors                        │
│        - tests: Validation tests (can be empty for retrofits)   │
│        - fulfillment_metric: 0.0-1.0 (orchestrator-computed)    │
│                                                                  │
│  4. CAPABILITIES & CAPACITY                                     │
│     └─ WHAT does the agent need?                                │
│        - dependencies: Typed deps (tool/agent/api/service)      │
│        - env: CPU, memory, timeout, token budget                │
│                                                                  │
│  5. ENABLING MANAGEMENT SYSTEMS                                 │
│     └─ WHO governs this agent?                                  │
│        - orchestrator: The owning orchestrator                  │
│        - governance: MUST be "BudgetLLM" for production         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Enforcement Flow

```
┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
│   Agent Spawn  │────▶│  SBA Validator  │────▶│   Validation   │
│    Request     │     │    (Python)     │     │    Result      │
└────────────────┘     └─────────────────┘     └────────────────┘
                              │                       │
                              ▼                       ▼
                       ┌─────────────────┐     ┌─────────────────┐
                       │ Semantic Checks │     │  valid=true?    │
                       │ - Tool catalog  │     │    │    │       │
                       │ - Agent registry│     │   YES   NO      │
                       │ - Context list  │     │    │    │       │
                       └─────────────────┘     │    ▼    ▼       │
                                               │ SPAWN  BLOCK    │
                                               └─────────────────┘
```

---

## Implementation Details

### Files Created

| File | Purpose |
|------|---------|
| `app/agents/sba/__init__.py` | Module exports (47 exports) |
| `app/agents/sba/schema.py` | Pydantic models for Strategy Cascade |
| `app/agents/sba/validator.py` | Spawn-time enforcement with semantic validation |
| `app/agents/sba/generator.py` | Auto-generate SBA for existing agents |
| `app/agents/sba/service.py` | Database operations for agent registry |
| `alembic/versions/028_m15_1_sba_schema.py` | Creates agent_registry table |
| `alembic/versions/029_m15_1_1_simplify_sba_validator.py` | Simplified SQL validator |

### Files Modified

| File | Changes |
|------|---------|
| `app/agents/skills/agent_spawn.py` | Added SBA validation at spawn |
| `app/api/agents.py` | Added 8 SBA API endpoints |

### Database Schema

```sql
CREATE TABLE agents.agent_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(128) NOT NULL UNIQUE,
    agent_name VARCHAR(256),
    description TEXT,
    agent_type VARCHAR(64) NOT NULL DEFAULT 'worker',

    -- SBA (Strategy Cascade) - JSONB for flexibility
    sba JSONB,
    sba_version VARCHAR(16),
    sba_validated BOOLEAN NOT NULL DEFAULT false,
    sba_validated_at TIMESTAMPTZ,

    -- Capabilities and config
    capabilities JSONB NOT NULL DEFAULT '{}',
    config JSONB NOT NULL DEFAULT '{}',

    -- Status and lifecycle
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    enabled BOOLEAN NOT NULL DEFAULT true,

    -- Tenant isolation
    tenant_id VARCHAR(128) NOT NULL DEFAULT 'default',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## M15.1.1 Risk Fixes

Five priority fixes were implemented to address identified risks:

### Fix 1: Semantic Dependency Validation (CRITICAL)

**Problem:** Governance was structural only - validated schema but not semantic correctness.

**Solution:**
- Added `DependencyType` enum: `tool`, `agent`, `api`, `service`
- Added `Dependency` class with `name`, `type`, `version`, `required`, `fallback`
- Added `agent_lookup_fn` and `tool_lookup_fn` callbacks to validator
- Added context whitelist validation: `job`, `p2p`, `blackboard`, `standalone`
- Added tool permission map per orchestrator

```python
class DependencyType(str, Enum):
    TOOL = "tool"       # Skill/tool dependency
    AGENT = "agent"     # Another agent dependency
    API = "api"         # External API dependency
    SERVICE = "service" # Internal service dependency

class Dependency(BaseModel):
    type: DependencyType
    name: str
    version: Optional[str] = None  # Version constraint e.g. ">=1.0"
    required: bool = True
    fallback: Optional[str] = None  # Fallback if primary unavailable
```

### Fix 2: Dynamic Fulfillment Metric Updates (HIGH)

**Problem:** `fulfillment_metric` set once at spawn, never updated.

**Solution:**
- Added `compute_fulfillment_from_job()` orchestrator hook
- Added `get_fulfillment_history()` for audit trail
- Added weighted scoring formula: `successes * 1.0 + failures * -0.5 + blocked * -0.25`
- History stored in JSONB for M16 analytics

```python
def compute_fulfillment_from_job(
    self,
    agent_id: str,
    job_id: str,
    total_items: int,
    completed_items: int,
    failed_items: int,
    blocked_items: int = 0,
) -> float:
    """Compute fulfillment from actual job results."""
```

### Fix 3: Strengthen SBA Generator (MEDIUM-HIGH)

**Problem:** Generator produces placeholder content that passes validation but has no semantic meaning.

**Solution:**
- Added `strict_mode` parameter to generator
- Added `GenerationQuality` enum: `HIGH`, `MEDIUM`, `LOW`
- Added `GenerationReport` with explicit/inferred/placeholder field tracking
- Added placeholder detection (forbidden phrases, minimum lengths)
- Added explicit overrides: `aspiration_override`, `domain_override`, `tasks_override`, `boundaries_override`

```python
gen = SBAGenerator(strict_mode=True)
sba = gen.generate(
    agent_id='production_scraper',
    aspiration_override='Extract web content from trusted sources...',
    domain_override='web-data-extraction',
    tasks_override=['Fetch HTML', 'Parse content', 'Validate schema'],
    boundaries_override='Must not access restricted domains',
)
```

### Fix 4: Version Negotiation System (MEDIUM)

**Problem:** No mechanism for schema evolution - breaking changes would halt system.

**Solution:**
- Added `SUPPORTED_SBA_VERSIONS`, `MIN_SUPPORTED_VERSION`, `MAX_SUPPORTED_VERSION`
- Added `DEPRECATED_VERSIONS` set for deprecation warnings
- Added `negotiate_version()` function
- Added `get_version_info()` for client capability discovery
- Added `SBAVersionError` exception
- Added API endpoints: `GET /api/v1/sba/version`, `POST /api/v1/sba/version/negotiate`

```python
# Client capability discovery
GET /api/v1/sba/version
{
    "current": "1.0",
    "supported": ["1.0"],
    "min_supported": "1.0",
    "max_supported": "1.0",
    "deprecated": []
}

# Version negotiation
POST /api/v1/sba/version/negotiate?requested_version=1.0
{
    "requested": "1.0",
    "negotiated": "1.0",
    "supported": true,
    "deprecated": false
}
```

### Fix 5: Simplify SQL Validator (MEDIUM-LOW)

**Problem:** Complex SQL validation function duplicated Python logic.

**Solution:**
- Reduced SQL function to field presence checks only
- All semantic validation (governance, dependencies, context) in Python
- Single source of truth eliminates divergence risk

```sql
-- Simplified SQL: Only checks field presence
IF NOT (v_sba ? 'winning_aspiration') THEN
    v_missing_fields := array_append(v_missing_fields, 'winning_aspiration');
END IF;
-- ... other fields ...

-- Semantic validation handled by Python SBAValidator
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/sba/validate` | POST | Validate SBA schema without registration |
| `/api/v1/sba/register` | POST | Register agent with SBA |
| `/api/v1/sba/generate` | POST | Auto-generate SBA from agent metadata |
| `/api/v1/sba/{agent_id}` | GET | Get agent SBA |
| `/api/v1/sba` | GET | List all agents with SBA status |
| `/api/v1/sba/check-spawn` | POST | Check if agent can spawn |
| `/api/v1/sba/version` | GET | Get SBA version info |
| `/api/v1/sba/version/negotiate` | POST | Negotiate SBA version |

---

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SBA_ENFORCE` | `true` | Enable spawn-time SBA validation |
| `SBA_AUTO_GENERATE` | `true` | Auto-generate SBA for agents without one |
| `SBA_ENFORCE_GOVERNANCE` | `true` | Require BudgetLLM governance |

### Valid Contexts

```python
VALID_CONTEXTS = {"job", "p2p", "blackboard", "standalone"}
```

---

## Migration Path

### For Existing Agents

1. **Auto-Generation:** Agents without SBA get auto-generated boilerplate
2. **Quality Tracking:** Generator reports quality level (HIGH/MEDIUM/LOW)
3. **Strict Mode:** Production agents should use explicit overrides
4. **Retrofit API:** `POST /api/v1/sba/generate` for manual retrofit

### Example Retrofit

```python
from app.agents.sba import SBAGenerator, create_tool_dependency

gen = SBAGenerator(strict_mode=True)
sba = gen.generate(
    agent_id='my_existing_agent',
    aspiration_override='Validate incoming API requests to ensure data quality...',
    domain_override='api-validation',
    tasks_override=[
        'Validate JSON schema compliance',
        'Check required fields present',
        'Verify data type constraints',
    ],
    boundaries_override='Must not modify request data, read-only validation only',
)

# Register
service = get_sba_service()
service.register_agent(agent_id='my_existing_agent', sba=sba)
```

---

## Testing

### Unit Test Coverage

```bash
PYTHONPATH=. python3 -c "
from app.agents.sba import (
    SBASchema, SBAValidator, SBAGenerator, validate_sba,
    DependencyType, Dependency, create_minimal_sba,
    get_version_info, negotiate_version,
)
print('All imports OK')
"
```

### Integration Test

```bash
# Verify spawn-time enforcement
curl -X POST http://localhost:8000/api/v1/sba/check-spawn?agent_id=test_agent

# Verify version negotiation
curl http://localhost:8000/api/v1/sba/version
```

---

## Metrics & Observability

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `sba_validation_passed` | counter | SBA validations that passed |
| `sba_validation_failed` | counter | SBA validations that failed |
| `sba_spawn_blocked` | counter | Agents blocked at spawn |
| `sba_generation_quality` | histogram | Distribution of generation quality |
| `sba_fulfillment_updates` | counter | Fulfillment metric updates |

### Log Events

```python
logger.info("sba_validation_passed", extra={"agent_id": agent_id, "warnings": len(warnings)})
logger.warning("sba_validation_failed", extra={"agent_id": agent_id, "errors": error_codes})
logger.warning("sba_generation_low_quality", extra={"agent_id": agent_id, "placeholder_fields": fields})
logger.info("fulfillment_metric_updated", extra={"agent_id": agent_id, "old": old, "new": new})
```

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| SBA tampering | JSONB stored server-side, not client-modifiable |
| Governance bypass | `SBA_ENFORCE_GOVERNANCE=true` requires BudgetLLM |
| Dependency spoofing | Semantic validation against registered catalogs |
| Version downgrade | `DEPRECATED_VERSIONS` set, version negotiation |

---

## Future Work (M16+)

| Item | Description |
|------|-------------|
| **M16 Fulfillment Analytics** | Dashboard for fulfillment history trends |
| **SBA Version 1.1** | Add `retry_policy`, `circuit_breaker` to schema |
| **Dependency Graph** | Visualize agent dependency relationships |
| **Compliance Reports** | Generate governance compliance reports |
| **Schema Diffing** | Track SBA changes between versions |

---

## Related Documents

- **PIN-071:** M15 BudgetLLM A2A Integration (parent milestone)
- **PIN-070:** BudgetLLM Safety Governance Layer
- **PIN-062:** M12 Multi-Agent System
- **PIN-065:** AOS System Reference

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-14 | Initial M15.1 implementation |
| 2025-12-14 | M15.1.1 - 5 risk fixes implemented |
| 2025-12-14 | Migration 028, 029 applied |

---

## Sign-Off

- [x] Strategy Cascade schema defined (5 elements)
- [x] Spawn-time blocking implemented
- [x] Semantic validation (tools, agents, contexts)
- [x] Dynamic fulfillment metrics
- [x] Strict mode generator
- [x] Version negotiation
- [x] Simplified SQL validator
- [x] API endpoints exposed
- [x] Migrations applied

**Status: COMPLETE**
