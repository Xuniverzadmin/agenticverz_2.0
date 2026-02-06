# project_aware_agenticverz2.md

## Purpose
This file is a lightweight project memory guide for the agent. It defines:
- Where to read project context
- How to load and maintain working memory
- What “state” should be tracked across tasks

## Standard Invocation Prompt (Copy/Paste)
Use this to explicitly load context before tasks:

```
Load project context and follow governance: codex_agents_agenticverz2.md, project_aware_agenticverz2.md, vision_mission_self_audit.md. When needed, consult docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md, docs/architecture/architecture_core/LAYER_MODEL.md, and docs/architecture/architecture_core/DRIVER_ENGINE_PATTERN_LOCKED.md. For domain work, read literature/hoc_domain/<domain>/SOFTWARE_BIBLE.md and DOMAIN_CAPABILITY.md. Task: <your task>
```

## Load Order (When Starting a Task)
1. `codex_agents_agenticverz2.md` (governance + architecture)
2. `docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md` (binding topology)
3. `docs/architecture/architecture_core/LAYER_MODEL.md`
4. `docs/architecture/architecture_core/DRIVER_ENGINE_PATTERN_LOCKED.md`
5. `docs/architecture/hoc/INDEX.md` (HOC domain index)

## Working Memory Checklist
Track this context per task:
- Task goal and scope
- Target directories (e.g., `backend/app/hoc/cus`, `backend/app/hoc/api`)
- Entry points involved (`backend/app/main.py`, `backend/app/hoc/api/int/agent/main.py`)
- Relevant governance constraints (L2->L4->L5->L6, no L3)
- Known wiring gaps or missing imports

## Operational Mode (Default)
- Codex role: Auditor and advisor (governance, architecture, audits, wiring, risk).
- Claude role: Primary coding and implementation.

## Updating Project Memory
When a new finding is discovered, prefer Memory Trail:
- Use `scripts/ops/memory_trail.py` to append findings
- Store references to memory pins and audit artifacts
- Keep this file minimal; do not bulk up Session Notes

## Session Notes
- Use memory trail instead of expanding this section.

## Memory Trail & Pins
- Memory trail script: `scripts/ops/memory_trail.py`
- Memory pins (canonical, single location): `docs/memory-pins/`
- Index: `docs/memory-pins/INDEX.md`
- Use pins to persist session state and link artifacts.

## Memory Pins Reference (Where to Find What)
- Project status, milestones, and architecture anchors: `docs/memory-pins/INDEX.md`
- Domain consolidation, topology, and governance decisions: `docs/memory-pins/PIN-4xx` through `PIN-5xx` (see index)
- Operational tools and automation (memory trail, CI guards): `docs/memory-pins/PIN-108`, `PIN-109`, `PIN-113`
- All memory pins are consolidated under `docs/memory-pins/`
- HOC API wiring migration (canonical): `docs/memory-pins/PIN-526-hoc-api-wiring-migration.md`
- HOC API canonical literature: `backend/app/hoc/api/hoc_api_canonical_literature.md`

## Literature Reference (Canonical Domain Docs)
- Index: `literature/INDEX.md`
- HOC domain literature index: `literature/hoc_domain/INDEX.md`
- Per-domain canonical docs:
- `literature/hoc_domain/overview/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/activity/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/incidents/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/policies/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/controls/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/logs/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/analytics/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/integrations/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/apis/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/api_keys/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/account/SOFTWARE_BIBLE.md`
- HOC spine literature: `literature/hoc_spine/HOC_SPINE_CONSTITUTION.md`

## Canonical Literature Files (domain*_canonical*)
- `literature/hoc_domain/overview/OVERVIEW_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/activity/ACTIVITY_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/incidents/INCIDENT_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/incidents/CANONICAL_REGISTRY.md`
- `literature/hoc_domain/policies/POLICIES_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/controls/CONTROLS_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/logs/LOGS_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/analytics/ANALYTICS_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/integrations/INTEGRATIONS_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/api_keys/API_KEYS_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/account/ACCOUNT_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/ops/OPS_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/platform/PLATFORM_CANONICAL_SOFTWARE_LITERATURE.md`

## Coherence Plan
- Global plan: `docs/COHERENCE_GLOBAL_PLAN.md`

## When to Ask for Confirmation
Ask before:
- Deleting or moving files
- Rewiring routers or changing entrypoints
- Changing layer responsibilities
- Renaming engine/driver patterns

## Quick Location Guide
- HOC topology: `docs/architecture/topology/`
- Layer rules: `docs/architecture/architecture_core/`
- HOC audits: `docs/architecture/hoc/`
- HOC runtime/API: `backend/app/hoc/`
 - CUS L2 → hoc_spine coverage report: `docs/architecture/hoc/CUS_HOC_SPINE_COMPONENT_COVERAGE.md`
 - CUS hoc_spine import matrix (L5/L6/L5_schemas): `docs/architecture/hoc/HOC_SPINE_IMPORT_MATRIX_CUS.md`

## Canonical CUS Domains (Do Not Miss)
overview, activity, incidents, policies, controls, logs, analytics, integrations, api_keys, account
