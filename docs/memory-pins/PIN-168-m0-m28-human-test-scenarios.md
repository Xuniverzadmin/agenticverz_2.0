# PIN-168: M0-M28 Human Test Scenarios

**Status:** READY FOR EXECUTION
**Category:** Testing / Human Validation / M0-M28 Coverage
**Created:** 2025-12-25
**Milestone:** Post-M25 Final Review
**Parent:** PIN-167 (Final Review Tasks)

---

## Summary

This PIN documents recommended human test scenarios covering M0-M28 capabilities not covered by the initial 6 scenarios in PIN-167. These scenarios are designed to test system visibility, predictability, and truthfulness from a human operator perspective.

---

## Context

### Completed Scenarios (PIN-167)

| # | Scenario | Match | Coverage |
|---|----------|-------|----------|
| 1 | Incident Creation | PARTIAL | M0-M3 (Request, Auth) |
| 2 | Execution Routing | NO | M15-M20 (CARE) |
| 3 | Recovery Suggestion | PARTIAL | M9-M10 (Recovery) |
| 4 | Policy Consequence | PARTIAL | M5 (Policy) |
| 5 | Cost/Ops Visibility | PARTIAL | M26 (Cost Loop) |
| 6 | Memory Carryover | NO | M7 (Memory) |

**Overall Result:** FAIL (3/4 exit criteria failed)

### Gaps Identified

- CARE routing invisible
- Memory opaque
- Budget advisory only
- Recovery siloed from workflows
- Monitoring undocumented

---

## Recommended Additional Scenarios

### Priority 0 (P0) - Core Visibility Gaps

#### Scenario 7: Multi-Skill Execution
**Tests:** M2-M3 (Skills Framework)

| Skill | Purpose | Testable Behavior |
|-------|---------|-------------------|
| `http_call` | External API calls | Timeout/retry visibility |
| `webhook_send` | Outbound webhooks | Delivery confirmation |
| `json_transform` | Data transformation | Error clarity |
| `fs_read`/`fs_write` | File operations | Access logging |
| `email_send` | Email delivery | Cost tracking |

**Test Steps:**
```bash
# 1. List available skills
curl -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/runtime/skills

# 2. Describe each skill
curl -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/runtime/skills/http_call

# 3. Execute skill with intentional timeout
curl -X POST -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/runtime/simulate \
  -d '{"plan": [{"skill": "http_call", "params": {"url": "http://httpstat.us/504"}}]}'
```

**Question:** Can a human understand which skills are available and their failure modes?

---

#### Scenario 8: RBAC Permission Enforcement
**Tests:** M7 (RBAC)

**Test Steps:**
```bash
# 1. Query RBAC info
curl -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/rbac/info

# 2. Attempt elevated operation without permission
curl -X POST -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/memory/pins \
  -d '{"key": "test", "value": {"data": "test"}}'

# 3. Check audit trail
curl -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/rbac/audit
```

**Question:** Is permission denial predictable and explainable?

---

#### Scenario 9: Circuit Breaker Behavior
**Tests:** M11 (Skill Expansion)

**Test Steps:**
```bash
# 1. Force 5+ failures on a skill (hit timeout endpoint)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/runtime/simulate \
    -d '{"plan": [{"skill": "http_call", "params": {"url": "http://httpstat.us/500"}}]}'
done

# 2. Check if circuit breaker opened
curl http://localhost:8000/api/v1/runtime/skills/http_call

# 3. Wait for cooldown (60s) and retry
sleep 65
curl http://localhost:8000/api/v1/runtime/skills/http_call
```

**Question:** Does the system explain why a skill is unavailable?

---

#### Scenario 10: Checkpoint & Resume
**Tests:** M4 (Workflow Engine)

**Test Steps:**
```bash
# 1. Create long-running workflow
curl -X POST -H "X-AOS-Key: $KEY" \
  http://localhost:8000/api/v1/workers/business-builder/run \
  -d '{"task": "Complex multi-step task", "budget_tokens": 10000}'

# 2. Query checkpoints
curl -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/integration/checkpoints

# 3. Attempt resume from checkpoint
curl -X POST http://localhost:8000/api/v1/integration/checkpoints/{id}/resolve
```

**Question:** Can a human understand execution state after interruption?

---

#### Scenario 11: Integration Loop Lifecycle
**Tests:** M25 (Integration Bridges)

