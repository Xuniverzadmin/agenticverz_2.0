# P1.1-2.1 Legacy Artifact Classification

**Generated:** 2026-01-06
**Phase:** Phase 1.1 - Legacy Resolution & Structural Hardening
**Reference:** PIN-317

---

## Classification Framework

| Classification | Meaning | Action |
|----------------|---------|--------|
| **DELETE** | No architectural value, no future intent | Remove from codebase |
| **QUARANTINE** | Historically meaningful, not active | Isolate with deprecation marker |
| **RETAIN** | Architecturally valid, wrong namespace | Keep, migrate to `/fops/*` |

**Constraint:** No default retention. Every decision requires explicit justification.

---

## Key Insight

> **"Legacy" in Phase 1.1 does NOT mean deprecated.**
> It means: founder-only pages/APIs mounted at wrong namespace (not under `/fops/*`).

Most founder tools are architecturally valid and actively used by founders.
The problem is discoverability by customers, not the code itself.

---

## Frontend Page Classifications

### Ops Console (`pages/ops/`)

| Page | Classification | Reason |
|------|----------------|--------|
| OpsConsoleEntry | **RETAIN** | Active founder tool, entry point for ops dashboard |
| FounderOpsConsole | **RETAIN** | Active founder tool, internal component |
| FounderPulsePage | **RETAIN** | Active founder tool, system health visibility |

**Migration:** `/ops/*` → `/fops/ops/*`

---

### Traces (`pages/traces/`)

| Page | Classification | Reason |
|------|----------------|--------|
| TracesPage | **RETAIN** | Active founder tool, execution trace listing |
| TraceDetailPage | **RETAIN** | Active founder tool, trace inspection |

**Migration:** `/traces/*` → `/fops/traces/*`

---

### Workers (`pages/workers/`)

| Page | Classification | Reason |
|------|----------------|--------|
| WorkerStudioHomePage | **RETAIN** | Active founder tool, worker management |
| WorkerExecutionConsolePage | **RETAIN** | Active founder tool, worker execution control |

**Migration:** `/workers/*` → `/fops/workers/*`

---

### Recovery (`pages/recovery/`)

| Page | Classification | Reason |
|------|----------------|--------|
| RecoveryPage | **RETAIN** | Active founder tool, recovery candidate management |

**Migration:** `/recovery` → `/fops/recovery`

---

### SBA Inspector (`pages/sba/`)

| Page | Classification | Reason |
|------|----------------|--------|
| SBAInspectorPage | **RETAIN** | Active founder tool, multi-agent inspection |

**Migration:** `/sba` → `/fops/sba`

---

### Integration (`pages/integration/`)

| Page | Classification | Reason |
|------|----------------|--------|
| IntegrationDashboard | **RETAIN** | Active founder tool, learning pipeline visibility |
| LoopStatusPage | **RETAIN** | Active founder tool, loop status inspection |

**Migration:** `/integration/*` → `/fops/integration/*`

---

### Founder Tools (`pages/fdr/`)

| Page | Classification | Reason |
|------|----------------|--------|
| FounderTimelinePage | **RETAIN** | Active founder tool, decision timeline |
| FounderControlsPage | **RETAIN** | Active founder tool, kill-switch controls |
| ReplayIndexPage | **RETAIN** | Active founder tool, replay index |
| ReplaySliceViewer | **RETAIN** | Active founder tool, replay slice inspection |
| ScenarioBuilderPage | **RETAIN** | Active founder tool, cost simulation |
| FounderExplorerPage | **RETAIN** | Active founder tool, cross-tenant explorer |

**Migration:** `/fdr/*` → `/fops/fdr/*`

---

### Credits (`pages/credits/`)

| Page | Classification | Reason |
|------|----------------|--------|
| CreditsPage | **RETAIN** (Decision Required) | Billing visibility - unclear if founder-only or customer |

**Decision Required:** Is billing a customer feature (`/guard/billing`) or founder-only (`/fops/billing`)?

**Default:** RETAIN as founder-only until decision made.

---

### Speculative Code

| Page | Classification | Reason |
|------|----------------|--------|
| SupportPage | **QUARANTINE** | Imported but no route defined, unclear intent |

**Action:** Move to `/quarantine/` directory with deprecation marker.

---

## Backend API Classifications

### Ops Console APIs

| File | Classification | Reason |
|------|----------------|--------|
| `ops.py` | **RETAIN** | Active founder API, ops pulse/infra/customers |
| `cost_ops.py` | **RETAIN** | Active founder API, cost operations |
| `founder_actions.py` | **RETAIN** | Active founder API, founder control actions |

