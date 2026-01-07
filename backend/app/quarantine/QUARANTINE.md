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

## Restored Items

### founder_review.py → founder_contract_review.py

**Original Location:** `app/api/founder_review.py`
**Quarantine Date:** 2026-01-06
**Restored Date:** 2026-01-06
**New Location:** `app/api/founder_contract_review.py`

**Reason for Rename:** Original `app/api/founder_review.py` is now used for PIN-333 AUTO_EXECUTE review (evidence-only). CRM contract review restored with distinct name.

**Recovery Actions Completed:**
1. ✅ Created frontend page: `website/fops/src/pages/founder/ContractReviewContent.tsx`
2. ✅ Unified review page: `website/fops/src/pages/founder/FounderReviewPage.tsx`
3. ✅ Copied to `app/api/founder_contract_review.py`
4. ✅ Router registered in main.py
5. ✅ Added FOPS token authentication to all endpoints
6. ✅ Adapter import restored in adapters/__init__.py

**Routes Active:**
- `GET /founder/contracts/review-queue`
- `GET /founder/contracts/{contract_id}`
- `POST /founder/contracts/{contract_id}/review`

---

### founder_review_adapter.py → founder_contract_review_adapter.py

**Original Location:** `app/adapters/founder_review_adapter.py`
**Quarantine Date:** 2026-01-06
**Restored Date:** 2026-01-06
**New Location:** `app/adapters/founder_contract_review_adapter.py`

**Recovery Actions Completed:**
1. ✅ Copied to `app/adapters/founder_contract_review_adapter.py`
2. ✅ Export restored in adapters/__init__.py

---

## Currently Quarantined Items

*None - all items have been restored*

---

## Rules

- Files here must NOT be imported anywhere
- Files here must NOT be deleted without explicit approval
- Each file must have documentation in this file
- Recovery requires explicit human approval
