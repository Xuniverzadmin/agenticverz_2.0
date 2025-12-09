# PIN-053: Mock Inventory & Real-World Plugin Requirements

**Date**: 2025-12-09
**Status**: REFERENCE
**Category**: Architecture / Testing Infrastructure
**Author**: Claude Code Analysis

---

## Summary

Comprehensive audit of all mocking mechanisms in the AOS codebase, identifying which mocks require real-world plugin implementations for production use.

---

## 1. SKILL STUBS (Production-Critical)

### 1.1 HTTP Call Stub
| Property | Value |
|----------|-------|
| **File** | `/backend/app/skills/stubs/http_call_stub.py` |
| **Classes** | `MockResponse`, `HttpCallStub` |
| **Mocks** | External HTTP API calls |
| **Real Plugin Needed** | YES - `HttpCallV2` in `/backend/app/skills/http_call_v2.py` |

**Limitations:**
- No actual network calls (purely deterministic)
- Requires pre-configured responses
- No streaming support
- No retry with real backoff

**Production Path:** Use `HttpCallV2` with real `httpx.AsyncClient`

---

### 1.2 LLM Invoke Stub
| Property | Value |
|----------|-------|
| **File** | `/backend/app/skills/stubs/llm_invoke_stub.py` |
| **Classes** | `MockLlmResponse`, `LlmInvokeStub` |
| **Mocks** | Anthropic Claude API calls |
| **Real Plugin Needed** | YES - `ClaudeAdapter` in `/backend/app/skills/adapters/claude_adapter.py` |

**Limitations:**
- Deterministic hash-based responses only
- No real temperature/creativity
- Mock responses must be explicitly configured
- No streaming

**Production Path:** Use `ClaudeAdapter` with real Anthropic SDK

---

### 1.3 JSON Transform Stub
| Property | Value |
|----------|-------|
| **File** | `/backend/app/skills/stubs/json_transform_stub.py` |
| **Class** | `JsonTransformStub` |
| **Mocks** | JSON transformation operations |
| **Real Plugin Needed** | NO - Already deterministic |

**Operations supported:** extract, map, filter, pick, omit, merge

**Note:** This stub IS the production implementation (deterministic by nature)

---

## 2. PLANNER STUBS (Production-Critical)

### 2.1 Stub Planner
| Property | Value |
|----------|-------|
| **Files** | `/backend/app/planner/stub_planner.py`, `/backend/app/planners/stub_adapter.py` |
| **Class** | `StubPlanner(PlannerInterface)` |
| **Mocks** | Anthropic planner for plan generation |
| **Real Plugin Needed** | YES - `AnthropicPlanner` in `/backend/app/planners/anthropic_adapter.py` |

**Limitations:**
- Rule-based only (5 keyword rules)
- No AI reasoning
- No context understanding beyond keywords
- Fixed response patterns

**Production Path:** Set `PLANNER_BACKEND=anthropic` and use `AnthropicPlanner`

---

### 2.2 LLM Adapter Stub
| Property | Value |
|----------|-------|
| **File** | `/backend/app/skills/llm_invoke_v2.py` |
| **Class** | `StubAdapter(LLMAdapter)` |
| **Mocks** | LLM provider interface |
| **Real Plugin Needed** | YES - Use real adapter implementations |

**Available Real Adapters:**
- `ClaudeAdapter` - Anthropic Claude (primary)
- Future: OpenAI, local LLMs

---

## 3. PERSISTENCE STUBS (Infrastructure-Critical)

### 3.1 In-Memory Checkpoint Store
| Property | Value |
|----------|-------|
| **File** | `/backend/app/workflow/checkpoint.py` |
| **Class** | `InMemoryCheckpointStore(CheckpointStore)` |
| **Mocks** | Database-backed checkpoint persistence |
| **Real Plugin Needed** | YES - PostgreSQL implementation |

**Limitations:**
- Loses data on process exit
- No multi-process support
- Single-instance only

**Production Path:** Use `PostgresCheckpointStore` (needs implementation or exists)

---

### 3.2 In-Memory Budget Store
| Property | Value |
|----------|-------|
| **File** | `/backend/app/workflow/policies.py` |
| **Class** | `InMemoryBudgetStore(BudgetStore)` |
| **Mocks** | Redis-backed budget tracking |
| **Real Plugin Needed** | YES - Redis implementation |

**Limitations:**
- No persistence
- No multi-process budget synchronization

**Production Path:** Use Redis-backed store (Upstash in production)

---

### 3.3 In-Memory Trace Store
| Property | Value |
|----------|-------|
| **File** | `/backend/app/traces/store.py` |
| **Class** | `InMemoryTraceStore(TraceStore)` |
| **Mocks** | SQLite/PostgreSQL trace storage |
| **Real Plugin Needed** | YES - Already has PostgreSQL implementation |

**Production Path:** Set `USE_POSTGRES_TRACES=true`

---

### 3.4 In-Memory Idempotency Store
| Property | Value |
|----------|-------|
| **File** | `/backend/app/traces/idempotency.py` |
| **Class** | `InMemoryIdempotencyStore(IdempotencyStore)` |
| **Mocks** | Redis-backed idempotency tracking |
| **Real Plugin Needed** | YES - Redis implementation |

**Limitations:**
- No TTL management
- No persistence

---

