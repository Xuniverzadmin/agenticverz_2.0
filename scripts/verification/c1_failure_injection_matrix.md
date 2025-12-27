# C1 FAILURE INJECTION MATRIX

**Phase:** C1 — Telemetry Plane
**Purpose:** Prove telemetry never alters truth, replay, memory, or enforcement under hostile conditions
**Reference:** PIN-210-c1-telemetry-plane.md
**Change Policy:** Any modification requires re-certification

---

## GLOBAL INVARIANTS (Apply to ALL injections)

| ID | Invariant | Description |
|----|-----------|-------------|
| I1 | Traces/Incidents persist correctly | Truth tables unaffected |
| I2 | Replay output identical (hash-stable) | Determinism preserved |
| I3 | No telemetry-caused incidents | Zero `telemetry_failure` triggers |
| I4 | No blocking of execution | Best-effort writes |
| I5 | O1 endpoints unaffected | Truth UI works |
| I6 | Telemetry may be lost without consequence | Delete-safe |

---

## AXES

- **Timing:** before truth commit | during | after
- **Failure type:** soft fail | hard crash | corruption
- **Scope:** writer | reader | cleanup | API | replay boundary

---

## A. TELEMETRY WRITER FAILURES

| ID | Injection | Timing | Method | Expected Outcome | Invariants |
|----|-----------|--------|--------|------------------|------------|
| W1 | Insert failure | before | revoke INSERT | Execution continues | I1-I6 |
| W2 | Insert failure | during | kill writer proc | Partial telemetry | I1-I6 |
| W3 | Insert failure | after | drop table | No telemetry | I1-I6 |
| W4 | Slow writer | during | sleep 10s | Latency unaffected | I1-I6 |
| W5 | Payload oversize | during | > limit JSON | Row rejected only | I1-I6 |
| W6 | Duplicate spam | after | rapid inserts | Truth unchanged | I1-I6 |

---

## B. TELEMETRY READER FAILURES

| ID | Injection | Timing | Method | Expected Outcome | Invariants |
|----|-----------|--------|--------|------------------|------------|
| R1 | Read timeout | anytime | delay query | Empty metrics | I1-I5 |
| R2 | Table missing | anytime | DROP table | O1 works | I1-I5 |
| R3 | Corrupt rows | anytime | bad JSON | Skipped rows | I1-I5 |
| R4 | Cardinality blowup | anytime | 10M rows | Metrics slow only | I1-I5 |

---

## C. CLEANUP / TTL FAILURES

| ID | Injection | Timing | Method | Expected Outcome | Invariants |
|----|-----------|--------|--------|------------------|------------|
| C1 | TTL job crash | after | kill job | Old telemetry remains | I1-I6 |
| C2 | TTL deletes active | during | bad WHERE | Telemetry loss only | I1-I6 |
| C3 | Lock contention | during | long txn | Cleanup delayed | I1-I6 |

---

## D. API AGGREGATION FAILURES (O2/O3)

| ID | Injection | Timing | Method | Expected Outcome | Invariants |
|----|-----------|--------|--------|------------------|------------|
| A1 | Metrics API 500 | anytime | throw error | UI empty state | I1-I5 |
| A2 | Partial data | anytime | limit rows | Partial charts | I1-I5 |
| A3 | Schema mismatch | deploy | rename col | Metrics off | I1-I5 |

---

## E. REPLAY BOUNDARY ATTACKS (CRITICAL)

| ID | Injection | Timing | Method | Expected Outcome | Invariants |
|----|-----------|--------|--------|------------------|------------|
| P1 | Telemetry present | replay | prefill rows | Replay ignores | I1-I4 |
| P2 | Telemetry hints | replay | correlated data | No effect | I1-I4 |
| P3 | Telemetry removed | replay | DROP table | Replay works | I1-I4 |

---

## F. CROSS-MODULE CASCADES (WORST-CASE)

| ID | Injection | Method | Expected Outcome | Invariants |
|----|-----------|--------|------------------|------------|
| X1 | Writer down + reader slow | combo | Truth intact | I1-I6 |
| X2 | Cleanup deletes all | combo | Metrics empty | I1-I6 |
| X3 | DB restart mid-run | infra | Incidents correct | I1-I6 |

---

## PASS CRITERIA

- **Zero invariant violations**
- Any single violation = **C1 FAIL**

---

# MINIMAL MATRIX (80/20 - Fastest Path to Certification)

| Category | ID | Why It Matters |
|----------|----|--------------------|
| Writer | W1 | Non-blocking proof |
| Writer | W3 | Delete-safety |
| Reader | R2 | O1 independence |
| Cleanup | C2 | Data loss safety |
| API | A1 | UI degradation |
| Replay | P1 | Replay isolation |
| Replay | P3 | Replay delete-safety |
| Cascade | X1 | Partial failure |
| Cascade | X3 | Infra realism |

