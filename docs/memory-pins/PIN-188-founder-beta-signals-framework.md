# PIN-188: Founder-Beta Signals Framework

**Status:** ACTIVE
**Category:** Governance / Beta / Signals
**Created:** 2025-12-26
**Milestone:** Runtime v1 Beta
**Related:** PIN-186 (Page Order Invariants), PIN-187 (Compliance Audit)
**Companion:** `PIN-188-beta-scorecard.md` (One-page printable scorecard)

---

## Summary

Pre-declared signal framework for Founder-Beta. Binary where it matters, tolerant where learning is intended, explicitly designed to prevent scope creep.

**Duration:** 2-4 weeks or 20-30 real sessions (whichever first)

---

## First Principle (LOCKED)

> **Beta is not for validation of features.
> Beta is for validation of *truthfulness and navigability*.**

Signals must answer:
- Do founders understand what happened?
- Can they explain it without you?
- Do they know where to click next?
- Do they trust the system's answers *even when it hurts*?

---

## Signal Taxonomy (4 Buckets Only)

| Bucket | Question Answered |
|--------|-------------------|
| Comprehension | Can they understand? |
| Navigation | Can they find it? |
| Trust | Do they believe it? |
| Pull | Are they asking for depth? |

---

## 1. Comprehension Signals (P0)

### HARD FAIL (Beta stops if occurs 2+)

| Signal | Interpretation |
|--------|----------------|
| "Why did this run do that?" *after* viewing Run O3 | UI lying by omission |
| "Why did it cost more than expected?" *after* seeing advisory badge + delta | Cost surfacing broken |
| "Was memory used here?" *after* PRE-RUN section | Memory injection hidden |
| "Did policy block this or not?" *after* CONSTRAINTS section | Constraint surfacing broken |

**Action:** Fix surfacing immediately. Do NOT add features.

### PASS

- Founder can explain a run outcome *verbatim* using O3
- Founder can point to PRE-RUN vs OUTCOME difference
- Founder uses correct vocabulary:
  - "Because it was advisory..."
  - "Memory was injected here..."
  - "Policy skipped here..."

**This is the single most important success signal.**

---

## 2. Navigation Signals (P0)

### HARD FAIL

| Signal | Interpretation |
|--------|----------------|
| Clicks back and forth between pages repeatedly | Navigation law broken in practice |
| Opens devtools / copies IDs manually | Cross-links missing |
| "Where do I see that again?" | Labels unclear |
| "Just show me the logs" | O3 insufficient |

**Action:** Fix links, labels, or cross-entity jumps. Do NOT add O4 yet.

### PASS

- Founder naturally moves: Incident → Run → Trace → back
- Breadcrumbs are used implicitly (no confusion)
- No one asks for "global search"

**This means O1-O3 is sufficient.**

---

## 3. Trust Signals (P0/P1)

### HARD FAIL (P0) - Even once is serious

| Signal | Interpretation |
|--------|----------------|
| "This feels like it's hiding something" | Core promise violated |
| "Is this really what happened?" | Surfacing incomplete |
| "Can I trust this number?" | Data integrity questioned |

**Action:** Stop beta. Audit surfacing, not logic.

### WARNING (P1) - Acceptable early

| Signal | Interpretation |
|--------|----------------|
| "I don't *like* that it did this" | Truthful discomfort (GOOD) |
| "That's expensive" | Cost awareness (GOOD) |
| "This behavior is annoying" | System working as designed |

**Do NOT optimize these away during beta.**

### PASS

- Founder disagrees with outcome but accepts explanation
- Founder says: "Okay, that makes sense"
- Founder continues using system *after* a bad outcome

**Trust ≠ happiness. Trust = acceptance of reality.**

---

## 4. Pull Signals (O4 Eligibility Gate)

### NOT a valid O4 pull (Ignore)

- "Can you add a details page?"
- "I want more info"
- "This feels shallow"

These are vibes, not signals.

### VALID O4 PULL (Must meet ALL)

1. Same question asked **3+ times**
2. References a **specific entity**:
   - "Which retries happened for this incident?"
   - "Which step failed in this trace?"
3. Cannot be answered from O3 without friction
4. Founder is already navigating correctly

**Only then unlock exactly ONE O4.**

---

## Beta Stop Conditions (Pre-Declared)

End beta immediately when ANY ONE is true:

| Condition | Meaning |
|-----------|---------|
| All P0 fails = 0 for 7 consecutive days | Comprehension achieved |
| Founders stop asking "what happened?" and start asking "what should I do?" | Truth density validated |
| One clear O4 pull emerges repeatedly | Depth need identified |
| You can write a causal post-mortem using only the UI | System is self-explanatory |

At that point: More users = diminishing returns.

---

## What You Explicitly Do NOT Measure

| Metric | Why Excluded |
|--------|--------------|
| Session length | Lies during beta |
| Click counts | Measures friction, not understanding |
| Feature usage | Irrelevant to truth |
| "Engagement" | Dopamine, not comprehension |
| NPS | Too early, too noisy |

**You are measuring understanding, not engagement.**

---

## Session Checklist (Print This)

Before every beta session, ask yourself:

- [ ] Am I watching *confusion*, not *complaints*?
- [ ] Am I resisting the urge to explain verbally?
- [ ] Am I writing down repeated questions verbatim?
- [ ] Am I preventing myself from adding features?

If any is NO, pause the beta.

---

## Beta Scorecard Template

| Date | Session # | Comprehension Fails | Navigation Fails | Trust Fails | O4 Pulls | Notes |
|------|-----------|---------------------|------------------|-------------|----------|-------|
| | | | | | | |

Track verbatim quotes, not interpretations.

---

## Exit Criteria Summary

| Gate | Condition | Action |
|------|-----------|--------|
| Beta Fail | 2+ P0 fails in any category | Stop, fix surfacing |
| Beta Pass | 7 days zero P0 fails | Declare success |
| O4 Unlock | Valid pull signal (all 4 criteria) | Build exactly one O4 |
| Runtime v2 | Beta complete + O4 validated | Begin next phase |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | Added companion scorecard - One-page printable format |
| 2025-12-26 | Created PIN-188 - Founder-Beta Signals Framework |
