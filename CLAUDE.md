# Claude Context File - AOS / Agenticverz 2.0

**Last Updated:** 2025-12-25

---

## SYSTEM CONTRACTS (GOVERNANCE FRAMEWORK)

**Status:** PHASE 3 COMPLETE - Contracts locked, M0-M27 classified

### Contract-First Development

All future work must align to these four contracts:

| Order | Contract | Question |
|-------|----------|----------|
| 1 | PRE-RUN | What must the system declare before execution starts? |
| 2 | CONSTRAINT | What constraints apply, and how are they enforced? |
| 3 | DECISION | What decisions must be surfaced when the system chooses a path? |
| 4 | OUTCOME | How do we reconcile what happened with what was promised? |

### Contract Gate Rule (MANDATORY)

Before any new scenario or feature:

```
1. Which contract does this exercise?
2. Which obligation does it test?
3. Is this a new obligation or an existing one?
```

If these cannot be answered, the work is rejected.

### No Code Without Contract

> **No code, no UI, no refactor is allowed unless you can name the contract obligation it satisfies.**

### Contract Files

| File | Purpose |
|------|---------|
| `docs/contracts/INDEX.md` | Contract index and status |
| `docs/contracts/PRE_RUN_CONTRACT.md` | Intent declarations |
| `docs/contracts/CONSTRAINT_DECLARATION_CONTRACT.md` | Constraint enforcement |
| `docs/contracts/DECISION_RECORD_CONTRACT.md` | Decision surfacing |
| `docs/contracts/OUTCOME_RECONCILIATION_CONTRACT.md` | Outcome verification |
| `docs/contracts/COVERAGE_MATRIX.md` | Ledger-to-contract mapping |
| `docs/contracts/M0_M27_CLASSIFICATION.md` | Milestone classification |
| `docs/contracts/OBLIGATION_DELTAS.md` | Proposed contract evolutions |

### Phase Status

| Phase | Status |
|-------|--------|
| Phase 1: Scenario Extraction | COMPLETE (13 entries) |
| Phase 2: Contract Drafting | COMPLETE (4 contracts) |
| Phase 3: M0-M27 Mapping | COMPLETE (27 milestones, 2 deltas) |
| Phase 4: Implementation | READY |

### Key Metrics

- 93% of M0-M27 collapsed into existing obligations
- 2 new obligations identified (decision_source, decision_trigger)
- 13 consecutive milestones without new obligation (stabilized)

**Reference:** `docs/contracts/INDEX.md`
**Ledger:** `docs/SYSTEM_TRUTH_LEDGER.md` (13 entries)

---

## Session Start Protocol (MANDATORY)

Before ANY work, run the hygiene check:

```bash
./scripts/ops/session_start.sh
```

This verifies:
- Working environment exists
- No stale checklists
- Services are healthy
- No blocking issues

Then read in order:
1. `agentiverz_mn/repo_snapshot.md` - Current state
2. `agentiverz_mn/milestone_plan.md` - What we're building
3. Pick the relevant checklist for your task

---

## Quick Start for AI Assistants

| Resource | Location | Purpose |
|----------|----------|---------|
| Memory PIN Index | `docs/memory-pins/INDEX.md` | Project status dashboard |
| M8 Working Environment | `agentiverz_mn/` | Focused context files |
| Current Roadmap | `docs/memory-pins/PIN-033-m8-m14-machine-native-realignment.md` | M8-M14 plan |

---

## Project Summary

**AOS (Agentic Operating System)** - The most predictable, reliable, deterministic SDK for building machine-native agents.

### Mission Statement
> AOS is the most predictable, reliable, deterministic SDK for building machine-native agents — with skills, budgets, safety, state management, and observability built-in.

### What "Machine-Native" Means
- Designed for agents to operate efficiently, not humans to babysit
- Queryable execution context (not log parsing)
- Capability contracts (not just tool lists)
- Structured outcomes (never throws exceptions)
- Failure as data (navigable, not opaque)
- Pre-execution simulation
- Resource contracts declared upfront

---

## Current Phase

**M0-M28 Complete → Contract Governance Active**

### Milestone Status

| Milestone | Status |
|-----------|--------|
| M0-M28 | ✅ COMPLETE (94% utilization score) |
| Contract Framework | ✅ COMPLETE (Phase 1-3) |
| Phase 4: Implementation | ⏳ READY |

### Contract-Driven Development

All future work follows the contract framework:
1. Identify which contract the work exercises
2. Verify obligation coverage
3. Propose delta if new obligation needed
4. Implement only after contract alignment