### 3.5 In-Memory Golden Recorder
| Property | Value |
|----------|-------|
| **File** | `/backend/app/workflow/golden.py` |
| **Class** | `InMemoryGoldenRecorder(GoldenRecorder)` |
| **Mocks** | File-based golden file recording |
| **Real Plugin Needed** | YES - Filesystem implementation |

**Production Path:** Use `FileGoldenRecorder` for CI golden file tests

---

## 4. OBSERVABILITY STUBS

### 4.1 Stub Metrics (Prometheus)
| Property | Value |
|----------|-------|
| **Files** | `/backend/app/workflow/metrics.py`, `/backend/app/traces/traces_metrics.py` |
| **Classes** | `StubCounter`, `StubHistogram`, `StubGauge`, `StubMetric` |
| **Mocks** | Prometheus metrics when unavailable |
| **Real Plugin Needed** | YES - Real Prometheus client |

**Activation:** Set `PROMETHEUS_AVAILABLE=True` (auto-detected)

---

### 4.2 Alertmanager Mock
| Property | Value |
|----------|-------|
| **File** | `/backend/tests/integration/conftest.py` |
| **Class** | `AlertmanagerMock` |
| **Mocks** | Alertmanager HTTP API |
| **Real Plugin Needed** | YES - Real Alertmanager in production |

**Test-only:** Captures alert payloads for verification

---

## 5. WIREMOCK STATUS

**Finding: NO WireMock configuration found in the codebase.**

The project uses custom Python stubs instead of WireMock for HTTP mocking. This is a deliberate architectural choice for:
- Tighter integration with Python testing
- Deterministic behavior guarantees
- No external service dependencies in tests

---

## 6. MOCKS REQUIRING REAL-WORLD PLUGINS (Priority List)

### Tier 1: Production-Blocking
| Mock | Real Implementation | Status |
|------|---------------------|--------|
| `LlmInvokeStub` | `ClaudeAdapter` | EXISTS |
| `StubPlanner` | `AnthropicPlanner` | EXISTS |
| `HttpCallStub` | `HttpCallV2` | EXISTS |

### Tier 2: Infrastructure-Blocking
| Mock | Real Implementation | Status |
|------|---------------------|--------|
| `InMemoryCheckpointStore` | PostgreSQL store | NEEDS VERIFICATION |
| `InMemoryBudgetStore` | Redis store | NEEDS IMPLEMENTATION |
| `InMemoryIdempotencyStore` | Redis store | NEEDS IMPLEMENTATION |
| `InMemoryTraceStore` | PostgreSQL store | EXISTS (`USE_POSTGRES_TRACES=true`) |

### Tier 3: Observability
| Mock | Real Implementation | Status |
|------|---------------------|--------|
| `StubCounter/Histogram/Gauge` | Prometheus client | AUTO-DETECTED |
| `AlertmanagerMock` | Real Alertmanager | DEPLOYED |

### Tier 4: Test-Only (No Production Plugin Needed)
| Mock | Purpose |
|------|---------|
| `JsonTransformStub` | Already deterministic (IS production) |
| `InMemoryGoldenRecorder` | CI test golden files only |
| `AlertmanagerMock` | Test verification only |

---

## 7. ENVIRONMENT FLAGS FOR STUB/REAL SWITCHING

```bash
# LLM/Planner
PLANNER_BACKEND=anthropic|stub          # Planner selection
ANTHROPIC_API_KEY=sk-...                # Required for real Claude

# Persistence
USE_POSTGRES_TRACES=true|false          # Trace store backend
REDIS_URL=redis://...                   # Redis for budget/idempotency

# Auth
RBAC_ENFORCE=true|false                 # RBAC enforcement
JWT_VERIFY_SIGNATURE=true|false         # JWT validation

# Observability
PROMETHEUS_AVAILABLE=true|false         # Auto-detected

# Testing
DISABLE_EXTERNAL_CALLS=1                # Block real HTTP in CI
```

---

## 8. RECOMMENDED ACTIONS

### Immediate (M11)
1. Verify `PostgresCheckpointStore` exists and is wired
2. Implement `RedisBudgetStore` for production budget enforcement
3. Implement `RedisIdempotencyStore` for request deduplication

### Near-term
4. Add integration tests that exercise real adapters (non-stub)
5. Document stub → real switching procedure
6. Add health checks for external dependencies (Claude, Redis)

### Future
7. Consider WireMock for complex HTTP scenario testing
8. Add circuit breaker around all external calls
9. Implement streaming support in HTTP and LLM skills

---

## 9. VERIFICATION COMMANDS

```bash
# Check which stubs are registered
PYTHONPATH=. python3 -c "from app.skills.registry import registry; print([s for s in registry.list_skills() if getattr(registry.get_skill(s), 'is_stub', False)])"

# Check planner backend
echo $PLANNER_BACKEND

# Check trace store mode
echo $USE_POSTGRES_TRACES

# Verify Claude adapter availability
PYTHONPATH=. python3 -c "from app.skills.adapters.claude_adapter import ClaudeAdapter; print('ClaudeAdapter available')"
```

---

## References

- PIN-046: Stub Replacement & pgvector
- PIN-038: Upstash Redis Integration
- `/backend/app/skills/stubs/` - All skill stubs
- `/backend/app/planners/` - Planner implementations
- `/backend/tests/conftest.py` - Test fixtures
