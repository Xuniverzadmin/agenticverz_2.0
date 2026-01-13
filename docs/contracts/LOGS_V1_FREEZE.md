# LOGS DOMAIN — V1 FREEZE (AUDIT LEDGER ONLY)

**Status:** FROZEN
**Effective:** 2026-01-13
**Scope:** Customer Console v1, Preflight Console v1
**Applies to:** Backend, Frontend, UX, Docs
**Reference:** PIN-413

---

## 1. Domain Purpose (Locked)

**Logs answers one question only:**

> *"What immutable governance actions occurred, and in what order?"*

Logs are **not**:

* Debug tooling
* Execution tracing
* Infrastructure monitoring

Those belong to future versions.

---

## 2. Logs v1 Domain Structure (Locked)

```
Logs (Domain)
└── Audit Ledger (Subdomain)
    └── Entries (O2)
        └── Entry Detail (O3)
```

### Explicit Non-Goals (v1)

* ❌ LLM Run logs
* ❌ Token-level traces
* ❌ System / infra logs
* ❌ Debug output
* ❌ Streaming or tailing

If it is mutable, high-volume, or ephemeral — it does **not** belong in Logs v1.

---

## 3. Audit Ledger — Canonical Definition

### What qualifies as an Audit Ledger entry?

An entry MUST be:

* **Immutable**
* **Append-only**
* **Causally meaningful**
* **Governance-relevant**

Examples (allowed):

* Policy rule created / modified / retired
* Policy enforcement decision taken
* Limit breached / exhausted
* Incident acknowledged / resolved
* Manual override performed

Examples (forbidden):

* Model prompt text
* Token streams
* Execution steps
* Retry attempts
* Internal debug logs

---

## 4. API Surface (Locked)

### Backend (Already Implemented)

```
GET /api/v1/runtime/logs/audit        → O2 list
GET /api/v1/runtime/logs/audit/{id}   → O3 detail
```

### Guarantees

* Read-only
* Tenant-isolated
* Time-ordered
* Index-backed
* No deletes
* No updates

---

## 5. O-Level Semantics (Locked)

| Order | Meaning                          |
| ----- | -------------------------------- |
| O1    | Navigation entry to Audit Ledger |
| O2    | List of audit entries            |
| O3    | Single audit entry detail        |
| O4    | ❌ Not applicable                 |
| O5    | ❌ Not applicable                 |

Audit Ledger **does not have Evidence or Proof views** — it *is* the proof.

---

## 6. Frontend Rules (Locked)

### Sidebar

* Label: **Logs**
* Subdomain label: **Audit Ledger**

### O1 Panels

* Navigation only
* No counts
* No fetching

### O2 List

* Time-ordered table
* Filters: event_type, actor_type, time range
* Empty-state compliant (UX invariants)

### O3 Detail

* Full event payload
* Before / after snapshots (if present)
* Linked entities (LLM Run, Policy Rule, Incident)

---

## 7. Explicit Deferrals (Documented)

The following are **v2+ candidates** and MUST NOT appear in v1 code, UI, or routes:

* `/logs/llm-runs`
* `/logs/system`
* Streaming / tailing
* Search across raw execution text

These require **capture-path validation** and are not part of this freeze.

---

## 8. Enforcement Rules

* ❌ No new Logs endpoints without a new PIN
* ❌ No frontend placeholders for deferred subdomains
* ❌ No "coming soon" UI
* ❌ No stubs
* ❌ No reuse of Audit Ledger for debugging

Any violation = architectural regression.

---

## 9. Freeze Declaration

**Logs v1 is now FROZEN** with:

* Exactly **one subdomain**
* Exactly **one data source**
* Exactly **one purpose**

No further expansion without an explicit v2 design pin.

---

## References

* PIN-413: Domain Design — Overview & Logs (CORRECTED)
* PIN-412: Incidents & Policies (V1_FROZEN)
* `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`
