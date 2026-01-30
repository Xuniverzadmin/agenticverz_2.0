# PIN-491: HOC Spine Literature Upgrade + L5 Pairing Gap Detector

**Status:** ✅ COMPLETE (All Phases: Literature, Gap Detector, Construction Plan A-C)
**Created:** 2026-01-30
**Category:** Architecture

---

## Summary

Upgraded all 65 HOC Spine literature files with three new machine-parseable sections (Export Contract, Import Boundary, L5 Pairing Declaration) and created `l5_spine_pairing_gap_detector.py` to scan all L2 API and L4 orchestrator files for missing L5 engine wiring through the spine.

**Construction Plan Execution (L2-L4-L5):**

| Phase | Operations | Status | Date |
|-------|-----------|--------|------|
| A.0 — Infrastructure | 1 (operation_registry.py) | ✅ COMPLETE | 2026-01-30 |
| A.1 — Facade domains | 10 | ✅ COMPLETE | 2026-01-30 |
| A.2 — Compound facades (logs) | 6 | ✅ COMPLETE | 2026-01-30 |
| A.3 — Controls | 2 | ✅ COMPLETE | 2026-01-30 |
| A.4 — Activity | 4 | ✅ COMPLETE | 2026-01-30 |
| A.5 — Policies | 9 | ✅ COMPLETE | 2026-01-30 |
| B — Orphan classification | 153 | ✅ COMPLETE | 2026-01-30 |
| C — CI freeze | — | ✅ COMPLETE | 2026-01-30 |

**Current gap detector output (after A.5):** Wired=31, Gaps=1, Orphaned=153

---

## Details

### Literature Upgrade

Added three YAML-block sections to every `.md` file in `literature/hoc_spine/`:

1. **Export Contract** — Lists all exported functions and classes with signatures, method inventories, and declared consumers. Extracted from AST.

2. **Import Boundary** — Declares allowed/forbidden inbound callers (per folder governance rules from FOLDER_SPEC), actual imports classified by category (spine_internal, l7_model, external), and any boundary violations.

3. **L5 Pairing Declaration** — Declares which customer domains and L5 engines this spine script serves, whether they are wired through L4, and any gaps. Populated by the gap detector.

Also added **Section 6: L5 Pairing Aggregate** table to all 9 `_summary.md` folder overviews.

### Gap Detector Findings

**185 total L5 engines** across 10 customer domains:

| Metric | Initial (A.0) | After A.1 | After A.2 | After A.3 | After A.4 | After A.5 |
|--------|---------------|-----------|-----------|-----------|-----------|-----------|
| Wired via L4 orchestrator | 0 | 10 | 16 | 18 | 22 | 31 |
| Direct L2→L5 (gaps) | 32 | 22 | 16 | 14 | 10 | 1 |
| Orphaned (no callers) | 153 | 153 | 153 | 153 | 153 | 153 |

**Remaining gap (1):**
- recovery.py → recovery_rule_engine.py (L6-only pattern, excluded from A-phase scope)

**Orphan domains (153 total):**
- policies: 52 orphaned, integrations: 34, analytics: 18, incidents: 15, logs: 12, controls: 9, account: 8, activity: 4, api_keys: 1

**Key insight (initial scan):** Zero L5 engines were wired through L4 orchestrator. All 32 active L2→L5 paths bypassed the spine entirely, confirming a systemic gap (PIN-487). Construction plan execution began immediately — Phase A.0 built the `operation_registry.py`, Phase A.1 wired 10 facade-pattern operations, reducing gaps from 32 to 22.

### Files Modified

| File | Change |
|------|--------|
| `scripts/ops/hoc_spine_study_validator.py` | Added `_get_allowed_inbound()`, `_get_forbidden_inbound()`, `_detect_boundary_violations()`, extended `generate_markdown()` with 3 new sections, extended `generate_folder_overview()` with Section 6, extended `validate_literature()` with section/boundary checks |
| `scripts/ops/l5_spine_pairing_gap_detector.py` | **NEW** — ~400 lines, AST-based L5 gap scanner with `--domain`, `--json`, `--update-literature` CLI |
| `scripts/ops/l5_orphan_classifier.py` | **NEW** (Phase B) — ~500 lines, AST-based orphan classifier with `--domain`, `--json`, `--verify`, `--output` CLI |
| `docs/architecture/hoc/L5_ORPHAN_CLASSIFICATION.md` | **NEW** (Phase B) — Full classification report for all 185 L5 engines |
| `docs/architecture/hoc/L2_L4_L5_BASELINE.json` | **NEW** (Phase C) — Frozen baseline for regression detection |
| `scripts/preflight/check_l2_l4_l5_freeze.py` | **NEW** (Phase C) — Preflight freeze enforcement (FREEZE-001, FREEZE-003) |
| `scripts/preflight/run_all_checks.sh` | Updated (Phase C) — Added L2-L4-L5 Freeze check |
| `literature/hoc_spine/**/*.md` | 65 script files + 9 summary files + INDEX.md regenerated with new sections |

### Commands

```bash
# Regenerate literature with new sections
python3 scripts/ops/hoc_spine_study_validator.py --generate --output-dir literature/hoc_spine/

# Run gap detector (text report)
python3 scripts/ops/l5_spine_pairing_gap_detector.py

# Run gap detector (single domain)
python3 scripts/ops/l5_spine_pairing_gap_detector.py --domain policies

# Run gap detector (JSON for CI)
python3 scripts/ops/l5_spine_pairing_gap_detector.py --json

# Backfill pairing declarations into literature
python3 scripts/ops/l5_spine_pairing_gap_detector.py --update-literature

# Validate literature (checks new sections + boundary drift)
python3 scripts/ops/hoc_spine_study_validator.py --validate literature/hoc_spine/

# Phase B: Orphan classification
python3 scripts/ops/l5_orphan_classifier.py

# Phase B: Single domain
python3 scripts/ops/l5_orphan_classifier.py --domain policies

# Phase B: Verify all classified
python3 scripts/ops/l5_orphan_classifier.py --verify

# Phase B: Markdown report
python3 scripts/ops/l5_orphan_classifier.py --output docs/architecture/hoc/L5_ORPHAN_CLASSIFICATION.md

# Phase C: Freeze baseline
python3 scripts/ops/l5_spine_pairing_gap_detector.py --freeze-baseline

# Phase C: Check against baseline (CI mode)
python3 scripts/ops/l5_spine_pairing_gap_detector.py --check

# Phase C: Full preflight freeze enforcement
python3 scripts/preflight/check_l2_l4_l5_freeze.py
```

### Verification

```
Export Contract sections:     65/65
Import Boundary sections:     65/65
L5 Pairing sections:          65/65
Validation drift:             0
```

---

## References

- PIN-488: HOC Spine Literature Study Complete
- PIN-489: HOC Spine Constitutional Enforcement
- PIN-490: HOC Spine Constitution Document
- PIN-487: L4-L5 Linkage Analysis
- PIN-470: HOC Layer Inventory
