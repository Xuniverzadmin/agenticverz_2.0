# PIN-446: Attention Feedback Loop Implementation

**Status:** ✅ COMPLETE
**Created:** 2026-01-19
**Category:** Activity Domain / Signal Feedback

---

## Summary

Implemented operator acknowledge/suppress controls for Activity signals using existing audit_ledger infrastructure. No new tables created.

---

## Details

## Overview

Implemented the Attention Feedback Loop for Activity signals, allowing operators to acknowledge or temporarily suppress signals in the attention queue.

## Key Highlights

### Critical Invariants (LOCKED)
- **SIGNAL-ID-001**: Canonical fingerprint derived from backend projection, never client input
- **ATTN-DAMP-001**: Idempotent 0.6x dampening for acknowledged signals
- **SIGNAL-SUPPRESS-001**: Time-bound suppression only (15-1440 minutes, no permanent)
- **SIGNAL-SCOPE-001**: Tenant-scoped suppression, actor for accountability

### API Endpoints Added
- `POST /api/v1/activity/signals/{signal_fingerprint}/ack` — Acknowledge signal
- `POST /api/v1/activity/signals/{signal_fingerprint}/suppress` — Suppress temporarily

### Design Principles
1. Signals remain projections — feedback is overlay metadata
2. Uses existing audit_ledger — no new tables
3. Acknowledgment = responsibility, not hiding
4. No permanent silencing allowed

### Files Created
- `backend/app/services/activity/signal_identity.py` — Fingerprint computation
- `backend/app/services/activity/signal_feedback_service.py` — Feedback operations
- `docs/architecture/activity/ATTENTION_FEEDBACK_LOOP.md` — Architecture doc
- `backend/scripts/sdsr/scenarios/SDSR-ACT-V2-SIGNAL-ACK-001.yaml`
- `backend/scripts/sdsr/scenarios/SDSR-ACT-V2-SIGNAL-SUPPRESS-001.yaml`

### Files Modified
- `backend/app/models/audit_ledger.py` — SIGNAL entity + event types
- `backend/app/services/logs/audit_ledger_service.py` — Convenience methods
- `backend/app/services/activity/attention_ranking_service.py` — Dampening + filtering
- `backend/app/api/activity.py` — Endpoints + response models
- `docs/architecture/activity/ACTIVITY_DOMAIN_CONTRACT.md` — Section 21-22

## Validation
- BLCA: 0 violations (961 files scanned)
- SDSR scenarios created for E2E validation

## Architecture Reference
- Primary: `docs/architecture/activity/ATTENTION_FEEDBACK_LOOP.md`
- Contract: `docs/architecture/activity/ACTIVITY_DOMAIN_CONTRACT.md` Section 21-22
