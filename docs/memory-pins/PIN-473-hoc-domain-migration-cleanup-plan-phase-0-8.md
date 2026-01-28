# PIN-473: HOC Domain Migration & Cleanup Plan (Phase 0-8)

**Status:** 📋 PROPOSED
**Created:** 2026-01-27
**Category:** Architecture / HOC / Migration

---

## Summary

Comprehensive 9-phase plan to migrate 84 misplaced domain files, lock domains, detect duplicates, consolidate general/, refactor clusters, and normalize import paths across 11 HOC customer domains.

---

## Details

## Overview

Phase 0-8 deterministic migration and cleanup plan for HOC customer domains.

## Problem Statement

1. **Domain Misplacement:** 84 files identified as MISPLACED in V3 Manual Audit Workbook
2. **Function Duplication:** Multiple files with same/similar/superset functions (e.g., logs export/evidence cluster with 9 overlapping files)
3. **Cross-Domain Duplicates:** 11 filenames duplicated across domains (runtime_switch.py in 3 domains, etc.)
4. **Policies Bloat:** 80 L5_engines files including DSL infrastructure that belongs in general/

## Phase Summary

| Phase | Purpose | Script |
|-------|---------|--------|
| P0 | Generate Migration Manifest | hoc_phase0_manifest_generator.py |
| P1 | Validate Migration Plan | hoc_phase1_migration_validator.py |
| P2 | Execute Migration (84 files) | hoc_phase2_migration_executor.py |
| P3 | Lock Domains | hoc_phase3_domain_locker.py |
| P4 | Post-Migration Validation | hoc_phase4_post_migration_validator.py |
| P5 | Duplicate Detection (3 modes) | hoc_phase5_duplicate_detector.py |
| P6 | Consolidate General | hoc_phase6_consolidator.py |
| P7 | Refactor Domain Clusters | hoc_phase7_cluster_refactor.py |
| P8 | Import Path Normalization | hoc_phase8_import_normalizer.py |

## Key Decisions

- Each phase has a supporting pyscript for deterministic execution and validation
- Every phase produces validation artifacts and exit criteria
- Phase 2 includes rollback capability via backup archive
- Phases 0-4 (migration) must complete before Phases 5-8 (cleanup)
- Domain locks prevent drift after migration

## Migration Stats (From Audit Workbook)

| Target Domain | Files Moving In |
|---------------|-----------------|
| general | ~20 |
| controls | ~15 |
| integrations | ~12 |
| logs | ~6 |
| policies | ~4 |
| analytics | ~2 |

## Architecture Rules (Phase 8)

- ARCH-001: Domains MAY import from general/
- ARCH-002: Domains MUST NOT import from other domains (except via general)
- ARCH-003: general/ MUST NOT import from any domain
- ARCH-004: All shared utilities MUST be in general/

## Artifacts

- Full Plan: backend/app/hoc/cus/docs/migration/HOC_MIGRATION_PLAN.md
- Audit Workbook: backend/app/hoc/cus/_domain_map/V3_MANUAL_AUDIT_WORKBOOK.md
- Domain Map: backend/app/hoc/cus/_domain_map/shadow_domain_map_v2.csv

## Related

- PIN-470: HOC Layer Inventory
- V3_MANUAL_AUDIT_WORKBOOK.md: Domain ownership decisions
