# Production Readiness Failure Audit

**Status:** AUDIT COMPLETE
**Author:** Claude + Human Pair
**Date:** 2026-01-12
**Reference:** PIN-401 Track A (Production Wiring)

---

## Executive Summary

This audit analyzes failure modes for each Phase 6-9 provider and runtime gate.
Each provider is assessed for:

1. **Failure Impact** - What happens when the provider fails?
2. **Current Mitigation** - What protection exists today?
3. **Observability Gap** - What signals are missing?
4. **Recovery Path** - How to recover from failure?
5. **Recommendation** - What needs to be added?

---

## Provider Audit Matrix

### 1. TenantLifecycleProvider (Phase-9)

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Failure Impact** | HIGH | Lifecycle gate blocks ALL SDK traffic |
| **Current Mitigation** | PARTIAL | Mock returns ACTIVE by default |
| **Observability Gap** | YES | No metrics for state transitions |
| **Recovery Path** | MANUAL | Requires founder intervention |

**Failure Scenarios:**

| Scenario | Impact | Current Behavior |
|----------|--------|------------------|
| Provider unreachable | SDK blocked | Mock returns ACTIVE (fail-open) |
| State lookup fails | SDK blocked | Mock returns ACTIVE (fail-open) |
| Invalid tenant_id | SDK blocked | Mock returns ACTIVE |
| Transition fails | State stuck | Transition rejected, state unchanged |

**Observability Gaps:**
- No metric: `lifecycle_state_transitions_total`
- No metric: `lifecycle_gate_blocks_total`
- No alert: State transition failures
- No logging: Transition audit trail

**Recommendations:**
- [ ] Add circuit breaker for provider calls
- [ ] Add `lifecycle_provider_errors_total` counter
- [ ] Add `lifecycle_transitions_total{from,to}` counter
- [ ] Add fallback state cache (read-through cache)
- [ ] Add explicit timeout (recommend: 500ms)

---

### 2. BillingProvider (Phase-6)

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Failure Impact** | MEDIUM | Billing gate returns 402 for SDK paths |
| **Current Mitigation** | PARTIAL | Mock returns TRIAL (allows usage) |
| **Observability Gap** | YES | No metrics for billing checks |
| **Recovery Path** | MANUAL | Requires plan reassignment |

**Failure Scenarios:**

| Scenario | Impact | Current Behavior |
|----------|--------|------------------|
| Provider unreachable | Usage blocked | Mock returns TRIAL (fail-open) |
| Plan lookup fails | Usage blocked | Mock returns FREE plan |
| Limit check fails | Usage allowed | Mock returns unlimited |
| State lookup fails | Usage allowed | Mock returns default state |

**BILLING-001 Compliance:**
- ✅ Onboarding never blocked (check exists)
- ✅ Billing state checked after lifecycle
- ⚠️ No timeout on provider calls

**Observability Gaps:**
- No metric: `billing_checks_total{result}`
- No metric: `billing_state_lookups_total`
- No metric: `billing_limit_exceeded_total{limit_name}`
- No alert: Provider latency spike

**Recommendations:**
- [ ] Add `billing_provider_latency_seconds` histogram
- [ ] Add `billing_gate_blocks_total{reason}` counter
- [ ] Add circuit breaker with 3-failure threshold
- [ ] Add explicit timeout (recommend: 200ms)
- [ ] Add cache for plan/limits (TTL: 5min)

---

### 3. AbuseProtectionProvider (Phase-7)

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Failure Impact** | MEDIUM | Protection gate returns 429/503 |
| **Current Mitigation** | PARTIAL | Mock uses static thresholds |
| **Observability Gap** | YES | No metrics for protection checks |
| **Recovery Path** | AUTOMATIC | Retry-After header provided |

**Failure Scenarios:**

| Scenario | Impact | Current Behavior |
|----------|--------|------------------|
| Provider unreachable | All requests allowed | Mock allows (fail-open) |
| Rate limit check fails | Requests allowed | Mock allows |
| Anomaly detection fails | Silent | Non-blocking per ABUSE-003 |
| Cost guard fails | Requests allowed | Mock allows |

