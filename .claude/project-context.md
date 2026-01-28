# Agenticverz 2.0 — Project Context

## Vision
Build the most predictable, reliable, deterministic AI console application
that helps AI users track, monitor, and troubleshoot agentic LLM runs.

## Mission
AOS (Agentic Operating System) provides machine-native observability:
- Queryable execution context (not log parsing)
- Capability contracts (not just tool lists)
- Structured outcomes (never throws exceptions)
- Failure as data (navigable, not opaque)
- Pre-execution simulation
- Resource contracts declared upfront

## Product
- **Customer Console:** console.agenticverz.com — single-tenant, 5 frozen domains
  (Overview, Activity, Incidents, Policies, Logs)
- **Preflight Console:** preflight-console.agenticverz.com — pre-prod validation
- **SDK:** Python + JS SDKs for agent builders
- **Backend:** FastAPI + SQLModel + Neon PostgreSQL

## Current Phase
- Phase Family: G (Steady State Governance)
- Architecture: HOC (House of Cards) — 7-layer topology, ratified v1.2.0
- SDSR Pipeline: AURORA L2 (capability observation → UI projection)

## Project Status
- HOC Migration: 472 files across 10 domains
  - Complete: logs, analytics, account, activity
  - Missing L1: policies, general, integrations, incidents, api_keys, overview
  - L2.1 Facades: to be built
- SDSR: Scenarios inject causes → engines create effects → UI reveals truth
- Auth: Clerk JWT (human plane) + X-AOS-Key (machine plane), gateway middleware

## Development Status
- Backend: FastAPI on port 8000 (uvicorn), worker pool (manual restart)
- Frontend: Vite app-shell, Apache serves dist/
- Database: Neon PostgreSQL (authoritative), local Postgres (staging only)
- Monitoring: Prometheus + Grafana + Alertmanager

## Key References (read on demand, not bulk-loaded)
- Architecture: docs/architecture/hoc/INDEX.md
- Layer Inventory: docs/architecture/hoc/HOC_LAYER_INVENTORY.csv
- Memory PINs: docs/memory-pins/INDEX.md (467+ PINs)
- Governance: docs/governance/ (73 files)
- Contracts: docs/contracts/INDEX.md
- Session Playbook: docs/playbooks/SESSION_PLAYBOOK.yaml

## Governance Model
- Rules auto-load from .claude/rules/ (path-scoped)
- Hooks enforce deterministically via .claude/settings.json
- Session health checked by scripts/ops/session_start.sh (12 steps)
- BLCA: scripts/ops/layer_validator.py --backend --ci (0 violations required)
- Contract scan: scripts/preflight/agen_internal_system_scan.py (cron every 30min)
- Bloat audit: scripts/ops/system_bloat_audit.sh (weekly cron + session check)
