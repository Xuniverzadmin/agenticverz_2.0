# PIN-485: HOC V2.0.0 Migration Complete — general/ Abolished

**Status:** ✅ COMPLETE
**Created:** 2026-01-28
**Category:** Architecture

---

## Summary

## HOC Topology V2.0.0 Migration — COMPLETE

All 8 phases of the V2.0.0 migration are done.

### What Happened
- Phase 1-6: Created hoc_spine/, moved 79 files from cus/general/ into hoc_spine/ subdirectories (orchestrator, authority, services, schemas, drivers, frontend/projections, mcp)
- Phase 7: Updated 70+ import statements across the entire codebase from app.hoc.cus.general.* to app.hoc.hoc_spine.*
- Phase 8: Deleted cus/general/ (83 files — all duplicates). Zero references remain.

### hoc_spine Final Structure (79 files)
- authority/ (8) — governance config, contracts, runtime decisions
- orchestrator/ (6+sub) — execution entry, lifecycle, job execution
- drivers/ (13) — cross-domain + infrastructure DB operations
- services/ (24) — shared infrastructure (facades, utilities, time, audit)
- schemas/ (9) — shared types (RAC, common, agent, plan, etc.)
- frontend/projections/ (1) — rollout_projection
- mcp/ (2) — MCP server registry
- consequences/ (stub)

### Key Import Mappings
- L4_runtime.engines -> hoc_spine.orchestrator
- L5_engines -> hoc_spine.services / authority
- L5_schemas -> hoc_spine.schemas
- L6_drivers -> hoc_spine.drivers
- L5_utils.time -> hoc_spine.services.time
- L5_controls -> hoc_spine.authority / drivers
- L5_lifecycle -> hoc_spine.orchestrator.lifecycle
- L5_workflow.contracts -> hoc_spine.authority.contracts
- L5_support.CRM -> hoc_spine.orchestrator.execution
- L5_ui -> hoc_spine.frontend.projections

### Binding Documents
- Topology spec: docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md
- Migration manifest: docs/architecture/topology/V2_MIGRATION_MANIFEST.md (COMPLETE)
- Supersedes: PIN-470 (inventory), builds on PIN-484 (ratification)

### Remaining
- _deprecated_L3/ still exists for human review (not active code)
- duplicate/ directory exists (not active code)
- Phase 8 is final — general/ domain no longer exists

---

## Details

[Add details here]