**Migration:** `/ops/*` → `/fops/ops/*` (with RBAC enforcement)

---

### Founder Tools APIs

| File | Classification | Reason |
|------|----------------|--------|
| `founder_timeline.py` | **RETAIN** | Active founder API, decision timeline |
| `founder_explorer.py` | **RETAIN** | Active founder API, cross-tenant explorer |
| `founder_review.py` | **QUARANTINE** | Mounted but not called by any frontend page |

**Evidence for founder_review.py QUARANTINE:**
- API is mounted (fixed in Phase 1)
- No frontend page calls `/fdr/contracts/*` endpoints
- May be future functionality or dead code
- Safe to quarantine until usage confirmed

**Migration (retained):** `/fdr/*` → `/fops/fdr/*`

---

### Execution & Replay APIs

| File | Classification | Reason |
|------|----------------|--------|
| `replay.py` | **RETAIN** | Active founder API, replay data |
| `traces.py` | **RETAIN** | Active founder API, trace listing/detail |
| `scenarios.py` | **RETAIN** | Active founder API, cost simulation |

**Migration:**
- `/replay/*` → `/fops/replay/*`
- `/traces/*` → `/fops/traces/*`
- `/scenarios/*` → `/fops/scenarios/*`

---

### Integration APIs

| File | Classification | Reason |
|------|----------------|--------|
| `integration.py` | **RETAIN** | Active founder API, learning pipeline |

**Migration:** `/integration/*` → `/fops/integration/*`

---

## Classification Summary

### Frontend Pages

| Classification | Count | Pages |
|----------------|-------|-------|
| **RETAIN** | 17 | All active founder pages |
| **QUARANTINE** | 1 | SupportPage |
| **DELETE** | 0 | - |

### Backend APIs

| Classification | Count | Files |
|----------------|-------|-------|
| **RETAIN** | 9 | All active founder APIs |
| **QUARANTINE** | 1 | founder_review.py |
| **DELETE** | 0 | - |

---

## Quarantine Actions (P1.1-2.2)

### 1. SupportPage (Frontend)

**Current Location:** `website/app-shell/src/products/ai-console/account/SupportPage.tsx`

**Action:**
```
1. Create quarantine directory: website/app-shell/src/quarantine/
2. Move SupportPage.tsx to quarantine/
3. Add QUARANTINE.md marker explaining status
4. Remove import from AIConsoleApp.tsx (already no route)
```

### 2. founder_review.py (Backend)

**Current Location:** `backend/app/api/founder_review.py`

**Action:**
```
1. Create quarantine directory: backend/app/quarantine/
2. Move founder_review.py to quarantine/
3. Remove router registration from main.py
4. Add QUARANTINE.md marker explaining status
```

---

## Namespace Migration Plan (P1.1-3.1)

All RETAIN items require namespace migration in Phase 1.1-3:

### Frontend Routes

| Current | Target |
|---------|--------|
| `/ops/*` | `/fops/ops/*` |
| `/traces/*` | `/fops/traces/*` |
| `/workers/*` | `/fops/workers/*` |
| `/recovery` | `/fops/recovery` |
| `/sba` | `/fops/sba` |
| `/integration/*` | `/fops/integration/*` |
| `/fdr/*` | `/fops/fdr/*` |

### Backend API Prefixes

| Current | Target |
|---------|--------|
| `/ops/*` | `/fops/ops/*` |
| `/explorer` | `/fops/explorer` |
| `/fdr/*` | `/fops/fdr/*` |
| `/replay` | `/fops/replay` |
| `/scenarios` | `/fops/scenarios` |
| `/traces` | `/fops/traces` |
| `/integration` | `/fops/integration` |

---

## Human Decisions Required

| Item | Question | Default | Impact |
|------|----------|---------|--------|
| CreditsPage | Customer or Founder? | Founder | Route namespace |
| founder_review.py | Future feature or dead? | Quarantine | Keep or delete |
| SupportPage | Add route or remove? | Quarantine | Keep or delete |

---

## Acceptance Criteria

- [x] Every legacy artifact classified
- [x] Every classification has explicit reason
- [x] No default retention applied
- [x] Quarantine items identified with actions
- [x] Migration plan outlined for RETAIN items
- [x] Human decisions surfaced (not assumed)

---

## Next Steps (P1.1-2.2)

Execute quarantine for:
1. SupportPage (frontend)
2. founder_review.py (backend)

Then proceed to P1.1-3.1 for founder console boundary isolation.
