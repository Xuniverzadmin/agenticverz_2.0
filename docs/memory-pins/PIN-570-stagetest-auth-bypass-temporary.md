# PIN-570: Stagetest Auth Bypass (Temporary)

**Status:** ✅ COMPLETE
**Created:** 2026-02-15
**Category:** Auth

---

## Summary

Temporarily disabled auth on stagetest evidence console routes for development visibility. 4 files modified with TODO markers for re-enablement: (1) stagetest.py L2 router — verify_fops_token commented out, (2) gateway_policy.py — /hoc/api/stagetest/ added to PUBLIC_PATHS, (3) rbac_policy.py — RBAC exemption returning None before catch-all, (4) routes/index.tsx — FounderRoute wrapper removed. All changes marked with 'TODO: Re-enable auth'. Must be reverted before production hardening.

---

## Details

[Add details here]