**Total: 9 injections**

### Why This Works

- Covers every axis
- Hits highest-risk boundaries
- Matches real outages
- Small enough to run repeatedly

---

# CLAUDE FAILURE INJECTION PACK

**Role:** Deterministic test executor
**Authority:** NONE
**Rule:** Execute steps, assert invariants, log evidence

---

## STEP 0 — Preconditions

- [ ] Telemetry migration applied (060_c1_telemetry_plane)
- [ ] Probe set frozen (15 probes)
- [ ] Baseline probe run recorded

---

## STEP 1 — Execute Injection (One at a Time)

For each injection ID (from matrix):

### 1.1 Apply Failure

Execute specified method:

```sql
-- Example: W3 (drop table)
DROP TABLE telemetry_event;

-- Example: W1 (revoke insert)
REVOKE INSERT ON telemetry_event FROM aos_app;

-- Example: R2 (table missing - same as W3)
DROP TABLE IF EXISTS telemetry_event;
```

### 1.2 Run Normal Execution

Trigger real LLM + DB flow (create run, execute steps)

### 1.3 Run Probes

```bash
DATABASE_URL=... AOS_API_KEY=... \
python3 scripts/verification/c1_telemetry_probes.py --all --json
```

### 1.4 Assert Invariants

Check I1-I6 (as listed per injection row)

---

## STEP 2 — Evidence Capture (MANDATORY)

For each injection, output:

```json
{
  "injection_id": "W3",
  "injection_name": "Insert failure after - drop table",
  "timestamp_utc": "2025-12-27T...",
  "failure_method": "DROP TABLE telemetry_event",
  "probes_run": [
    "truth-independence",
    "telemetry-write-failure-safe",
    "replay-does-not-read-telemetry",
    "o1-survives-telemetry-outage"
  ],
  "probes_passed": 15,
  "probes_failed": 0,
  "invariants_checked": ["I1", "I2", "I3", "I4", "I5", "I6"],
  "invariants_passed": true,
  "replay_hash_verified": true,
  "o1_available": true,
  "incidents_changed": false
}
```

If **any invariant fails**:

- STOP immediately
- Output failure JSON
- Do not proceed

```json
{
  "injection_id": "...",
  "status": "FAIL",
  "violated_invariant": "I3",
  "evidence": "telemetry_failure incident created",
  "timestamp_utc": "..."
}
```

---

## STEP 3 — Restoration

After each injection:

1. Restore telemetry table (re-apply migration if needed)
2. Confirm baseline probes pass again
3. Verify system nominal before next injection

```bash
# Re-apply migration
cd backend && alembic upgrade head

# Verify baseline
python3 scripts/verification/c1_telemetry_probes.py --all
```

---

## STEP 4 — Final Summary (NO INTERPRETATION)

After all injections complete:

```json
{
  "phase": "C1",
  "failure_matrix": "MINIMAL",
  "executed_injections": ["W1", "W3", "R2", "C2", "A1", "P1", "P3", "X1", "X3"],
  "total_injections": 9,
  "violations": [],
  "all_invariants_held": true,
  "certification_ready": true,
  "timestamp_utc": "2025-12-27T...",
  "evidence_hash": "sha256:..."
}
```

---

## EXECUTION CHECKLIST

| ID | Injection | Applied | Probes Run | Invariants | Restored |
|----|-----------|---------|------------|------------|----------|
| W1 | Insert failure (revoke) | [ ] | [ ] | [ ] | [ ] |
| W3 | Drop table | [ ] | [ ] | [ ] | [ ] |
| R2 | Table missing | [ ] | [ ] | [ ] | [ ] |
| C2 | TTL deletes active | [ ] | [ ] | [ ] | [ ] |
| A1 | Metrics API 500 | [ ] | [ ] | [ ] | [ ] |
| P1 | Telemetry present during replay | [ ] | [ ] | [ ] | [ ] |
| P3 | Telemetry removed during replay | [ ] | [ ] | [ ] | [ ] |
| X1 | Writer down + reader slow | [ ] | [ ] | [ ] | [ ] |
| X3 | DB restart mid-run | [ ] | [ ] | [ ] | [ ] |

---

## EXIT CRITERIA

C1 Failure Injection is COMPLETE when:

- [ ] All 9 minimal injections executed
- [ ] Zero invariant violations
- [ ] Evidence JSON archived
- [ ] System restored to nominal

---

## RELATED FILES

| File | Purpose |
|------|---------|
| `scripts/verification/c1_telemetry_probes.py` | Probe execution |
| `scripts/verification/c1_claude_test_pack.md` | Test instruction pack |
| `docs/memory-pins/PIN-210-c1-telemetry-plane.md` | C1 specification |
| `backend/alembic/versions/060_c1_telemetry_plane.py` | Migration |