See `docs/contracts/INDEX.md` for contract status.

---

## Tech Stack

- **Backend:** FastAPI + SQLModel + PostgreSQL
- **Worker:** ThreadPoolExecutor with graceful shutdown
- **Observability:** Prometheus + Alertmanager + Grafana
- **Container:** Docker Compose with host networking
- **LLM:** Anthropic Claude (claude-sonnet-4-20250514)
- **Connection Pool:** PgBouncer (port 6432)

---

## Key Directories

```
/root/agenticverz2.0/
├── agentiverz_mn/           # M8+ working environment (START HERE)
│   ├── repo_snapshot.md     # Current state
│   ├── milestone_plan.md    # M8-M14 roadmap
│   ├── auth_blocker_notes.md
│   ├── demo_checklist.md
│   ├── sdk_packaging_checklist.md
│   └── auth_integration_checklist.md
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── api/             # API routers
│   │   ├── auth/            # RBAC (uses stub - needs real auth)
│   │   ├── skills/          # 5 production skills
│   │   ├── worker/runtime/  # Machine-native runtime
│   │   ├── workflow/        # Workflow engine
│   │   └── costsim/         # Cost simulation V2
│   └── cli/aos.py           # CLI tool
├── sdk/
│   ├── python/              # Python SDK (10/10 tests, needs packaging)
│   └── js/                  # JS SDK (needs types, machine-native methods)
├── docs/
│   ├── memory-pins/         # 168+ PINs (project memory)
│   ├── contracts/           # System contracts (governance framework)
│   ├── test_reports/        # Test reports + REGISTER.md
│   └── API_WORKFLOW_GUIDE.md
├── scripts/
│   └── ops/
│       ├── session_start.sh  # Run before each session
│       ├── hygiene_check.sh  # Weekly automated check
│       └── memory_trail.py   # Auto-create PINs & test reports
└── monitoring/
```

---

## Services

| Service | Port | Status |
|---------|------|--------|
| nova_agent_manager | 8000 | Backend API |
| nova_worker | - | Run executor |
| nova_db | 5433 | PostgreSQL |
| nova_pgbouncer | 6432 | Connection pool |
| nova_prometheus | 9090 | Metrics |
| nova_alertmanager | 9093 | Alert routing |
| nova_grafana | 3000 | Dashboards |

---

## Machine-Native APIs (Implemented)

```python
# All implemented and working
POST /api/v1/runtime/simulate      # Plan feasibility check
POST /api/v1/runtime/query         # State queries
GET  /api/v1/runtime/capabilities  # Skills, budget, rate limits
GET  /api/v1/runtime/skills/{id}   # Skill details
POST /api/v1/runs                  # Create run
GET  /api/v1/runs/{id}             # Run status
```

---

## Common Commands

```bash
# Session start (ALWAYS RUN FIRST)
./scripts/ops/session_start.sh

# Weekly hygiene check
./scripts/ops/hygiene_check.sh

# Check services
docker compose ps

# View logs
docker compose logs backend --tail 100

# Check health
curl http://localhost:8000/health

# Check capabilities
curl -H "X-API-Key: $AOS_API_KEY" http://localhost:8000/api/v1/runtime/capabilities

# Run tests
cd backend && PYTHONPATH=. python -m pytest tests/ -v

# Rebuild after changes
docker compose up -d --build backend worker
```

---

## Environment Variables

```bash
# Key variables (in .env)
DATABASE_URL=postgresql://nova:novapass@localhost:6432/nova_aos
REDIS_URL=redis://localhost:6379/0
AOS_API_KEY=edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf
AUTH_SERVICE_URL=http://localhost:8001  # STUB - needs real auth for M8
RBAC_ENABLED=true
RBAC_ENFORCE=true
```

---

## Key Memory PINs

| PIN | Topic | Status |
|-----|-------|--------|
| PIN-170 | System Contract Governance Framework | ACTIVE (Phase 1-3 complete) |
| PIN-167 | Final Review Tasks Phase 1 | COMPLETE (6 scenarios, visibility gaps) |
| PIN-163 | M0-M28 Utilization Report | REFERENCE (94% score) |
| PIN-122 | Master Milestone Compendium M0-M21 | REFERENCE |
| PIN-005 | Machine-Native Architecture | PRIMARY (vision) |
| PIN-120 | Test Suite Stabilization & Prevention | COMPLETE (PREV-1 to PREV-12) |
| PIN-125 | SDK Cross-Language Parity | COMPLETE (PREV-16 to PREV-19) |

