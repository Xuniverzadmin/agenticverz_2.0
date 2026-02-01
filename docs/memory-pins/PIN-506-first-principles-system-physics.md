# PIN-506 — First-Principles System Physics

**Status:** RATIFIED
**Date:** 2026-01-31
**Category:** Architecture / Governing Laws
**Depends On:** PIN-484 (HOC Topology V2.0.0), PIN-504 (Cross-Domain Resolution)
**Blocks:** All future architectural work must comply

---

## Purpose

Define the **target physics** of the system — the invariant properties that, if maintained, guarantee stability, speed, single-ownership troubleshooting, and agent-safety. These are non-negotiable laws, not guidelines.

---

## Prime Objective

> **At any moment, for any execution, there must be exactly one place that can be blamed.**

If this holds: incidents are debuggable, performance is explainable, ownership is unambiguous, automation and agents are safe. Everything below exists only to enforce this.

---

## The 9 Laws

### Law 1 — Execution Must Have a Single Authority

> **Every execution has exactly one authority that decides *what happens next*.**

- No "helpful" engines deciding on their own
- No drivers called opportunistically
- No cross-domain negotiation
- **L4 (Handlers / Runtime Authority)** is the *only* execution authority
- L4 receives intent, selects domain capabilities, sequences calls, owns retries/ordering/compensation
- L5/L6 **never** decide flow

**Debugging consequence:** "Which handler ran?" answers 80% of debugging instantly.

---

### Law 2 — Domains Must Be Sovereign, Not Cooperative

> **Domains do not collaborate. They only respond.**

Collaboration implies shared assumptions, hidden coupling, split ownership.

- A domain exposes: **capabilities** (functions) and **facts** (schemas)
- A domain never: calls another domain or reasons about another domain's state
- Cross-domain work is **system choreography**, not business logic
- Therefore it belongs **outside domains** (in L4 spine)

**Debugging consequence:** Each domain has one owner. Cross-domain bugs point to choreography, not domain code.

---

### Law 3 — Orchestration Is a Distinct Concern (And Must Be Rare)

> **Orchestration exists only when ordering, fan-out, retries, or compensation exist.**

If none of these exist: do **not** orchestrate — extract pure functions instead.

- Orchestration lives in **spine**, is explicit, is named as orchestration (coordinator / handler)
- **Anti-Law:** Orchestration must never be "convenient access." If orchestration is easy, it will spread.

**Consequence:** The system does not collapse into a "smart middle." Complexity stays localized and visible.

---

### Law 4 — Execution Context Must Never Leak

> **Only the authority owns execution context.**

Execution context includes: sessions, transactions, retries, timing, idempotency, logging scope.

- Domains accept **facts**, not context
- Coordinators accept **facts**, not sessions
- Drivers accept **commands**, not decisions

**Consequence:** Transaction bugs disappear. Retry logic is explainable. Observability becomes coherent.

---

### Law 5 — Speed Comes From Predictability, Not Cleverness

> **Fast systems are systems where the runtime knows what will happen.**

- Deterministic call paths
- No hidden imports
- No runtime discovery
- No reflection-driven behavior in hot paths

**Practical effects:** CPU cache friendliness, fewer allocations, stable latency curves, easier profiling.

**Consequence:** p95 ≈ p50. Latency regressions are attributable to a single layer.

---

### Law 6 — Types Are Contracts, Not Utilities

> **Types describe reality; they do not help execute it.**

- Schemas are: immutable, behavior-free, versionable
- No helpers, no convenience methods, no hidden defaults
- L5_schemas files contain **only** enums, dataclasses, exception classes, constants

**Consequence:** L2 can depend on schemas safely. Static analysis becomes meaningful. Breaking changes are obvious.

---

### Law 7 — Ownership Must Be Visible in the Filesystem

> **If ownership is not obvious from the path, it does not exist.**

Each directory answers: Who owns this? Who is allowed to call this? Who is forbidden?

- `hoc/cus/{domain}` → domain owner
- `hoc_spine/orchestrator` → system owner
- `L4/handlers` → runtime authority owner

**Consequence:** New engineers don't ask "where should this go?" Agents can operate safely. Reviews become mechanical.

---

### Law 8 — Troubleshooting Must Collapse the Search Space

> **Debugging must reduce to: *which authority ran, with what inputs*.**

- Every handler logs start/end, chosen path, domain calls
- Domain code logs *only domain facts*

When an incident happens, answer in order:
1. Which handler?
2. Which orchestration path?
3. Which domain capability?
4. Which driver?

Never "all of the above."

**Consequence:** MTTR collapses. Postmortems become short. Confidence increases.

---

### Law 9 — Enforcement Must Be Structural, Not Cultural

> **If a rule can be broken accidentally, it will be.**

- Validators enforce: directionality, ownership, import legality
- Humans do not remember laws; tools do

**Consequence:** Architecture survives scale. You do not become the bottleneck. The system is agent-ready.

---

## Final Shape (Compressed)

If the system is correct:

| Layer | Role |
|-------|------|
| **L2** | Expresses intent, nothing else |
| **L4** | Owns execution, sequencing, failure |
| **L5** | Computes domain truth |
| **L6** | Performs side effects |
| **Spine** | Orchestrates when unavoidable |
| **Schemas** | Describe, never act |
| **Validators** | Prevent decay |

---

## The Ultimate Test

> *"If this breaks at 3am, can I point to exactly one file and say: this owned the decision?"*

If yes → system is correct.
If no → architecture is leaking.

---

## Enforcement

All future code changes, architecture decisions, and refactoring MUST be evaluated against these 9 laws. Violations require explicit justification and a remediation plan with a PIN reference.

Validators that enforce these laws:
- `scripts/ops/hoc_cross_domain_validator.py` — Laws 2, 3, 9
- `scripts/ops/layer_validator.py` (BLCA) — Laws 1, 7, 9
- File headers — Law 7
- OperationRegistry logging — Law 8
