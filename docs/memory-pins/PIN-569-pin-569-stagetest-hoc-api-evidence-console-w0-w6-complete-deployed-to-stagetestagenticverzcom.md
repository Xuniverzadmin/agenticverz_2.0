# PIN-569: PIN-569: Stagetest HOC API Evidence Console — W0-W6 complete, deployed to stagetest.agenticverz.com

**Status:** ✅ COMPLETE
**Created:** 2026-02-15
**Category:** Architecture

---

## Summary

Implemented audit-ready, read-only stagetest evidence console. 7 workstreams (W0-W6): route prefix guard (0 forbidden), artifact schema+emitter (16 fields, SHA-256), artifact integrity validator, L2 router (5 GET /hoc/api/stagetest/* endpoints + verify_fops_token), L5 filesystem engine, 5 React components (StagetestPage/RunList/CaseTable/CaseDetail/Client), founder route wiring (/prefops/stagetest + /fops/stagetest), 8 Playwright tests, subdomain deploy plan, docs sync. Gate results: 12/14 pass (2 = Chromium infra). Deployed: DNS CNAME + Apache vhost + Cloudflare Origin SSL at stagetest.agenticverz.com. Commit 9cbf09e5 (26 files, +3299). Evidence: evidence_stagetest_hoc_api_2026_02_15/ (14 logs).

---

## Details

[Add details here]