---

## Mypy Technical Debt (PIN-121)

**Baseline:** 572 errors in 118 files (known limitation)

### Error Categories
- SQLModel `table=True` keyword (27) - Known limitation, low priority
- None + operator issues (14) - P1, genuine bugs
- Type assignment mismatches (13) - P2, gradual fix
- SQLAlchemy `Base` inheritance (8) - False positive

### Prevention Mechanisms
| ID | Rule | Enforcement |
|----|------|-------------|
| PREV-13 | Mypy pre-commit (warning mode) | `.pre-commit-config.yaml` |
| PREV-14 | CI mypy step (non-blocking) | `.github/workflows/ci.yml` |
| PREV-15 | Postflight mypy category | `postflight.py` |

### Commands
```bash
# Run mypy on changed files
mypy backend/app/ --ignore-missing-imports --show-error-codes

# Skip mypy for commits with known issues
SKIP=mypy git commit -m "message"

# Check postflight mypy category
./scripts/ops/postflight.py --category mypy
```

See PIN-121 for full remediation plan and root cause analysis.

---

## SDK Cross-Language Parity (PIN-125)

**Status:** Python and JS SDKs must produce identical deterministic hashes.

### Hash Algorithm (MUST match in both SDKs)

```
1. base_string = f"{seed}:{timestamp}:{tenant_id}"
2. chain_hash = SHA256(base_string).hexdigest()
3. For each step:
   a. step_payload = canonical_json(deterministic_payload)
   b. step_hash = SHA256(step_payload).hexdigest()
   c. combined = f"{chain_hash}:{step_hash}"  # COLON SEPARATOR
   d. chain_hash = SHA256(combined).hexdigest()
4. root_hash = chain_hash
```

### Prevention Mechanisms
| ID | Rule | Enforcement |
|----|------|-------------|
| PREV-16 | SDK Export Verification | `postflight.py` sdkparity check |
| PREV-17 | Cross-Language Parity Pre-Commit | `postflight.py` sdkparity check |
| PREV-18 | SDK Build Freshness | `preflight.py` + CI workflow |
| PREV-19 | Hash Algorithm Parity Test | CI workflow parity tests |

### Common Issues (Fixed in PIN-125)

1. **Hash Chain Separator**: Must use colon `:` between hashes
   - ❌ `currentHash + stepHash` (wrong)
   - ✅ `${currentHash}:${stepHash}` (correct)

2. **ES Modules vs CommonJS**: JS scripts must use CommonJS
   - ❌ `import fs from "fs"` (wrong in non-module package)
   - ✅ `const fs = require("fs")` (correct)

3. **Missing SDK Exports**: JS dist/ must export all functions
   - Run `npm run build` after any SDK changes

### Commands
```bash
# Build JS SDK (always do this after changes)
cd sdk/js/aos-sdk && npm run build

# Run local parity check
python3 -c "from aos_sdk import Trace, RuntimeContext; ..."  # Generate trace
node sdk/js/aos-sdk/scripts/compare_with_python.js /tmp/trace.json

# Run postflight SDK parity check
./scripts/ops/postflight.py --category sdkparity

# Run preflight SDK build check
./scripts/ops/preflight.py --full
```

See PIN-125 for full root cause analysis and fix details.

---

## Hygiene Scripts

### session_start.sh
Run at the start of every session:
- Checks working environment
- Shows current phase
- Lists blockers
- Verifies services

### hygiene_check.sh
Run weekly (or via cron):
- Detects stale files
- Checks PIN count
- Validates INDEX.md freshness
- Flags completed checklists
- `--fix` mode for auto-cleanup
- `--json` mode for CI

---

## Session Workflow

1. **Start:** `./scripts/ops/session_start.sh`
2. **Read:** `agentiverz_mn/repo_snapshot.md`
3. **Plan:** Check `milestone_plan.md`
4. **Work:** Use relevant checklist
5. **Update:** Mark checklist items complete
6. **End:** Update `repo_snapshot.md` if major changes

---

## Memory Trail Automation (MANDATORY)

After completing any significant job, **ALWAYS** use the memory trail workflow.

### ⚠️ CRITICAL: Find First, Update Existing, Create Only for NEW

**DO NOT** create new PINs for work related to existing topics. Instead:

1. **FIND** existing PINs first
2. **UPDATE** if a related PIN exists
3. **CREATE** only for genuinely NEW topics

