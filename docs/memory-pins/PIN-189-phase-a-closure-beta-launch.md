# PIN-189: Phase A Closure & Beta Launch

**Status:** LOCKED
**Category:** Governance / Milestone / Beta
**Created:** 2025-12-26
**Milestone:** Runtime v1 Beta Launch
**Related:** PIN-186 (LAW), PIN-187 (COMPLETE), PIN-188 (ACTIVE)
**Companion:** `PIN-189-weekly-synthesis.md` (Printable weekly template)

---

## Phase A Declaration

**PHASE A IS COMPLETE.**

| Artifact | Status | Lock Date |
|----------|--------|-----------|
| PIN-186 (Page Order Invariants) | LAW | 2025-12-26 |
| PIN-187 (Compliance Audit) | COMPLETE | 2025-12-26 |
| PIN-188 (Beta Signals Framework) | ACTIVE | 2025-12-26 |

### What This Means

1. **UI is structurally sound** - No hidden navigation, no order violations
2. **Accountability is surfaced** - Contracts visible, outcomes explainable
3. **Beta instrumentation exists** - Signals defined, scorecard printable

### The Rule (LOCKED)

> **No UI changes without scorecard signal.**

Any change request must cite:
- Which P0 fail triggered it, OR
- Which O4 pull criteria were met (all 4)

Vibes, preferences, and "feels like" are rejected.

---

## Beta Parameters

| Parameter | Value |
|-----------|-------|
| Founders | 3-5 maximum |
| Duration | 2-4 weeks OR 20-30 sessions (whichever first) |
| Observer | Must be present in every session |
| Artifact | Printed scorecard per session |

### Session Rules

1. Print the scorecard before each session
2. Do NOT explain unless asked
3. Do NOT defend the system
4. Write verbatim quotes only
5. Everything goes on the card

---

## Deployment Topology (AUTHORITATIVE)

> **CRITICAL:** Four subdomains, four separate deployments. Not routes under one domain.

This is a **security and trust boundary**, not a UI convenience.

### Why Four Subdomains

| Reason | Implication |
|--------|-------------|
| Security isolation | Separate cookies, CSP, auth audiences |
| Promotion discipline | Real preflight → prod boundary |
| Audit defensibility | Founder ops never under customer domain |
| Psychological clarity | Founders don't treat prod as test |

---

## Console Access URLs (Correct)

### 1. CUSTOMER CONSOLE (Production)

```
https://console.agenticverz.com
```

| Route | Purpose |
|-------|---------|
| `/guard` | Customer dashboard |
| `/guard/runs` | Run history & outcomes |
| `/guard/incidents` | Customer-visible incidents |
| `/guard/keys` | API key management |
| `/guard/limits` | Budget & rate limit awareness |

**Customers NEVER see:** `/ops`, `/fdr/*`, `/traces`

---

### 2. FOUNDER OPS CONSOLE (Production)

```
https://fops.agenticverz.com
```

| Route | Purpose |
|-------|---------|
| `/ops` | Founder operations dashboard |
| `/fdr/controls` | Kill-switch (freeze/unfreeze) |
| `/fdr/timeline` | Decision audit trail |
| `/incidents` | All incidents (founder view) |
| `/runs` | All runs (founder view) |
| `/traces` | Execution traces |

**Full visibility, full authority.**

---

### 3. PREFLIGHT CUSTOMER CONSOLE (Internal Only)

```
https://preflight-console.agenticverz.com
```

| Route | Purpose |
|-------|---------|
| `/guard` | Shadow customer dashboard |
| `/guard/runs` | Verify run UX before exposure |
| `/guard/incidents` | Verify incident UX |

**Same UI as customer console, different data + access.**
Like TestFlight — founders/QA verify exactly what customers will see.

---

### 4. PREFLIGHT FOUNDER OPS (Verification)

```
https://preflight-fops.agenticverz.com
```

| Route | Purpose |
|-------|---------|
| `/ops` | Infra health verification |
| `/cost` | Cost pipeline verification |
| `/incidents` | Incident summary (read-only) |
| `/promotion` | Promotion readiness check |

**Read-only. No actions. Truth verification before promotion.**

---

### API Endpoints

| Environment | URL |
|-------------|-----|
| Production API | `https://api.agenticverz.com` |
| Preflight API | `https://preflight-api.agenticverz.com` |
| Local Dev | `http://localhost:8000` |

---

## Beta Access (CURRENT - Existing Infrastructure)

> **Note:** Subdomains are NOT deployed. Beta runs on existing infrastructure.
> Global beta banner added to all pages (PIN-189 guardrail).

For founder beta sessions, use these URLs:

