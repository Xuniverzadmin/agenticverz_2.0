# Global Coherence Plan (System + Customer Domains)

## North Star
Build a governance console that monitors LLM runs, detects incidents, enforces policies, applies controls, integrates with customer environments, and provides analytics — backed by deterministic system execution through hoc_spine.

---

## Phase 1 — Re-Anchor the System (Start Here)
**Goal:** Re-establish one source of truth for what exists, what is wired, and what is canonical.

### What to do
1. Declare domain intent (customer + system):
   - Customer: Activity, Incidents, Policies, Controls, Logs, Analytics, Integrations, Overview, API Keys, Accounts.
   - System: hoc_spine (orchestrator, authority, consequences, drivers, lifecycle).
2. Align canonical literature to intent.
3. Confirm execution topology (L2 → L4 → L5 → L6) for each domain.

### Output
- Unified system truth map (intent vs wiring)
- No fixes yet, just verified truth

---

## Phase 2 — Stitch Execution (System Spine First)
**Goal:** Ensure hoc_spine is the single owner of execution and every domain flows through it.

### What to do
1. Verify hoc_spine orchestration (registry + handlers).
2. Verify lifecycle and consequences (active, suspended, terminated).
3. Verify authority boundaries (hoc_spine owns execution flow).

### Output
- hoc_spine confirmed as stable execution anchor

---

## Phase 3 — Validate Customer Domains (In Order)
**Goal:** Confirm each domain aligns to customer-facing mission and attaches to hoc_spine.

### Order (coherence-based)
1. Activity → Incidents → Policies → Controls
2. Logs → Analytics
3. Integrations
4. Overview
5. Accounts + API Keys

### Output
- Each domain wired and coherent
- Gaps logged as TODOs

---

## Phase 4 — End-to-End Verification (End Here)
**Goal:** Prove the system is deterministic and truth-preserving.

### What to do
1. Run domain tests (customer + system facing).
2. Run SDSR and replay.
3. Validate audit trails (traceable, replayable).

### Output
- Test evidence + audit logs proving truth preservation

---

## Start and End
**Start:** Phase 1 — Truth Map  
**End:** Phase 4 — Proof of Integrity

---

## First Execution Step
Begin with Activity + Incidents to ground the event pipeline, then move to Policies and Controls.
