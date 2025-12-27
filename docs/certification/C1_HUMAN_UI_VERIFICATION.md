# C1 Human UI Verification

**Date:** 2025-12-27
**Environment:** Neon Postgres (ep-long-surf-a1n0hv91.ap-southeast-1.aws.neon.tech)
**Verifier:** _______________

---

## Pre-Check Confirmation

- [ ] Telemetry is enabled (table exists, no permissions revoked)
- [ ] I will judge ONLY what the UI communicates
- [ ] I will NOT reason about backend behavior

---

## O1 — Truth UI Check (/guard/incidents)

### Verification Questions

| Question | Answer |
|----------|--------|
| Are incidents visible? | [ ] YES / [ ] NO |
| Does each incident show timestamp? | [ ] YES / [ ] NO |
| Does each incident show type? | [ ] YES / [ ] NO |
| Does each incident show severity? | [ ] YES / [ ] NO |
| Does each incident show status? | [ ] YES / [ ] NO |
| Does data match known test incidents? | [ ] YES / [ ] NO |

### Red Flags (must NOT appear)

| Phrase | Found? |
|--------|--------|
| "confidence" wording | [ ] YES / [ ] NO |
| "estimated", "likely", "predicted" | [ ] YES / [ ] NO |
| Charts/metrics explaining facts | [ ] YES / [ ] NO |

### Critical Question

> "If telemetry were completely deleted, would this page still be truthful?"

Answer: [ ] YES → PASS / [ ] NO → FAIL

**O1 Result:** _______________

---

## O2/O3 — Metrics & Insights Check

(Only if such pages exist)

### With Telemetry Present

| Check | Status |
|-------|--------|
| Charts show counts/trends/aggregates | [ ] YES / [ ] N/A |
| Labels indicate "Metrics" / "Insights" | [ ] YES / [ ] N/A |
| Labels indicate "Non-authoritative" | [ ] YES / [ ] N/A |

### Degradation Test (Mental)

> "If this chart disappeared, would anything factual be lost?"

Answer: [ ] NO (correct) / [ ] YES (problem)

**O2/O3 Result:** _______________

---

## Telemetry Misrepresentation Check

### Scan all visible UI text for:

| Red Flag Phrase | Found? |
|-----------------|--------|
| "System believes..." | [ ] YES / [ ] NO |
| "Likely root cause..." | [ ] YES / [ ] NO |
| "High confidence incident..." | [ ] YES / [ ] NO |
| "Telemetry confirms..." | [ ] YES / [ ] NO |

### Acceptable Phrasing Observed

- [ ] "Observed"
- [ ] "Recorded"
- [ ] "Measured"
- [ ] "Aggregated metrics"

**Misrepresentation Check Result:** _______________

---

## Final Sanity Test

> "If I were a customer during an outage, could this UI mislead me about what actually happened?"

Answer: [ ] NO → PASS / [ ] YES → FAIL

---

## Summary

| Check | Result |
|-------|--------|
| O1 Truth UI | _______ |
| O2/O3 Metrics | _______ |
| Telemetry Labeling | _______ |
| Final Sanity | _______ |

**Overall Human UI Verification:** [ ] PASS / [ ] FAIL

---

## Notes

(Any observations, edge cases, or concerns)

```
[Write notes here]
```

---

## Signature

**Verified by:** _______________
**Date:** _______________
**Time:** _______________
