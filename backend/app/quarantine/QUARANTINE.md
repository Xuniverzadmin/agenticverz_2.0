# Quarantine Directory

**Created:** 2026-01-06
**Phase:** Phase 1.1 - Legacy Resolution & Structural Hardening
**Reference:** PIN-317

---

## Purpose

This directory contains backend artifacts that have been quarantined during Phase 1.1.

Quarantined items are NOT deleted because they may have:
- Historical significance
- Future intent
- Architectural value that hasn't been connected yet

---

## Quarantined Items

### founder_review.py

**Original Location:** `app/api/founder_review.py`
**Quarantine Date:** 2026-01-06
**Reason:** API mounted but no frontend page calls `/founder/contracts/*` endpoints

**Evidence:**
- Routes: `/founder/contracts/review-queue`, `/founder/contracts/{id}`, `/founder/contracts/{id}/review`
- Was mounted in main.py (registration removed during quarantine)
- No frontend page calls these endpoints
- References PART2_CRM_WORKFLOW_CHARTER.md (future feature)

**Recovery Path:**
1. Create frontend page for contract review workflow
2. Move file back to `app/api/`
3. Restore router registration in main.py
4. Restore adapter import in adapters/__init__.py

---

### founder_review_adapter.py

**Original Location:** `app/adapters/founder_review_adapter.py`
**Quarantine Date:** 2026-01-06
**Reason:** Adapter for founder_review.py, quarantined together

**Evidence:**
- Only consumer was founder_review.py (also quarantined)
- Part of L3 adapter layer for founder review workflow
- References PART2_CRM_WORKFLOW_CHARTER.md (future feature)

**Recovery Path:**
1. Restore alongside founder_review.py
2. Move file back to `app/adapters/`
3. Restore export in adapters/__init__.py

---

## Rules

- Files here must NOT be imported anywhere
- Files here must NOT be deleted without explicit approval
- Each file must have documentation in this file
- Recovery requires explicit human approval