**Test Steps:**
```bash
# 1. Find a failed run (incident)
curl -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/runs?status=failed

# 2. Get integration loop stages
curl -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/integration/loop/{id}/stages

# 3. Get narrative summary
curl -H "X-AOS-Key: $KEY" http://localhost:8000/api/v1/integration/loop/{id}/narrative
```

**Question:** Is the incident-to-prevention loop visible and understandable?

---

#### Scenario 12: Event Streaming (Real-time)
**Tests:** M8, M24 (Event Publishing)

**Test Steps:**
```bash
# 1. Start SSE stream
curl -N -H "X-AOS-Key: $KEY" \
  http://localhost:8000/api/v1/workers/business-builder/stream/{run_id}

# 2. In another terminal, trigger workflow
curl -X POST -H "X-AOS-Key: $KEY" \
  http://localhost:8000/api/v1/workers/business-builder/run-streaming \
  -d '{"task": "Test streaming"}'

# 3. Observe events in stream
```

**Question:** Can a human follow execution progress in real-time?

---

### Priority 1 (P1) - Safety & Isolation

#### Scenario 13: Killswitch Activation
**Tests:** M22 (KillSwitch MVP)

**Test Steps:**
```bash
# 1. Check killswitch status
curl http://localhost:8000/api/v1/killswitch/status

# 2. Activate killswitch
curl -X POST http://localhost:8000/api/v1/killswitch/activate

# 3. Attempt workflow (should fail)
curl -X POST http://localhost:8000/api/v1/workers/business-builder/run \
  -d '{"task": "Should be blocked"}'

# 4. Reset killswitch
curl -X POST http://localhost:8000/api/v1/killswitch/reset
```

**Question:** Is emergency stop behavior obvious?

---

#### Scenario 14: Tenant Isolation
**Tests:** M21 (Multi-Tenancy)

**Test Steps:**
```bash
# 1. Create tenant A
curl -X POST http://localhost:8000/api/v1/tenants \
  -d '{"name": "tenant_a", "plan": "beta"}'

# 2. Create tenant B
curl -X POST http://localhost:8000/api/v1/tenants \
  -d '{"name": "tenant_b", "plan": "beta"}'

# 3. Run workflow as tenant A
# 4. Attempt to query A's data as B
# 5. Verify isolation
```

**Question:** Is data boundary enforcement clear?

---

#### Scenario 15: Cost Anomaly Detection
**Tests:** M26 (Cost Intelligence)

**Test Steps:**
```bash
# 1. Run several normal-cost workflows
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/workers/business-builder/run \
    -d '{"task": "Small task", "budget_tokens": 1000}'
done

# 2. Run one high-cost workflow
curl -X POST http://localhost:8000/api/v1/workers/business-builder/run \
  -d '{"task": "Large complex task", "budget_tokens": 50000}'

# 3. Check for anomalies
curl http://localhost:8000/api/v1/costs/anomalies
```

**Question:** Are cost spikes automatically detected and reported?

---

### Priority 2 (P2) - State & Persistence

#### Scenario 16: Memory Pin TTL
**Tests:** M7 (Memory Pins)

**Test Steps:**
```bash
# 1. Create memory pin with TTL=30s
curl -X POST http://localhost:8000/api/v1/memory/pins \
  -d '{"key": "ttl_test", "value": {"test": true}, "ttl_seconds": 30}'

# 2. Verify pin exists
curl http://localhost:8000/api/v1/memory/pins/ttl_test

# 3. Wait 35s
sleep 35

# 4. Verify pin expired/deleted
curl http://localhost:8000/api/v1/memory/pins/ttl_test
```

**Question:** Is memory lifecycle visible and predictable?

---

#### Scenario 17: Agent Registration & Heartbeat
**Tests:** M12-M14 (Multi-Agent)

**Test Steps:**
```bash
# 1. Register agent
curl -X POST http://localhost:8000/api/v1/agents/register \
  -d '{"name": "test_agent", "domain": "testing"}'

# 2. Send heartbeats every 10s for 30s
for i in {1..3}; do
  curl -X POST http://localhost:8000/api/v1/agents/{id}/heartbeat
  sleep 10
done

# 3. Stop heartbeats, wait for stale detection
sleep 60

# 4. Check agent status
curl http://localhost:8000/api/v1/agents/{id}
```