| What | URL | API Key |
|------|-----|---------|
| Ops Dashboard | `https://agenticverz.com/console/ops` | See .env |
| Kill-Switch | `https://agenticverz.com/console/fdr/controls` | See .env |
| Decision Timeline | `https://agenticverz.com/console/fdr/timeline` | See .env |
| Guard Console | `https://agenticverz.com/console/guard` | See .env |
| Incidents | `https://agenticverz.com/console/guard/incidents` | See .env |
| Runs | `https://agenticverz.com/console/guard/runs` | See .env |
| Traces | `https://agenticverz.com/console/traces` | See .env |

**Local Development:**

| What | URL | API Key |
|------|-----|---------|
| All Consoles | `http://localhost:5173/console/*` | `edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf` |
| API | `http://localhost:8000` | Same key |

---

## Beta Test Scenarios

### Scenario 1: Run Comprehension (P0)

**Setup:** Create a run with 3+ steps, one fails mid-execution.

**Test:**
1. Founder opens Guard Console → Runs
2. Clicks on the failed run
3. **Observe:** Can they explain WHY it failed using only the UI?

**Pass:** Founder points to OUTCOME section, names the failed step.
**Fail:** Founder asks "Why did this run do that?" after viewing O3.

---

### Scenario 2: Cost Delta Comprehension (P0)

**Setup:** Create a run where actual cost > estimated cost.

**Test:**
1. Founder views run detail
2. **Observe:** Do they notice the cost delta?

**Pass:** Founder says "It cost more because [reason from UI]."
**Fail:** Founder asks "Why did it cost more than expected?"

---

### Scenario 3: Navigation Flow (P0)

**Setup:** Create an incident linked to a run linked to a trace.

**Test:**
1. Founder starts at Incidents page
2. Clicks into incident detail
3. **Observe:** Can they reach the trace without confusion?

**Pass:** Founder navigates Incident → Run → Trace using links.
**Fail:** Founder clicks back/forth repeatedly or asks "Where do I see that?"

---

### Scenario 4: Memory Injection Visibility (P0)

**Setup:** Create a run with memory injection in PRE-RUN.

**Test:**
1. Founder views run detail
2. **Observe:** Do they see memory was used?

**Pass:** Founder points to PRE-RUN section, mentions "memory injected."
**Fail:** Founder asks "Was memory used here?"

---

### Scenario 5: Trust After Bad Outcome (P0/P1)

**Setup:** Create a run that completed but with expensive or unexpected result.

**Test:**
1. Founder views the run
2. **Observe:** Do they accept the explanation even if unhappy?

**Pass:** Founder says "I don't like it, but I understand why."
**Fail:** Founder says "This feels like it's hiding something."

---

### Scenario 6: O4 Pull Detection

**Setup:** Multiple runs with varying step counts.

**Test:**
1. Founder explores several runs
2. **Observe:** Do they ask the same question 3+ times about a specific entity?

**Valid Pull Example:** "Which step failed in this trace?" (asked 3 times)
**Invalid Pull Example:** "I want more details" (vibe, not signal)

---

## Weekly Synthesis Template

Complete every Friday (30 minutes max).

```
WEEK: ___  DATE: ___________

SESSIONS THIS WEEK: ___

1. P0 FAILS THIS WEEK
   [ ] Comprehension: ___ (count)
   [ ] Navigation: ___ (count)
   [ ] Trust: ___ (count)

2. VERBATIM QUESTIONS (asked 3+ times)
   Q1: "_________________________________"
       Entity: _____________ Times: ___
   Q2: "_________________________________"
       Entity: _____________ Times: ___

3. NAVIGATION HEALTH
   [ ] Founders navigate without help
   [ ] Breadcrumbs used implicitly
   [ ] No one asked for "global search"

4. DECISION
   [ ] CONTINUE BETA - signals unclear
   [ ] FIX REQUIRED - P0 fail identified (do not add features)
   [ ] END BETA - exit criteria met

5. NOTES (one sentence only)
   _________________________________________________
```

---

## Exit Criteria (From PIN-188)

End beta when ANY ONE is true:

| Condition | Meaning |
|-----------|---------|
| Zero P0 fails for 7 consecutive days | Comprehension achieved |
| "What should I do?" replaces "What happened?" | Truth density validated |
| Clear O4 pull emerges (all 4 criteria) | Depth need identified |
| Post-mortem writable using only UI | System is self-explanatory |

---

## What Happens After Beta

| Outcome | Next Step |
|---------|-----------|
| Beta Pass | Declare Runtime v1 stable, write public brief |
| O4 Unlock | Build exactly ONE O4, run validation |
| Beta Fail | Fix surfacing (not features), re-run |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | **BETA INFRASTRUCTURE DECISION** - Run beta on existing infra (agenticverz.com/console/*). Subdomains deferred post-beta. Global BetaBanner added to all consoles. |
| 2025-12-26 | **TOPOLOGY CORRECTION** - Fixed URL section. Four subdomains (not routes under one domain): console, fops, preflight-console, preflight-fops. Security/trust boundary preserved. |
| 2025-12-26 | Created PIN-189 - Phase A Closure & Beta Launch |
