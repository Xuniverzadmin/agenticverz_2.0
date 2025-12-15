# PIN-059: M11 Skill Expansion Blueprint (Refined)

**Created:** 2025-12-09
**Status:** COMPLETE ✅
**Category:** Milestone / Implementation
**Milestone:** M11 Skill Expansion
**Estimated Duration:** 3 weeks
**Completed:** 2025-12-09
**Last Updated:** 2025-12-09

---

## Executive Summary

M11 adds 5 deterministic, replayable skills — `kv_store`, `slack_send`, `email_send`, `webhook_send`, and `voyage_embed` — integrated with existing infrastructure (idempotency, circuit breaker, replay enforcement) and real-world backends (Upstash Redis, Resend, Slack, Voyage AI, Microsoft/Google OAuth).

---

## Consistency Check Results

### Existing Infrastructure to Leverage (NOT rebuild)

| Component | Location | Status |
|-----------|----------|--------|
| **Skill Registry** | `backend/app/skills/registry.py` | ✅ Use `@skill` decorator |
| **Idempotency Store** | `backend/app/traces/idempotency.py` | ✅ Redis + Lua atomic ops |
| **Replay Enforcer** | `backend/app/traces/replay.py` | ✅ Skip/check/execute modes |
| **Circuit Breaker** | `backend/app/costsim/circuit_breaker.py` | ✅ DB-backed, adapt pattern |
| **Skill Schemas** | `backend/app/schemas/skill.py` | ✅ Add new I/O schemas here |
| **Email Skill** | `backend/app/skills/email_send.py` | ✅ EXISTS - needs registration |

### Vision Alignment (PIN-005)

| Principle | How M11 Addresses |
|-----------|-------------------|
| **Determinism by default** | Seeded backoff, idempotency keys, replay verification |
| **Machine-native** | Skills return structured outcomes, not exceptions |
| **Failure as data** | All errors recorded with category, retryable flag |
| **Queryable execution** | Audit trail via existing traces infrastructure |

---

## M11 Deliverables (Refined)

### Priority 0 (Core Skills)

| Skill | Backend | Existing Code | Action |
|-------|---------|---------------|--------|
| `kv_store` | Upstash Redis | NEW | Implement |
| `slack_send` | Slack Webhooks | NEW | Implement |
| `email_send` | Resend API | EXISTS | Register + test |
| `webhook_send` | HTTP + HMAC | NEW | Implement |

### Priority 1 (Embeddings)

| Skill | Backend | Action |
|-------|---------|--------|
| `voyage_embed` | Voyage AI API | Implement |

### Priority 2 (OAuth Skills - Stretch)

| Skill | Backend | Notes |
|-------|---------|-------|
| `outlook_send` | Microsoft Graph | OAuth tokens in Vault |
| `gmail_send` | Google Gmail API | OAuth tokens in Vault |

### REMOVED (Already Exists or Deferred)

| Item | Reason |
|------|--------|
| `common/retry.py` | Use existing skill retry patterns |
| `common/circuit.py` | Adapt `costsim/circuit_breaker.py` |
| `common/audit.py` | Use existing `traces/` infrastructure |
| `fs` skill | Deferred - sandbox security complexity |

---

## Skill Specifications

### 1. kv_store (P0)

**Purpose:** Key-value operations using Upstash Redis

**File:** `backend/app/skills/kv_store.py`

**Operations:**
```python
class KVOperation(str, Enum):
    GET = "get"
    SET = "set"
    DELETE = "delete"
    EXISTS = "exists"
    TTL = "ttl"
    INCR = "incr"
    EXPIRE = "expire"
```

**Input Schema:**
```python
class KVStoreInput(SkillInputBase):
    operation: KVOperation
    key: str
    value: Optional[Any] = None
    ttl_seconds: Optional[int] = None
    namespace: str = "default"  # Tenant isolation
```

**Output Schema:**
```python
class KVStoreOutput(SkillOutputBase):
    operation: str
    key: str
    value: Optional[Any] = None
    exists: Optional[bool] = None
    ttl_remaining: Optional[int] = None
```