```bash
# STEP 1: Always search first
python scripts/ops/memory_trail.py find "ops console"
python scripts/ops/memory_trail.py find 111

# STEP 2: Update existing PIN (PREFERRED)
python scripts/ops/memory_trail.py update 111 \
    --section "Updates" \
    --content "Added customers panel with sort controls..."

# STEP 3: Only create NEW PIN if no related PIN exists
python scripts/ops/memory_trail.py pin \
    --title "Completely New Feature" \
    --category "Category" \
    --summary "Description"
```

### When to Update vs Create

| Situation | Action | Example |
|-----------|--------|---------|
| Adding panel to existing console | **UPDATE** existing console PIN | Update PIN-111 |
| Bug fix in existing feature | **UPDATE** that feature's PIN | Update PIN-XXX |
| Enhancement to existing feature | **UPDATE** that feature's PIN | Update PIN-XXX |
| Brand new feature/system | **CREATE** new PIN | Create new |
| New milestone (M25, M26...) | **CREATE** new PIN | Create new |
| Test run completed | **CREATE** Test Report | TR-XXX |

### Find Existing PINs

```bash
# Search by keyword
python scripts/ops/memory_trail.py find "ops console"
python scripts/ops/memory_trail.py find "stickiness"

# Search by PIN number
python scripts/ops/memory_trail.py find 111

# Output shows matching PINs with titles and paths
```

### Update Existing PIN (PREFERRED)

```bash
python scripts/ops/memory_trail.py update 111 \
    --section "Updates" \
    --content "## 2025-12-20: Added Customers Panel

- Added CustomersPanel component
- Changed layout to 2x2 grid
- Wired /ops/customers endpoint"

# Optionally update status
python scripts/ops/memory_trail.py update 111 \
    --section "Updates" \
    --content "..." \
    --status "ENHANCED"
```

### Create New PIN (Only for NEW Topics)

```bash
# Basic usage
python scripts/ops/memory_trail.py pin \
    --title "Feature Name" \
    --category "Category / Subcategory" \
    --status "COMPLETE" \
    --summary "Brief description of what was done" \
    --content "Detailed markdown content"

# With milestone and related PINs
python scripts/ops/memory_trail.py pin \
    --title "M24 Feature" \
    --category "Ops Console / Feature" \
    --milestone "M24 Phase-2" \
    --status "COMPLETE" \
    --summary "Summary here" \
    --related 110 111 \
    --commits "abc123" "def456"

# From file (for complex content)
python scripts/ops/memory_trail.py pin \
    --title "Big Feature" \
    --category "Architecture" \
    --from-file /tmp/pin_content.md
```

### Create a Test Report

```bash
python scripts/ops/memory_trail.py report \
    --title "Test Name" \
    --type "Integration" \
    --status "PASS" \
    --run-id "uuid-here" \
    --tokens 5000 \
    --findings "Key findings summary"

# With gaps identified
python scripts/ops/memory_trail.py report \
    --title "Adversarial Test" \
    --type "Adversarial" \
    --status "GAPS" \
    --gaps "Issue 1" "Issue 2"
```

### Check Next Available IDs

```bash
python scripts/ops/memory_trail.py next
# Output:
# 📌 Next PIN number: PIN-113
# 📋 Next Test Report number: TR-006
```

### What Gets Updated Automatically

1. **PIN Creation:**
   - Creates `docs/memory-pins/PIN-XXX-title.md`
   - Updates `docs/memory-pins/INDEX.md` (Last Updated, Active PINs table, Changelog)

2. **Test Report Creation:**
   - Creates `docs/test_reports/TR-XXX_TITLE_DATE.md`
   - Updates `docs/test_reports/REGISTER.md` (Test Report Index, Changelog)

### Categories Reference

| Category | When to Use |
|----------|-------------|
| `Ops Console / Feature` | Ops console features |
| `Frontend / UI` | UI components |
| `Infrastructure / Automation` | Systemd, cron, schedulers |
| `Milestone / Completion` | Major milestone completion |
| `Bug Fix / Feature` | Bug fixes |
| `Testing / Verification` | Test infrastructure |
| `Developer Tooling / CI` | Dev tools, CI/CD |

---

## Notes

- Host networking required (systemd-resolved + Tailscale)
- Backend publicly accessible on 0.0.0.0:8000
- Auth currently uses STUB - must wire real provider before beta
- PgBouncer on 6432, not direct Postgres on 5433
- All sensitive tokens in `.env` (not committed)