**ABUSE-003 Compliance:**
- ✅ Anomaly detection never blocks
- ✅ Retry-After headers on 429/503
- ⚠️ No metrics on anomaly signals

**Observability Gaps:**
- No metric: `protection_checks_total{dimension,decision}`
- No metric: `protection_anomalies_total{severity}`
- No metric: `protection_check_latency_seconds`
- No alert: Burst of 429s

**Recommendations:**
- [ ] Add `protection_decisions_total{dimension,decision}` counter
- [ ] Add `protection_anomaly_signals_total{severity}` counter
- [ ] Add circuit breaker (recommend: 5 failures / 30s)
- [ ] Add explicit timeout (recommend: 100ms)
- [ ] Add rate limit cache (TTL: 1s)

---

### 4. ObservabilityProvider (Phase-8)

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Failure Impact** | LOW | Emit failures are silent |
| **Current Mitigation** | STRONG | OBSERVE-004 enforced |
| **Observability Gap** | MODERATE | Emit failures logged locally |
| **Recovery Path** | AUTOMATIC | Next emit succeeds |

**Failure Scenarios:**

| Scenario | Impact | Current Behavior |
|----------|--------|------------------|
| Provider unreachable | Events lost | Logged locally, continues |
| Emit fails | Event lost | Logged locally, continues |
| Query fails | Empty results | Error returned to caller |
| Store full | Events lost | Mock unbounded (memory issue) |

**OBSERVE-004 Compliance:**
- ✅ emit() never blocks execution
- ✅ emit() never raises exceptions
- ⚠️ Lost events not counted

**Observability Gaps:**
- No metric: `observability_emit_failures_total`
- No metric: `observability_events_emitted_total{type,source}`
- No metric: `observability_store_size_bytes` (for real provider)
- No alert: Sustained emit failures

**Recommendations:**
- [ ] Add `observability_emit_attempts_total{success}` counter
- [ ] Add `observability_emit_latency_seconds` histogram
- [ ] Add memory limit for mock store (recommend: 100k events)
- [ ] Add event sampling if overloaded
- [ ] Add dead-letter queue for failed emits (future)

---

## Runtime Gate Audit

### 5. LifecycleGate (Middleware)

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Failure Impact** | HIGH | 403 for all SDK paths |
| **Current Mitigation** | PARTIAL | Provider call not protected |
| **Observability Gap** | YES | No block metrics |
| **Recovery Path** | MANUAL | Fix provider or state |

**Recommendations:**
- [ ] Wrap provider call in try/except
- [ ] Return 503 (not 500) on provider failure
- [ ] Add `gate_lifecycle_blocks_total{reason}` counter
- [ ] Add timeout on `get_state()` call

---

### 6. ProtectionGate (Middleware)

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Failure Impact** | MEDIUM | 429/503 for over-limit |
| **Current Mitigation** | PARTIAL | Provider call not protected |
| **Observability Gap** | YES | No metrics |
| **Recovery Path** | AUTOMATIC | Retry-After |

**Recommendations:**
- [ ] Wrap provider call in try/except
- [ ] Return 503 on provider failure (fail-open)
- [ ] Add `gate_protection_decisions_total{decision}` counter
- [ ] Add circuit breaker

---

### 7. BillingGate (Middleware)

| Dimension | Status | Notes |
|-----------|--------|-------|
| **Failure Impact** | MEDIUM | 402 for suspended |
| **Current Mitigation** | PARTIAL | Provider call not protected |
| **Observability Gap** | YES | No metrics |
| **Recovery Path** | MANUAL | Fix billing state |

**Recommendations:**
- [ ] Wrap provider call in try/except
- [ ] Return 503 on provider failure (fail-open)
- [ ] Add `gate_billing_blocks_total{reason}` counter
- [ ] Add billing state cache

---

## Timeout Recommendations