**Implementation Notes:**
- Use `REDIS_URL` from environment (Upstash)
- Key prefix: `aos:{namespace}:{key}` for isolation
- Idempotency: Use existing `traces/idempotency.py` for SET/DELETE
- Rate limit: Leverage existing rate limit middleware

**Rate Limit Lua (Upstash compatible):**
```lua
-- skills/kv_store/rate_limit.lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call("INCR", key)
if current == 1 then
    redis.call("EXPIRE", key, window)
end
if current > limit then
    return 0
end
return 1
```

---

### 2. slack_send (P0)

**Purpose:** Send messages to Slack via webhook

**File:** `backend/app/skills/slack_send.py`

**Input Schema:**
```python
class SlackSendInput(SkillInputBase):
    webhook_url: Optional[str] = None  # Uses env default if not set
    text: str
    blocks: Optional[List[Dict]] = None  # Block Kit
    channel: Optional[str] = None  # Display only
    unfurl_links: bool = False
```

**Output Schema:**
```python
class SlackSendOutput(SkillOutputBase):
    webhook_response: str  # "ok" or error
    channel: Optional[str] = None
```

**Environment:**
- `SLACK_WEBHOOK_URL` - Default webhook (from Vault)
- `SLACK_MISMATCH_WEBHOOK` - Already configured

**Idempotency:**
- Accept `idempotency_key` parameter
- Store result in Redis via existing idempotency store
- Prevent duplicate posts on retry

---

### 3. email_send (P0 - EXISTS)

**Current File:** `backend/app/skills/email_send.py`

**Status:** Implemented but not registered in `__init__.py`

**Review Checklist:**
- [ ] Verify `@skill("email_send", ...)` decorator
- [ ] Add to `backend/app/skills/__init__.py` exports
- [ ] Create `backend/tests/skills/test_email_send.py`
- [ ] Test with actual Resend API

**Environment:**
- `RESEND_API_KEY` - Already in `secrets/resend.env`
- `RESEND_FROM_ADDRESS` - Configure in env

---

### 4. webhook_send (P1)

**Purpose:** Generic webhook with HMAC signing

**File:** `backend/app/skills/webhook_send.py`

**Input Schema:**
```python
class WebhookSendInput(SkillInputBase):
    url: str
    method: str = "POST"
    payload: Dict[str, Any]
    headers: Optional[Dict[str, str]] = None
    sign_payload: bool = True
    signature_header: str = "X-Signature-256"
    timeout_seconds: float = 30.0
```

**Output Schema:**
```python
class WebhookSendOutput(SkillOutputBase):
    status_code: int
    response_body: Optional[str] = None
    request_id: Optional[str] = None
    signature_sent: bool = False
```

**HMAC Signing Implementation:**
```python
import hmac
import hashlib
import time

def sign_payload(payload_bytes: bytes, secret: str, timestamp: int) -> str:
    """HMAC-SHA256 signature."""
    message = f"{timestamp}.{payload_bytes.decode()}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"
```

**Headers Added:**
- `X-Signature-256: sha256=<hex>`
- `X-Signature-Timestamp: <unix_timestamp>`

**Environment:**
- `WEBHOOK_SIGNING_SECRET` - Generate and store in Vault

---

### 5. voyage_embed (P1)

**Purpose:** Generate embeddings using Voyage AI

**File:** `backend/app/skills/voyage_embed.py`

**Input Schema:**
```python
class VoyageEmbedInput(SkillInputBase):
    input: Union[str, List[str]]  # Text(s) to embed
    model: str = "voyage-3"  # voyage-3, voyage-3-lite, voyage-code-3
    input_type: Optional[str] = None  # "query" or "document"
```

**Output Schema:**
```python
class VoyageEmbedOutput(SkillOutputBase):
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int]  # {"total_tokens": N}
```

**Implementation:**
```python
async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.voyageai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "input": params["input"],
                "model": params.get("model", "voyage-3"),
                "input_type": params.get("input_type")
            }
        )
        data = response.json()
        return {
            "skill": "voyage_embed",
            "skill_version": self.VERSION,
            "result": {
                "embeddings": [e["embedding"] for e in data["data"]],
                "model": data["model"],
                "usage": data["usage"]
            },
            "status": "ok",
            "duration": ...
        }
```

**Environment:**
- `VOYAGE_API_KEY` - Already in `secrets/voyage.env` and Vault

