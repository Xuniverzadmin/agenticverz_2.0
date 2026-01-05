# PIN-299: Tech Debt Clearance - Forensic Inventory & Governed Actions

**Status:** 🏗️ IN_PROGRESS
**Created:** 2026-01-05
**Category:** Governance / Tech Debt
**Milestone:** Tech Debt Clearance

---

## Summary

Governance-first tech debt clearance workflow. Forensic inventory of 30+ untracked files, RBAC v2 promotion path, auth debt resolution. No deletion or promotion without explicit decision records.

---

## Details

## Task Contract

**Mode:** Governance-first, forensic, founder-supervised
**Invariant:** No deletion, promotion, or refactor without understanding + explicit decision record

---

## Global Guards (Always On)

Claude MUST:
- Operate on facts only until classification is complete
- Never delete, refactor, or promote code pre-classification
- Never assume replacement unless proven by references
- Produce decision tables, not opinions
- Pause and ask when ambiguity remains

---

## Phase 1 — Forensic Inventory (NO DECISIONS)

### T1. Untracked / Partially Implemented Files
- [ ] Enumerate all untracked / modified files
- [ ] Extract: path, layer, imports, dependents, authority, data, runtime reachable, purpose

---

## Phase 2 — Classification (STILL NO ACTION)

### T2. Classify Each File
- [ ] UNIQUE & REQUIRED
- [ ] DUPLICATE
- [ ] LEGACY
- [ ] EXPERIMENTAL
- [ ] AMBIGUOUS

---

## Phase 3 — Decision Record (FOUNDER-LED)

### T3. Decision Support
- [ ] Evidence summary per file
- [ ] Risk of deletion / promotion
- [ ] Founder decides: PROMOTE, DELETE, QUARANTINE, DEFER

---

## Phase 4 — Governed Actions (ONLY AFTER DECISION)

### T4. Promotion Path
- [ ] Authority declared
- [ ] Layer correctness (BLCA clean)
- [ ] Tests added/mapped
- [ ] Governance records updated

### T5. Deletion Path
- [ ] No inbound references
- [ ] No runtime dependency
- [ ] Decision record exists

### T6. Quarantine Path
- [ ] Move to quarantine location
- [ ] Add warning header
- [ ] Ensure nothing imports it

---

## Phase 5 — RBAC v2 Promotion

### T7. RBAC v1 vs v2 Diff Analysis
- [ ] Run identical request matrix
- [ ] Capture mismatches
- [ ] Identify impact

### T8. Founder Authority Modeling
- [ ] Define cross-tenant visibility
- [ ] Define debug access
- [ ] Define explicit write powers

### T9. RBAC v2 Cutover
- [ ] Enable RBAC v2
- [ ] Disable RBAC v1
- [ ] Update governance records

---

## Phase 6 — Auth & Security Debt

### T10. JWT Verification
- [ ] Implement strict vs trusted modes
- [ ] Enforce strict for customer/console

### T11. Auth Fallback Audit
- [ ] Locate API-key-as-token paths
- [ ] Identify replacements

### T12. Machine Token Validation
- [ ] Identify all machine token logic
- [ ] If replaced → delete
- [ ] If needed → quarantine

---

## Phase 7 — Subdomain Plumbing

### T13. Subdomain Separation
- [ ] Wire console.agenticverz.com
- [ ] Wire fops.agenticverz.com
- [ ] Separate cookies, auth audience

---

## Phase 8 — Known Messy Areas

### T14. Legacy Routes (410s)
- [ ] Identify callers
- [ ] Determine replacement paths
- [ ] Recommend action

---

## Phase 9 — Governance Hygiene

### T15. Update Records
- [ ] Hygiene notes
- [ ] Governance logs
- [ ] Closure appendices

---

## Current Status

**Active Task:** T1 — Forensic Inventory
**Blockers:** None
**Next Decision Point:** T3 (Founder decides)


---

## Related PINs

- [PIN-298](PIN-298-.md)
- [PIN-290](PIN-290-.md)
- [PIN-297](PIN-297-.md)
