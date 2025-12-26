# PIN-162: P2FC-4 — Scoped Execution Gate

**Status:** COMPLETE
**Created:** 2025-12-24
**Category:** Architecture / Recovery / Safety
**Milestone:** M6 Promotion (P2FC)
**Parent:** [PIN-161](PIN-161-p2fc-partial-to-full-consume.md)

---

## Summary

Implementation of scope-gated recovery execution as the M6 promotion requirement. No recovery action can execute without an explicit, bounded execution scope derived from incident context.

---

## Core Invariant

> **"A recovery action without a valid execution scope is invalid by definition."**

This is non-negotiable. M6 is about **restraint**, not convenience.

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/recovery/scope` | POST | Create bound scope (Gate Step) |
| `/api/v1/recovery/execute` | POST | Execute with scope (FAILS without) |
| `/api/v1/recovery/scopes/{incident_id}` | GET | List scopes for incident |
| `/api/v1/recovery/scopes/{scope_id}` | DELETE | Revoke scope |

---

## BoundExecutionScope Model

```python
@dataclass
class BoundExecutionScope:
    scope_id: str              # Unique identifier
    incident_id: str           # Incident binding (scope is incident-specific)
    allowed_actions: List[str] # Only listed actions can execute
    max_cost_usd: float        # Cost ceiling ($0.50 default)
    max_attempts: int          # Execution limit (1 = single-use)
    expires_at: datetime       # Time-bound expiry (5 min default)
    intent: str                # Why this action is allowed
    target_agents: List[str]   # Optional agent targeting
    status: str                # active/exhausted/expired/revoked
```

---

## Exception Hierarchy

| Exception | HTTP | Trigger |
|-----------|------|---------|
| `ScopedExecutionRequired` | 400 | No scope_id provided |
| `ScopeNotFound` | 404 | Invalid scope_id |
| `ScopeExhausted` | 400 | max_attempts consumed |
| `ScopeExpired` | 400 | TTL exceeded |
| `ScopeActionMismatch` | 403 | Action not in allowed_actions |
| `ScopeIncidentMismatch` | 403 | Wrong incident_id |

---

## Test Script Compliance

| Step | Test | Expected | Status |
|------|------|----------|--------|
| A1 | Execute without scope | 400 `scoped_execution_required` | ✅ |
| A2 | Create scope | `scope_id`, `expires_at`, `intent` | ✅ |
| A3 | Execute with scope | Success, scope consumed | ✅ |
| A4 | Reuse exhausted scope | 400 `scope_exhausted` | ✅ |
| A5 | Different action | 403 `action_outside_scope` | ✅ |

---

## Kill Criteria Verification

| Criterion | Status | Enforcement |
|-----------|--------|-------------|
| Recovery executes without scope | ❌ BLOCKED | `validate_scope_required()` |
| Scope auto-created without intent | ❌ BLOCKED | Intent required in request |
| Scope reused across incidents | ❌ BLOCKED | `ScopeIncidentMismatch` |
| Cost exceeds scope silently | ❌ TRACKED | `cost_used_usd` tracking |
| Scope hidden from user | ❌ VISIBLE | `GET /scopes/{incident_id}` |

---

## Usage Example

```bash
# Step 1: Attempt execute without scope → FAIL
curl -X POST http://localhost:8000/api/v1/recovery/execute \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "inc_123", "action": "retry_agent"}'
# → 400: {"error": "scoped_execution_required", ...}

# Step 2: Create scope
curl -X POST http://localhost:8000/api/v1/recovery/scope \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc_123",
    "action": "retry_agent",
    "intent": "Recover from hallucinated legal response",
    "max_cost_usd": 0.50,
    "max_attempts": 1
  }'
# → 201: {"scope_id": "scope_abc123...", "expires_at": "...", ...}

# Step 3: Execute with scope → SUCCESS
curl -X POST http://localhost:8000/api/v1/recovery/execute \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc_123",
    "action": "retry_agent",
    "scope_id": "scope_abc123..."
  }'
# → 200: {"success": true, "scope_status": "exhausted", ...}

# Step 4: Reuse scope → FAIL
# → 400: {"error": "scope_exhausted", ...}

# Step 5: Different action → FAIL
# → 403: {"error": "action_outside_scope", ...}
```

---

## Files Changed

| File | Changes |
|------|---------|
| `backend/app/services/scoped_execution.py` | BoundExecutionScope, ScopeStore, exceptions, API functions |
| `backend/app/api/recovery.py` | 4 new endpoints (scope, execute, list, revoke) |

---

## Memory Pin Mapping

| Memory Pin | Meaning | Status |
|------------|---------|--------|
| PIN-148 | Incident lifecycle | ✅ Required |
| PIN-161 | P2FC execution plan | ✅ Parent |
| PIN-162 | Scoped execution gate | ✅ This PIN |

---

## Next Steps (Console UI)

```
□ Add Recovery section to Incident detail page
□ Show scope summary (action, cost ceiling, status)
□ Hide "Run" button when no scope exists
□ Add text: "All recovery actions are scoped and audited"
```

---

## Related PINs

- [PIN-161](PIN-161-p2fc-partial-to-full-consume.md) - P2FC execution plan (parent)
- [PIN-148](PIN-148-m29-categorical-next-steps.md) - Incident lifecycle
- [PIN-050](PIN-050-m10-recovery-suggestion-engine-complete.md) - Recovery engine

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-24 | Created PIN-162 with full scope gating implementation |
