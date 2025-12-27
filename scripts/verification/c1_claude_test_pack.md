# CLAUDE TEST INSTRUCTION PACK

**Phase:** C1 — Telemetry Plane
**Purpose:** Prove telemetry observes reality without influencing it
**Authority:** Non-authoritative test runner
**Change Policy:** Any deviation invalidates results
**Reference:** PIN-210-c1-telemetry-plane.md

---

## 0. OPERATING RULES (MANDATORY)

1. **You are a test executor, not an analyst.**
   - Do not explain.
   - Do not summarize.
   - Do not infer intent.
   - Only execute steps and assert pass/fail.

2. **All assertions must be probe-backed.**
   - If a probe exists, you must use it.
   - Do not eyeball results.

3. **Evidence > narration.**
   - Output structured logs only (JSON preferred).
   - Each step must record timestamp, command, result.

4. **Failure policy**
   - If any assertion fails: STOP immediately.
   - Output failure artifact and exit.

---

## 1. ENVIRONMENT PRE-CHECK

### Required Inputs

- `DATABASE_URL`
- `AOS_API_KEY`
- Access to:
  - real LLM
  - real database
  - deployed API

### Preflight Commands

```bash
python3 scripts/verification/c1_telemetry_probes.py --list
```

### Assert

- Probe list includes **11 SQL probes** and **4 API probes**
- If mismatch -> FAIL

---

## 2. BASELINE SNAPSHOT (CONTROL)

### Step 2.1 — Baseline Counts

Run:

```bash
DATABASE_URL=... python3 scripts/verification/c1_telemetry_probes.py --sql-probes --json
```

Record:

- trace count
- incident count
- telemetry_event count

Store as:

```json
{
  "baseline_snapshot": {
    "timestamp_utc": "...",
    "trace_count": 0,
    "incident_count": 0,
    "telemetry_count": 0
  }
}
```

---

## 3. REAL SCENARIO EXECUTION (TRUTH FIRST)

Execute the following scenarios **using real LLM + DB**.

### Scenario S1 — Token Explosion

- Trigger high token usage
- Allow failure if it occurs

### Scenario S2 — Policy Violation

- Trigger a known policy violation

### Scenario S3 — Retry Success

- Induce transient failure
- Allow retry to succeed

### Scenario S4 — Infra Timeout

- Simulate DB/API latency timeout

**After each scenario:**

- Ensure traces exist
- Ensure incidents exist when applicable

No telemetry checks yet.

---

## 4. FULL PROBE EXECUTION (PRIMARY ASSERTIONS)

Run **all probes**:

```bash
DATABASE_URL=... AOS_API_KEY=... \
python3 scripts/verification/c1_telemetry_probes.py --all --json
```

### Assert ALL = PASS

Specifically verify these invariants from probe output:

- `truth-independence` = PASS
- `telemetry-write-failure-safe` = PASS
- `replay-does-not-read-telemetry` = PASS
- `o1-survives-telemetry-outage` = PASS

If any FAIL -> STOP.

---

## 5. TELEMETRY FAILURE INJECTION (HARD TEST)

### Step 5.1 — Disable Telemetry Writes

Perform ONE of the following:

- drop `telemetry_event` table **OR**
- revoke insert permissions

### Step 5.2 — Execute Normal Run

Trigger a standard execution path.

### Assert (MUST ALL HOLD)

- trace committed
- incident raised if applicable
- **NO telemetry-related incident**
- API endpoints respond normally

Re-enable telemetry afterward.

---

## 6. DELETION SAFETY TEST (CRITICAL)

### Step 6.1 — Hard Delete Telemetry

```sql
DROP TABLE telemetry_event;
```

### Step 6.2 — Run Core Reads

Execute:

- incident queries (O1)
- replay for a known trace
- audit export (if available)

### Assert

- outputs identical to baseline (hash or row-equivalence)
- zero errors
- replay output unchanged

If any deviation -> FAIL.

---

## 7. WEB/API PROPAGATION CHECK (O1-O3)

### O1 — Truth Pages

Call:

- incidents endpoint
- traces endpoint

Assert:

- 200 OK
- factual data present
- no dependency on telemetry

### O2/O3 — Metrics & Insights

Call metrics endpoints.

Assert:

- empty state OR partial data
- **no error**
- labeled non-authoritative

---

## 8. REPLAY HERMETICITY FINAL CHECK

Run replay on:

- trace created before telemetry deletion
- trace created after telemetry restoration

Assert:

- identical replay outputs
- zero telemetry reads/writes
- no side effects

---

## 9. FINAL EVIDENCE OUTPUT

Output a single JSON object containing:

```json
{
  "phase": "C1",
  "status": "PASS",
  "timestamp_utc": "...",
  "probes_run": ["..."],
  "failures": [],
  "telemetry_present": true,
  "replay_hash_verified": true,
  "truth_independent": true,
  "baseline_hash": "...",
  "final_hash": "..."
}
```

If any step failed, output:

```json
{
  "status": "FAIL",
  "failed_step": "...",
  "evidence": "..."
}
```

---

## 10. TERMINATION

- Do not provide opinions
- Do not suggest improvements
- Do not proceed to C2

**End of instruction pack.**

---

## VERIFICATION CHECKLIST

| Step | Description | Status |
|------|-------------|--------|
| 0 | Operating rules acknowledged | [ ] |
| 1 | Environment pre-check passed | [ ] |
| 2 | Baseline snapshot recorded | [ ] |
| 3.S1 | Token explosion scenario | [ ] |
| 3.S2 | Policy violation scenario | [ ] |
| 3.S3 | Retry success scenario | [ ] |
| 3.S4 | Infra timeout scenario | [ ] |
| 4 | All probes passed | [ ] |
| 5 | Telemetry failure injection passed | [ ] |
| 6 | Deletion safety test passed | [ ] |
| 7 | O1-O3 propagation verified | [ ] |
| 8 | Replay hermeticity verified | [ ] |
| 9 | Evidence output generated | [ ] |

---

## EXIT CRITERIA

C1 is CERTIFIED only when:

- [ ] All 15 probes pass
- [ ] Deletion safety proven
- [ ] Replay hash unchanged
- [ ] Human UI check passed
- [ ] Evidence JSON archived

---

## RELATED FILES

| File | Purpose |
|------|---------|
| `scripts/verification/c1_telemetry_probes.py` | Probe execution script |
| `docs/memory-pins/PIN-210-c1-telemetry-plane.md` | C1 specification |
| `backend/alembic/versions/060_c1_telemetry_plane.py` | Migration |