**Question:** Is agent health monitoring observable?

---

#### Scenario 18: Trace Persistence & Retrieval
**Tests:** M8 (Trace Storage)

**Test Steps:**
```bash
# 1. Run workflow
RUN_ID=$(curl -X POST http://localhost:8000/api/v1/workers/business-builder/run \
  -d '{"task": "Trace test"}' | jq -r '.run_id')

# 2. Get execution trace
curl http://localhost:8000/api/v1/traces/$RUN_ID

# 3. Verify all steps recorded with timing, inputs, outputs
```

**Question:** Can execution history be reliably reconstructed?

---

### Priority 3 (P3) - Advanced Features

#### Scenario 19: SBA (Skill Behavior Agreement)
**Tests:** M15 (SBA System)

**Test Steps:**
```bash
# 1. Generate SBA for agent
curl -X POST http://localhost:8000/api/v1/sba/generate \
  -d '{"agent_id": "test_agent"}'

# 2. Validate SBA
curl -X POST http://localhost:8000/api/v1/sba/validate \
  -d '{"agent_id": "test_agent", "action": "...", "context": "..."}'
```

---

#### Scenario 20: Blackboard Concurrent Access
**Tests:** M13 (Shared State)

**Test Steps:**
```bash
# 1. Write to blackboard
curl -X PUT http://localhost:8000/api/v1/blackboard/counter \
  -d '{"value": 0}'

# 2. Concurrent increments (run in parallel)
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/blackboard/counter/increment &
done
wait

# 3. Verify atomic operations
curl http://localhost:8000/api/v1/blackboard/counter
```

---

#### Scenario 21: Job Coordination
**Tests:** M12 (Job Queues)

**Test Steps:**
```bash
# 1. Create job with 5 items
curl -X POST http://localhost:8000/api/v1/jobs \
  -d '{"items": ["a", "b", "c", "d", "e"]}'

# 2. Claim items from multiple agents
# 3. Verify no double-claiming
```

---

#### Scenario 22: Golden File Determinism
**Tests:** M4 (Determinism)

**Test Steps:**
```bash
# 1. Run with --save-trace
aos simulate '{"plan": [...]}' --seed 12345 --save-trace /tmp/golden.json

# 2. Replay with same seed
aos replay /tmp/golden.json

# 3. Verify hash matches
```

---

## Execution Matrix

| Scenario | Milestone | Priority | Est. Time | Dependencies |
|----------|-----------|----------|-----------|--------------|
| 7 | M2-M3 | P0 | 15 min | None |
| 8 | M7 | P0 | 20 min | RBAC enabled |
| 9 | M11 | P0 | 10 min | None |
| 10 | M4 | P0 | 20 min | Long workflow |
| 11 | M25 | P0 | 15 min | Failed run exists |
| 12 | M8, M24 | P0 | 15 min | SSE support |
| 13 | M22 | P1 | 10 min | Killswitch API |
| 14 | M21 | P1 | 30 min | Multi-tenant mode |
| 15 | M26 | P1 | 20 min | Cost tracking |
| 16 | M7 | P2 | 5 min | Memory pins |
| 17 | M12-M14 | P2 | 15 min | Agent registry |
| 18 | M8 | P2 | 10 min | Trace storage |

**Total P0:** ~95 min
**Total P1:** ~60 min
**Total P2:** ~30 min

---

## Success Criteria

For each scenario, record:
- **Match:** YES / NO / PARTIAL
- **Trust Impact:** Increased / Neutral / Decreased
- **Confusion Points:** List specific moments

### Exit Criteria (Same as PIN-167)

**PASS Conditions (ALL must be true):**
- Tester can explain system behavior to a colleague
- Tester trusts system with appropriate caveats
- Tester knows system boundaries
- No "magic" moments

**FAIL Conditions (ANY triggers fail):**
- Tester believed system could do something it can't
- Tester couldn't explain why something happened
- System made implicit promises it didn't keep
- Tester had to read code to understand behavior

---

## Related PINs

- PIN-167: Final Review Tasks - Phase 1 (parent)
- PIN-163: M0-M28 Utilization Report
- PIN-161: P2FC - Partial to Full Consume
- PIN-032: M7 RBAC Enablement

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-25 | Created PIN-168 with 16 additional test scenarios covering M0-M28 |
