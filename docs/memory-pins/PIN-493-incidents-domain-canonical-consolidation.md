# PIN-493: Incidents Domain — Canonical Consolidation

**Created:** 2026-01-31
**Status:** COMPLETE
**Category:** Architecture / Domain Consolidation
**Related PINs:** PIN-470 (HOC Layer Inventory), PIN-484 (HOC Topology V2.0.0)

---

## Summary

Completed full consolidation of the incidents domain: duplicate analysis, canonical registration, naming fixes, literature generation, and deterministic tally verification. This is the pilot domain — lessons learned here drive the process for all remaining domains.

## Scope

- **Physical files:** 30 (17 L5_engines + 11 L6_drivers + 2 adapters)
- **Traced scripts:** 27 (in call graph via CALL_CHAINS.csv)
- **Total LOC:** ~8,200
- **L2 Features:** 22 (all COMPLETE, no gaps)

## Key Decisions

### 1. Zero Duplicates Confirmed
Previously flagged overlaps were reclassified:
- `incident_driver` vs `incident_engine` → FACADE_PATTERN (orchestration facade delegates to decision engine)
- `prevention_engine` vs `recovery_rule_engine` → FALSE_POSITIVE (before-incident vs after-incident, zero shared code)

### 2. All 30 Scripts Declared Canonical
Every script has a unique purpose. No merges, no removals. Full registry in `INCIDENT_CANONICAL_SOFTWARE_LITERATURE.md`.

### 3. Naming Fix Applied (N1)
- `ExportBundleService` → `ExportBundleDriver` in `L6_drivers/export_bundle_driver.py`
- Backward-compatible alias preserved
- L2 API callers updated to `get_export_bundle_driver()`
- Verified by `hoc_incidents_tally.py` (9/9 PASS)

### 4. Five Uncalled Functions Classified
All in `policy_violation_engine.py`:
- 1 INTERNAL (indirect delegation call)
- 1 WIRED (false positive — called from driver)
- 3 PENDING (design-ahead for PIN-195, PIN-407)

### 5. Deferred Issues (wiring exercise post-all-domains)
| ID | Issue | Severity |
|----|-------|----------|
| V1 | `incident_aggregator` (L6) imports `IncidentSeverityEngine` (L5) | HIGH |
| V2 | policies `lessons_engine` (L5) imports incidents `lessons_driver` (L6) directly | MEDIUM |
| V3 | analytics `cost_anomaly_detector` imports from stale `L3_adapters` path | HIGH |
| W1 | `export_bundle_driver` called directly from L2 API, bypasses L4 | MEDIUM |
| W2 | `lessons_driver` has no L5 caller within incidents domain | MEDIUM |
| E1 | `anomaly_bridge._create_incident()` has un-extracted direct SQL | LOW |

## Bible Generator Improvements (apply to all domains)

Three improvements made to `hoc_software_bible_generator.py`:

1. **Role-aware overlap detection** — classifies scripts by role (FACADE, ALGORITHM, PERSISTENCE). Same noun + different role = FACADE_PATTERN, not overlap. Eliminated false positives.

2. **Uncalled function classification** — reads source files for `self.method()` calls (→INTERNAL) and PIN references (→PENDING). Previously all uncalled functions were undifferentiated.

3. **CANONICAL_REGISTRY.md generation** — per-domain auditable artifact with purpose, role, callers, delegates, overlap verdict per script.

## Lessons Learned (for subsequent domains)

| # | Lesson | Impact |
|---|--------|--------|
| L1 | Overlap detection must consider role, not just noun | Generator updated |
| L2 | Uncalled detection misses self.method() and cross-file sync calls | Generator updated |
| L3 | L6→L5 imports are common violation pattern | Check in every domain |
| L4 | Cross-domain L5→L6 signals wrong domain ownership | Use as ownership heuristic |
| L5 | Physical file count ≠ traced script count | Always use tally script for physical, bible for call graph |
| L6 | Naming violations break automated classification | Fix naming first, then analyze |

## Artifacts Produced

| Artifact | Path |
|----------|------|
| Full Literature | `literature/hoc_domain/incidents/INCIDENT_CANONICAL_SOFTWARE_LITERATURE.md` |
| Software Bible | `literature/hoc_domain/incidents/SOFTWARE_BIBLE.md` |
| Canonical Registry | `literature/hoc_domain/incidents/CANONICAL_REGISTRY.md` |
| Tally Script | `scripts/ops/hoc_incidents_tally.py` |
| Bible Generator (improved) | `scripts/ops/hoc_software_bible_generator.py` |

## Process Template (for next domains)

1. Read every file in the domain (two passes — second pass skeptical of first)
2. Classify duplicates: TRUE_DUPLICATE, FACADE_PATTERN, or FALSE_POSITIVE
3. Propose canonical candidates → get approval
4. Fix simple naming violations immediately
5. Document architecture violations with correct topology diagrams
6. Document wiring gaps with expected wiring and recommendations
7. Generate literature + tally pyscript
8. Run both verification scripts
9. Create memory PIN
10. Freeze domain, move to next

## Verification Commands

```bash
python3 scripts/ops/hoc_incidents_tally.py          # 9/9 PASS
python3 scripts/ops/hoc_software_bible_generator.py --domain incidents  # 0 overlaps, 27 scripts
```
