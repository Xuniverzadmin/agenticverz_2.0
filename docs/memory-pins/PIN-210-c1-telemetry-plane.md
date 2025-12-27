# PIN-210 — C1 TELEMETRY PLANE

**Status:** SPEC-READY
**Phase:** C1
**Created:** 2025-12-27
**Change Policy:** Breaking changes reopen Phase A

---

## 1. C1 OBJECTIVE (SINGLE SENTENCE)

> Provide high-volume observability signals that **never participate in truth, memory, replay, or enforcement**.

If telemetry disappears, **nothing factual breaks**.

---

## 2. NON-NEGOTIABLE SYSTEM INVARIANTS

### 2.1 Authority Boundary

| Plane                       | Can Write   | Can Read                |
| --------------------------- | ----------- | ----------------------- |
| Truth (Traces, Incidents)   | NO Telemetry | YES Telemetry           |
| Control (Retries, Policies) | NO Telemetry | YES Telemetry           |
| Telemetry                   | YES Telemetry | NO Nothing authoritative |
| Replay                      | NO Telemetry | NO Telemetry            |

**Invariant:**
Telemetry is **observational only**.

---

### 2.2 One-Way Data Law

```
Truth -> Telemetry     ALLOWED
Telemetry -> Truth     FORBIDDEN
Telemetry -> Memory    FORBIDDEN
Telemetry -> Replay    FORBIDDEN
```

Violation = **P0 system breach**.

---

## 3. TELEMETRY DATA MODEL (REQUIRED)

### 3.1 Table: `telemetry_event`

```sql
CREATE TABLE telemetry_event (
  id                UUID PRIMARY KEY,
  created_at_utc    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at_utc    TIMESTAMPTZ NOT NULL,

  tenant_hash       TEXT NOT NULL,
  source_module     TEXT NOT NULL,
  signal_type       TEXT NOT NULL,

  signal_payload    JSONB NOT NULL DEFAULT '{}',

  trace_id          UUID NULL,
  incident_id       UUID NULL,

  authoritative     BOOLEAN NOT NULL DEFAULT FALSE,

  CONSTRAINT chk_never_authoritative CHECK (authoritative = FALSE)
);

-- TTL cleanup index
CREATE INDEX idx_telemetry_expires ON telemetry_event (expires_at_utc);

-- Query patterns
CREATE INDEX idx_telemetry_tenant_module ON telemetry_event (tenant_hash, source_module);
CREATE INDEX idx_telemetry_signal_type ON telemetry_event (signal_type);
CREATE INDEX idx_telemetry_trace_id ON telemetry_event (trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX idx_telemetry_incident_id ON telemetry_event (incident_id) WHERE incident_id IS NOT NULL;
```

### 3.2 Mandatory Properties

* `authoritative = FALSE` **always** (enforced by CHECK constraint)
* `trace_id`, `incident_id` are **references only** (no FK constraints)
* **NO foreign key constraints** to truth tables
* TTL cleanup is mandatory (via expires_at_utc)

### 3.3 Forbidden Fields

* no severity
* no status
* no decision flags
* no derived "truth"

---

## 4. WRITE RULES (CRITICAL)

Telemetry writes must be:

* best-effort
* non-blocking
* non-transactional with truth writes

### Explicit Rule

> **Failure to write telemetry must never raise an incident.**

### Implementation Pattern

```python
async def emit_telemetry(event: TelemetryEvent) -> None:
    """Best-effort telemetry write. Never raises, never blocks."""
    try:
        # Fire-and-forget, no await on response
        asyncio.create_task(_write_telemetry_async(event))
    except Exception:
        # Swallow ALL exceptions. Telemetry failure is not a system failure.
        pass
```

---

## 5. READ RULES

Telemetry reads:

* are optional
* must degrade to empty state
* must not affect correctness

If telemetry read fails -> **UI shows "No telemetry data available"**, not error.

### Implementation Pattern

```python
async def get_telemetry_metrics(tenant_id: str) -> TelemetryMetrics:
    """Read telemetry. Returns empty on failure."""
    try:
        return await _fetch_telemetry(tenant_id)
    except Exception:
        return TelemetryMetrics.empty()  # Graceful degradation
```

---

## 6. MODULE-LEVEL REQUIREMENTS

### 6.1 Execution / Traces

Telemetry may observe:

* latency
* step count
* retry count

Telemetry may NOT:

* infer success
* mark failure
* change determinism

---

### 6.2 Incidents

Telemetry may observe:

* incident type
* resolution path
* timestamps

Telemetry may NOT:

* downgrade severity
* auto-resolve
* suppress visibility

---

### 6.3 Policy Engine

Telemetry may observe:

* violation frequency
* policy version

Telemetry may NOT:

* influence enforcement
* rewrite policies

---

### 6.4 Replay Engine

**ABSOLUTE RULE**

* Replay must emit **zero telemetry**
* Replay must not read telemetry
* Replay output must be identical with telemetry ON/OFF

---

### 6.5 Memory System

Telemetry:

* never injected
* never summarized
* never promoted

Memory remains **human-curated only**.

---

## 7. ACCEPTANCE TESTS (5 TESTS -> CONTRACT)

This section defines what Claude must **prove**, not "check".

---

### TEST-1 — REAL SCENARIOS

#### Required Scenarios

* S1: Token explosion (LLM exceeds budget)
* S2: Policy violation (safety trigger)
* S3: Retry success (first fail, second pass)
* S4: Infra timeout (DB slow/timeout)

#### Acceptance Criteria

* Incidents exist without telemetry
* Telemetry adds only observability
* Deleting telemetry changes nothing factual