| Component | Current | Recommended | Rationale |
|-----------|---------|-------------|-----------|
| Lifecycle gate | None | 500ms | State lookup is fast |
| Protection gate | None | 100ms | Rate limits are hot path |
| Billing gate | None | 200ms | Plan lookup is cacheable |
| Observability emit | None | 50ms | Must not block request |
| Observability query | None | 5000ms | Query can be slow |

---

## Circuit Breaker Recommendations

| Component | Threshold | Reset Time | Open Behavior |
|-----------|-----------|------------|---------------|
| Lifecycle provider | 3 failures / 10s | 30s | Return ACTIVE |
| Billing provider | 5 failures / 30s | 60s | Return TRIAL |
| Protection provider | 5 failures / 30s | 30s | Return ALLOW |
| Observability emit | 10 failures / 60s | 120s | Log locally only |

---

## Fail-Open vs Fail-Closed Matrix

| Gate | Fail Mode | Rationale |
|------|-----------|-----------|
| Lifecycle Gate | Fail-Open | Availability > strict enforcement |
| Protection Gate | Fail-Open | Availability > rate limiting |
| Billing Gate | Fail-Open | Availability > billing enforcement |
| Auth Gateway | Fail-Closed | Security > availability |

**Exception:** Auth failures MUST be fail-closed. All other gates fail-open
to preserve customer availability.

---

## Observability Gaps Summary

### Missing Metrics (Priority 1)

| Metric | Type | Labels |
|--------|------|--------|
| `lifecycle_transitions_total` | counter | `from`, `to`, `tenant_id` |
| `billing_gate_blocks_total` | counter | `reason` |
| `protection_decisions_total` | counter | `dimension`, `decision` |
| `gate_latency_seconds` | histogram | `gate` |

### Missing Metrics (Priority 2)

| Metric | Type | Labels |
|--------|------|--------|
| `provider_errors_total` | counter | `provider`, `operation` |
| `provider_circuit_open_total` | counter | `provider` |
| `observability_events_total` | counter | `type`, `source` |
| `observability_emit_failures_total` | counter | `reason` |

### Missing Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| LifecycleProviderDown | errors > 5 in 1m | critical |
| BillingGateHighBlocks | blocks > 100 in 5m | warning |
| ProtectionBurstRejects | 429s > 1000 in 1m | warning |
| ObservabilityEmitFailing | failures > 100 in 5m | warning |

---

## Recovery Procedures

### 1. Lifecycle Provider Failure

```
1. Check provider health: GET /health
2. If unhealthy: Restart provider service
3. If healthy but failing:
   a. Check database connection
   b. Check state table integrity
   c. Check circuit breaker state
4. Manual recovery:
   a. Set circuit breaker to closed
   b. Clear state cache
   c. Verify state lookup works
```

### 2. Billing Provider Failure

```
1. Check provider health
2. If external (Stripe): Check status.stripe.com
3. If internal:
   a. Check database connection
   b. Check plan table integrity
4. Manual recovery:
   a. Enable emergency bypass (ENV: BILLING_BYPASS=true)
   b. Fix root cause
   c. Disable bypass
```

### 3. Protection Provider Failure

```
1. Check provider health
2. Check rate limit store (Redis in prod)
3. If Redis down:
   a. Fail-open is automatic
   b. Alert: High risk of abuse
4. Manual recovery:
   a. Restart Redis
   b. Clear rate limit state
   c. Monitor for abuse spike
```

---

## Next Steps (Track A2-A4)

| Phase | Task | Priority |
|-------|------|----------|
| A2 | Wire observability metrics | HIGH |
| A2 | Add missing counters | HIGH |
| A3 | Add circuit breakers | HIGH |
| A3 | Add timeouts | HIGH |
| A3 | Add emergency bypass flags | MEDIUM |
| A4 | Dry-run in staging | HIGH |
| A4 | Load test gates | MEDIUM |

---

**End of Production Readiness Failure Audit**

This audit identifies gaps. Implementation is Track A2-A4.