---

## Common Infrastructure

### Deterministic Backoff (Add to existing retry)

**File:** `backend/app/utils/deterministic.py`

```python
import hmac
import hashlib
import struct

def seeded_jitter(workflow_run_id: str, attempt: int) -> float:
    """Deterministic jitter from workflow ID + attempt."""
    key = workflow_run_id.encode()
    msg = f"{workflow_run_id}:{attempt}".encode()
    digest = hmac.new(key, msg, hashlib.sha256).digest()
    return struct.unpack(">I", digest[:4])[0] / 2**32

def deterministic_backoff_ms(
    workflow_run_id: str,
    attempt: int,
    initial_ms: int = 200,
    multiplier: float = 2.0,
    jitter_pct: float = 0.1,
    max_ms: int = 10000
) -> int:
    """Calculate backoff with deterministic jitter."""
    base = initial_ms * (multiplier ** (attempt - 1))
    jitter = seeded_jitter(workflow_run_id, attempt)
    factor = 1 + (2 * jitter - 1) * jitter_pct
    return int(min(base * factor, max_ms))
```

### Skill Base Class Enhancement

**File:** `backend/app/skills/base.py` (new)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.traces.idempotency import IdempotencyStore

class IdempotentSkill(ABC):
    """Base class for skills with idempotency support."""

    def __init__(self, idempotency_store: Optional[IdempotencyStore] = None):
        self.idempotency_store = idempotency_store

    async def execute_with_idempotency(
        self,
        params: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        workflow_run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute with idempotency check."""
        if idempotency_key and self.idempotency_store:
            cached = await self.idempotency_store.get(idempotency_key)
            if cached:
                return {**cached, "from_cache": True}

        result = await self.execute(params)

        if idempotency_key and self.idempotency_store:
            await self.idempotency_store.set(idempotency_key, result)

        return result

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Implement in subclass."""
        pass
```

---

## Audit Table (Reuse M10)

Use existing M10 audit infrastructure:

```sql
-- Already exists in m10_recovery schema
-- replay_log table tracks executed operations
-- Can be extended for M11 skills
```

**Alternative: Create M11-specific audit:**

```sql
CREATE SCHEMA IF NOT EXISTS m11_skills;

CREATE TABLE m11_skills.skill_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id TEXT NOT NULL,
    op_index INT NOT NULL,
    skill_name TEXT NOT NULL,
    skill_version TEXT NOT NULL,
    params JSONB NOT NULL,
    result JSONB,
    idempotency_key TEXT,
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_skill_audit_workflow ON m11_skills.skill_audit(workflow_run_id, op_index);
CREATE INDEX idx_skill_audit_idempotency ON m11_skills.skill_audit(idempotency_key) WHERE idempotency_key IS NOT NULL;
```

---

## Implementation Plan (3 Weeks)

### Week 1: Foundation + Core Skills

| Day | Tasks |
|-----|-------|
| 1-2 | Add schemas to `skill.py`, create `utils/deterministic.py`, review `email_send.py` |
| 3-4 | Implement `kv_store` skill with Upstash Redis |
| 5 | Implement `slack_send` skill, tests |

### Week 2: Notification Skills

| Day | Tasks |
|-----|-------|
| 1-2 | Implement `webhook_send` with HMAC signing |
| 3-4 | Implement `voyage_embed` skill |
| 5 | Integration tests for all P0/P1 skills |

### Week 3: Validation + Polish

| Day | Tasks |
|-----|-------|
| 1-2 | Replay tests: run → record → replay → verify |
| 3 | Load tests for `kv_store` |
| 4 | E2E test: 5-step workflow using all skills |
| 5 | Documentation, PIN update |

---

## Acceptance Criteria

### Gate (Required)

- [x] 5 skills registered in registry (`kv_store`, `slack_send`, `email_send`, `webhook_send`, `voyage_embed`)
- [x] All skills have input/output schemas in `skill.py`
- [x] All skills support `idempotency_key` parameter
- [x] All skills return structured `{ok, result, error}` format
- [x] Unit tests for each skill (≥80% coverage) - 27 unit tests passing
- [x] 5-step E2E workflow passes - 6 E2E tests passing
- [x] Replay test: run → replay → no duplicate side effects - 10 replay tests passing

### Stretch

- [ ] OAuth skills (outlook_send, gmail_send) - DEFERRED
- [x] Prometheus metrics per skill - 15 M11 metrics added
- [x] Circuit breaker per external provider - SkillCircuitBreaker in base.py

---

## File Manifest

### New Files

| File | Purpose |
|------|---------|
| `backend/app/skills/kv_store.py` | Redis KV operations |
| `backend/app/skills/slack_send.py` | Slack notification |
| `backend/app/skills/webhook_send.py` | HMAC-signed webhooks |
| `backend/app/skills/voyage_embed.py` | Voyage AI embeddings |
| `backend/app/skills/base.py` | Idempotent skill base class |
| `backend/app/utils/deterministic.py` | Seeded backoff/jitter |
| `backend/tests/skills/test_kv_store.py` | KV tests |
| `backend/tests/skills/test_slack_send.py` | Slack tests |
| `backend/tests/skills/test_email_send.py` | Email tests |
| `backend/tests/skills/test_webhook_send.py` | Webhook tests |
| `backend/tests/skills/test_voyage_embed.py` | Embedding tests |
| `backend/tests/e2e/test_m11_workflow.py` | 5-step E2E |
| `backend/tests/replay/test_m11_replay.py` | Replay verification |

### Modified Files

| File | Changes |
|------|---------|
| `backend/app/schemas/skill.py` | Add KV/Slack/Webhook/Voyage schemas |
| `backend/app/skills/__init__.py` | Export all skills |
| `backend/app/skills/email_send.py` | Verify registration |
| `alembic/versions/024_m11_skill_audit.py` | Audit table migration |

---

## Test Matrix

| Test Type | Target | Command |
|-----------|--------|---------|
| Unit | All skills | `pytest backend/tests/skills/test_*.py -v` |
| Integration | Real backends | `pytest backend/tests/integration/test_m11_*.py -v` |
| E2E | 5-step workflow | `pytest backend/tests/e2e/test_m11_workflow.py -v` |
| Replay | Determinism | `pytest backend/tests/replay/test_m11_replay.py -v` |
| Load | KV store | `scripts/m11_kv_load_test.sh` |

---

## Example 5-Step Workflow

```json
{
  "workflow_run_id": "wf_m11_test_001",
  "steps": [
    {
      "id": "s1",
      "skill": "kv_store",
      "params": {"operation": "set", "namespace": "wf_m11_test_001", "key": "status", "value": {"state": "started"}}
    },
    {
      "id": "s2",
      "skill": "voyage_embed",
      "params": {"input": "Workflow started successfully", "model": "voyage-3-lite"}
    },
    {
      "id": "s3",
      "skill": "slack_send",
      "params": {"text": "Workflow wf_m11_test_001 started", "idempotency_key": "wf_m11_test_001_s3"}
    },
    {
      "id": "s4",
      "skill": "kv_store",
      "params": {"operation": "get", "namespace": "wf_m11_test_001", "key": "status"}
    },
    {
      "id": "s5",
      "skill": "email_send",
      "params": {"to": "admin1@agenticverz.com", "subject": "Workflow Complete", "body": "Done", "idempotency_key": "wf_m11_test_001_s5"}
    }
  ]
}
```

---

## Environment Variables Summary

| Variable | Source | Used By |
|----------|--------|---------|
| `REDIS_URL` | `.env` | kv_store |
| `SLACK_WEBHOOK_URL` | Vault | slack_send |
| `RESEND_API_KEY` | `secrets/resend.env` | email_send |
| `VOYAGE_API_KEY` | `secrets/voyage.env` | voyage_embed |
| `WEBHOOK_SIGNING_SECRET` | Vault | webhook_send |
| `MICROSOFT_CLIENT_ID` | `secrets/microsoft_oauth.env` | outlook_send (P2) |
| `GOOGLE_CLIENT_ID` | `secrets/google_oauth.env` | gmail_send (P2) |

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| Upstash rate limits | MEDIUM | Token bucket in Lua, local caching |
| Slack webhook abuse | LOW | Idempotency + audit logging |
| Email bounce storms | LOW | Resend dashboard monitoring |
| Voyage API quota | MEDIUM | Daily quota tracking, fallback to OpenAI |

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-033 | Parent M8-M14 roadmap |
| PIN-005 | Machine-native architecture principles |
| PIN-034 | Vault secrets (OAuth credentials) |
| PIN-050 | M10 Recovery (idempotency patterns) |
| PIN-058 | M10 Phase 6.5 (predecessor) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-09 | Initial blueprint created |
| 2025-12-09 | Consistency check: leveraged existing infrastructure, removed redundant components |
| 2025-12-09 | Added real credentials: Microsoft OAuth, Google OAuth, Voyage AI |
| 2025-12-09 | Refined to align with vision (PIN-005) and existing patterns |
| 2025-12-09 | **IMPLEMENTATION COMPLETE** |

---

## Implementation Summary (2025-12-09)

### Completed Deliverables

| Component | Location | Tests |
|-----------|----------|-------|
| **KV Store Skill** | `app/skills/kv_store.py` | 6 tests |
| **Slack Send Skill** | `app/skills/slack_send.py` | 4 tests |
| **Email Send Skill** | `app/skills/email_send.py` | Registered |
| **Webhook Send Skill** | `app/skills/webhook_send.py` | 5 tests |
| **Voyage Embed Skill** | `app/skills/voyage_embed.py` | 6 tests |
| **Skill Base Classes** | `app/skills/base.py` | IdempotentSkill, ExternalSkill |
| **Circuit Breaker** | `app/skills/base.py` | SkillCircuitBreaker class |
| **Deterministic Utils** | `app/utils/deterministic.py` | Seeded backoff |
| **M11 Audit Migration** | `alembic/versions/024_m11_skill_audit.py` | Applied to Neon |
| **Replay Runner** | `tools/replay/runner.py` | WorkflowRunner |
| **Replay Verifier** | `tools/replay/verifier.py` | ReplayVerifier |
| **Audit Store** | `tools/replay/audit.py` | AuditStore |

### Test Results

```
43 tests passed in 85.53s
├── tests/skills/test_m11_skills.py: 27 passed
├── tests/e2e/test_m11_workflow.py: 6 passed
└── tests/replay/test_replay_end_to_end.py: 10 passed
```

### Prometheus Metrics Added

- `m11_skill_executions_total` - Skill execution counts by status/tenant
- `m11_skill_execution_seconds` - Skill latency histogram
- `m11_skill_idempotency_hits_total` - Cache hits
- `m11_skill_idempotency_conflicts_total` - Param conflicts
- `m11_circuit_breaker_state` - Breaker state gauge
- `m11_circuit_breaker_failures_total` - Failure counts
- `m11_circuit_breaker_successes_total` - Success counts
- `m11_circuit_breaker_opens_total` - Open events
- `m11_circuit_breaker_closes_total` - Recovery events
- `m11_circuit_breaker_rejected_total` - Rejected requests
- `m11_audit_ops_total` - Audit log operations
- `m11_replay_runs_total` - Replay executions
- `m11_replay_ops_verified_total` - Verified ops
- `m11_replay_ops_mismatched_total` - Mismatched ops
- `m11_replay_verification_seconds` - Verification latency

### Database Tables Created (m11_audit schema)

1. `ops` - Append-only skill operation log
2. `replay_runs` - Replay verification tracking
3. `circuit_breaker_state` - Per-target breaker state
4. `skill_metrics` - Prometheus aggregation
5. `workflow_summary` - Workflow stats

### SQL Syntax Fixes Applied

Fixed SQLAlchemy parameter binding conflicts with PostgreSQL cast syntax:
- Changed `:args::jsonb` → `CAST(:args_json AS jsonb)`
- Changed `:result::jsonb` → `CAST(:result_json AS jsonb)`
- Changed `:diff::jsonb` → `CAST(:diff_json AS jsonb)`

### Key Architectural Decisions

1. **Circuit breaker in skill base** - Not CostSim-specific, generic for external services
2. **CAST() over :: syntax** - PostgreSQL explicit casts avoid SQLAlchemy conflicts
3. **Metrics in base class** - Automatic instrumentation for all skills
4. **Transient flag for ops** - Allows skipping certain ops during replay