---

### TEST-2 — REAL INFRA (CLAUDE)

Claude must:

* Call real LLM
* Write real DB rows
* Induce real failures

#### Acceptance Criteria

* telemetry row count != trace count
* telemetry failure does not fail execution
* incidents still raised correctly

---

### TEST-3 — DATA PROPAGATION (ALL MODULES)

Claude proves ordering:

```
Trace commit
-> Incident commit (if any)
-> Telemetry write
```

#### Acceptance Criteria

* Telemetry never precedes truth
* Deleting telemetry does not break:
  * incident queries
  * replay
  * audit export

---

### TEST-4 — WEB DATA PROPAGATION (O1-O4)

| Layer           | Dependency Rule |
| --------------- | --------------- |
| O1 (Truth UI)   | NO Telemetry    |
| O2 (Metrics)    | YES Telemetry   |
| O3 (Insights)   | YES Telemetry   |
| O4 (Prediction) | NOT IN C1       |

#### Acceptance Criteria

* O1 works with telemetry table dropped
* O2/O3 show empty state, not error

---

### TEST-5 — PHYSICAL UI (HUMAN)

Manual verification:

* Incidents show facts, not confidence
* Telemetry labeled "Non-authoritative"
* No UI suggests certainty from telemetry

---

## 8. GLOBAL FAILURE CONDITIONS (AUTO-FAIL)

C1 fails immediately if **any** occur:

* Telemetry blocks execution
* Telemetry affects replay
* Telemetry influences memory
* Telemetry suppresses incidents
* Telemetry modifies severity

No exception process. Roll back.

---

## 9. EXIT CRITERIA (C1 DONE)

All must be true:

- [ ] Telemetry table can be dropped safely
- [ ] Replay output hash unchanged with/without telemetry
- [ ] Audit export unchanged with/without telemetry
- [ ] Incidents reproducible without telemetry
- [ ] Claude verification logs saved
- [ ] Human UI check passed

Only then:

> **C1 is complete. System observes reality without rewriting it.**

---

## 10. IMPLEMENTATION SEQUENCE

Confirmed order — no deviation:

1. **PIN-210** (this spec) - COMPLETE
2. **Migration**: telemetry_event table
3. **SQL/API probes**: Verification queries
4. **Claude Test Instruction Pack**: Scenario execution
5. **Failure Injection Matrix**: Stress tests

---

## 11. SQL/API PROBES (VERIFICATION QUERIES)

### Probe 1: Truth Independence

```sql
-- Prove incidents exist without telemetry
SELECT COUNT(*) FROM incident WHERE id NOT IN (
  SELECT incident_id FROM telemetry_event WHERE incident_id IS NOT NULL
);
-- Expected: > 0 (some incidents have no telemetry)
```

### Probe 2: Non-Authoritative Constraint

```sql
-- Verify no authoritative telemetry exists
SELECT COUNT(*) FROM telemetry_event WHERE authoritative = TRUE;
-- Expected: 0 (constraint should prevent this)
```

### Probe 3: Replay Isolation

```sql
-- Verify no telemetry emitted during replay
SELECT COUNT(*) FROM telemetry_event
WHERE signal_payload->>'is_replay' = 'true';
-- Expected: 0 (replay never emits telemetry)
```

### Probe 4: TTL Enforcement

```sql
-- Check for expired telemetry (should be cleaned)
SELECT COUNT(*) FROM telemetry_event
WHERE expires_at_utc < NOW();
-- Expected: 0 (or low, cleanup job running)
```

### Probe 5: Write Order Verification

```sql
-- Verify telemetry timestamp >= trace timestamp
SELECT te.id, te.created_at_utc AS telemetry_time,
       t.started_at AS trace_time
FROM telemetry_event te
JOIN runs t ON te.trace_id = t.id::uuid
WHERE te.created_at_utc < t.started_at;
-- Expected: 0 rows (telemetry never precedes truth)
```

---

## 12. API PROBES

### Probe A: O1 Independence

```bash
# Drop telemetry, verify incidents still load
curl -X GET /api/v1/incidents \
  -H "X-AOS-Key: $KEY" \
  -H "X-Telemetry-Disabled: true"
# Expected: 200 OK with incident data
```

### Probe B: Telemetry Failure Tolerance

```bash
# Telemetry write fails, execution succeeds
curl -X POST /api/v1/runs \
  -H "X-AOS-Key: $KEY" \
  -H "X-Inject-Telemetry-Failure: true" \
  -d '{"plan": [...]}'
# Expected: 200 OK (run succeeds despite telemetry failure)
```

### Probe C: Graceful Degradation

```bash
# Telemetry table missing, metrics degrade
curl -X GET /api/v1/metrics/observability \
  -H "X-AOS-Key: $KEY"
# Expected: 200 OK with empty/degraded metrics
```

---

## 13. RELATED DOCUMENTS

| Document | Purpose |
|----------|---------|
| PIN-193-198 | Phase A acceptance gates (truth guarantees) |
| PIN-199-205 | Phase B scenarios (must not break) |
| PIN-208 | Phase C Discovery Ledger |
| LESSONS_ENFORCED.md | 15 invariants that must hold |

---

## 14. CHANGE LOG

| Date | Change | Author |
|------|--------|--------|
| 2025-12-27 | Initial specification | Human + Claude |

---

## 15. SIGNATURE

This specification is **FROZEN** upon creation.

Any modification that:
- Allows telemetry to write to truth tables
- Allows telemetry to affect replay
- Allows telemetry to influence memory
- Removes the `authoritative = FALSE` constraint

**Reopens Phase A** and requires re-verification of S1-S6.
