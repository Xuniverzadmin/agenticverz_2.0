# HOC Migration Phase 2 - Step 3: Layer Criteria & Analysis

**Version:** 2.0
**Date:** 2026-01-23
**Status:** ACTIVE
**Purpose:** Machine-checkable criteria for layer fit analysis
**Approach:** Static analysis auditor (two-pass: Signal Detection → Classification)

---

## 1. Layer Model (Corrected)

| Layer | Name | Location Pattern | Core Responsibility |
|-------|------|------------------|---------------------|
| **L2** | APIs | `hoc/api/{audience}/{domain}.py` | HTTP boundary only |
| **L3** | Adapters | `hoc/{audience}/{domain}/facades/*.py` | Translation, cross-domain aggregation |
| **L4** | Engines | `hoc/{audience}/{domain}/engines/*.py` | Authority, business decisions |
| **L5** | Workers | `hoc/{audience}/{domain}/workers/*.py` | Background computation |
| **L6** | Drivers + Schemas | `hoc/{audience}/{domain}/drivers/*.py`, `schemas/*.py` | Data access, data contracts |

**Note:** L3 named "Adapters" (not "Facades") — aligns with cross-domain distribution role.

---

## 2. Signal Detection (Pass 1)

### 2.1 L2 — APIs (HTTP Boundary)

| Signal Type | Pattern | Detection Code |
|-------------|---------|----------------|
| Import | `from fastapi import` | L2_API |
| Import | `APIRouter`, `Request`, `Response`, `HTTPException` | L2_API |
| Import | `JSONResponse`, `BackgroundTasks` | L2_API |
| Decorator | `@router.get`, `@router.post`, `@router.put`, `@router.delete` | L2_API |
| Function | `async def *(request: Request, ...)` | L2_API |
| Return | `return JSONResponse(...)` | L2_API |

### 2.2 L3 — Adapters (Translation + Aggregation)

| Signal Type | Pattern | Detection Code |
|-------------|---------|----------------|
| Class name | `*Adapter`, `*Facade` (in facades/ folder) | L3_ADAPTER |
| Import | From `*/engines/*` (calls L4) | L3_ADAPTER |
| Import | From **multiple domains** | L3_CROSS_DOMAIN |
| No HTTP | Absence of `fastapi`, `Request`, `HTTPException` | L3_ADAPTER |
| No DB | Absence of `select()`, `session.execute()` | L3_ADAPTER |

### 2.3 L4 — Engines (Authority + Business Logic)

| Signal Type | Pattern | Detection Code |
|-------------|---------|----------------|
| Class name | `*Engine`, `*Service` (in engines/ folder) | L4_ENGINE |
| Contains | Business decisions (`if budget >`, `if policy.allows`) | L4_ENGINE |
| Contains | Pattern detection, rule evaluation | L4_ENGINE |
| Import | From `*/drivers/*` (calls L6) | L4_ENGINE |
| Return | Domain objects (dataclass, Pydantic, Verdict) | L4_ENGINE |
| Positive | `Verdict`, `Decision`, `Outcome` objects | L4_ENGINE_GOOD |
| No HTTP | Absence of `fastapi`, `Request`, `JSONResponse` | L4_ENGINE |
| No DB | Absence of `select()`, `session.execute()` | L4_ENGINE |

### 2.4 L5 — Workers (Background Processing)

| Signal Type | Pattern | Detection Code |
|-------------|---------|----------------|
| Class name | `*Worker`, `*Processor`, `*Handler` | L5_WORKER |
| Function | `async def process_*`, `async def compute_*` | L5_WORKER |
| Contains | Batch/heavy computation | L5_WORKER |
| Import | From `*/drivers/*` (calls L6) | L5_WORKER |
| Header | `# Idempotent: YES/NO` | L5_WORKER |

### 2.5 L6 — Drivers (Data Access)

| Signal Type | Pattern | Detection Code |
|-------------|---------|----------------|
| Class name | `*Driver`, `*ReadService`, `*WriteService`, `*Repository` | L6_DRIVER |
| Import | `from sqlalchemy import select, insert, update, delete` | L6_DRIVER |
| Import | `from sqlmodel import Session` | L6_DRIVER |
| Import | `from app.models.*` (ORM models) | L6_DRIVER |
| Contains | `session.execute(...)`, `session.add(...)` | L6_DRIVER |
| Contains | `.scalars()`, `.one()`, `.all()`, `.first()` | L6_DRIVER |
| Contains | `.commit()`, `.flush()`, `.refresh()` | L6_DRIVER |

### 2.6 L6 — Schemas (Data Contracts)

| Signal Type | Pattern | Detection Code |
|-------------|---------|----------------|
| Class | `class X(BaseModel)` (Pydantic) | L6_SCHEMA |
| Decorator | `@dataclass` | L6_SCHEMA |
| Contains | `class X(str, Enum)` | L6_SCHEMA |
| Contains | `Field(...)`, validators | L6_SCHEMA |
| No logic | Pure data shape (no functions beyond validation) | L6_SCHEMA |

---

## 3. Violation Detection (FORBIDDEN Signals)

### 3.1 Authority Leak (L4 doing L2/L6 things)

| Signal | Source Layer | Violation Code |
|--------|--------------|----------------|
| `raise HTTPException` | L4 | AUTHORITY_LEAK_HTTP |
| `return JSONResponse` | L4 | AUTHORITY_LEAK_HTTP |
| `BackgroundTasks` | L4 | AUTHORITY_LEAK_SCHEDULE |
| `@retry`, `tenacity` | L4 (except runtime/) | AUTHORITY_LEAK_RETRY |
| `sleep()`, `asyncio.sleep()` | L4 | TEMPORAL_LEAK |
| `session.execute(select(...))` | L4 | DATA_LEAK |
| `.commit()`, `.flush()` | L4 | DATA_LEAK |

### 3.2 Execution Leak (L3/L5 doing L4 things)

| Signal | Source Layer | Violation Code |
|--------|--------------|----------------|
| `while True:` with retry | L3 | EXECUTION_LEAK |
| `@retry`, `tenacity` | L3, L5 | EXECUTION_LEAK |
| `BackgroundTasks` | L3 | EXECUTION_LEAK |
| Business decisions | L3 | AUTHORITY_LEAK |
| Incident creation | L5 | AUTHORITY_LEAK |
| Policy enforcement | L5 | AUTHORITY_LEAK |

### 3.3 Data Leak (Non-L6 touching ORM)

| Signal | Source Layer | Violation Code |
|--------|--------------|----------------|
| `from sqlalchemy import select` | L2, L3, L4, L5 | DATA_LEAK |
| `session.execute(...)` | L2, L3, L4, L5 | DATA_LEAK |
| `from app.models.*` (direct) | L2, L3 | DATA_LEAK |
| `.scalars()`, `.one()`, `.all()` | L2, L3, L4, L5 | DATA_LEAK |

### 3.4 Temporal Leak

| Signal | Source Layer | Violation Code |
|--------|--------------|----------------|
| `time.sleep()` | L3, L4 | TEMPORAL_LEAK |
| `asyncio.sleep()` | L3, L4 | TEMPORAL_LEAK |
| Backoff logic | L3, L4, L5 | TEMPORAL_LEAK |

---

## 4. Misfit Taxonomy

| Code | Meaning | Severity |
|------|---------|----------|
| **AUTHORITY_LEAK** | L4 doing L2/L6 things | HIGH |
| **EXECUTION_LEAK** | L3/L5 retrying or scheduling | MEDIUM |
| **DATA_LEAK** | Non-L6 touching ORM/DB | HIGH |
| **TEMPORAL_LEAK** | sleep, backoff, timing logic in wrong layer | MEDIUM |
| **DUPLICATION** | Same DTO/enum defined in multiple places | LOW |
| **DRIFT** | Header declares X, behavior is Y | HIGH |
| **SCOPE_CREEP** | Layer does more than allowed | MEDIUM |
| **LAYER_JUMP** | Completely wrong layer | HIGH |

---

## 4.5. Three-Axis Classification Model

Each file is classified on three independent axes:

### Axis A — Structural Fit (detected_layer)
What layer the file *behaves* like based on signal analysis.
- L2/L3/L4/L5/L6 (or multiple)
- Answers: "Where does this file belong if moved as-is?"

### Axis B — Authority Violation Severity
What the file is doing *wrong* (from Section 4 above).
- Answers: "How dangerous is this file if left unchanged?"

### Axis C — Refactor Action (refactor_action)
What kind of change is needed. Every file maps to **exactly one** action.

| Action | Description | Effort |
|--------|-------------|--------|
| **NO_ACTION** | File is correctly placed and classified | NONE |
| **HEADER_FIX_ONLY** | Fix header/metadata only, no code changes | LOW |
| **RECLASSIFY_ONLY** | Move file to correct folder, update header | LOW |
| **QUARANTINE_DUPLICATE** | Move to duplicate/ folder | LOW |
| **EXTRACT_DRIVER** | Extract DB operations to new L6 Driver | MEDIUM |
| **EXTRACT_AUTHORITY** | Move HTTP/decisions to appropriate layer | HIGH |
| **SPLIT_FILE** | Split into multiple single-responsibility files | HIGH |

### Action Determination Rules

```python
# Priority-ordered rules for determining refactor action

if layer_fit and no violations:
    action = NO_ACTION

elif only_drift and folder == dominant:
    action = HEADER_FIX_ONLY  # Just fix the header

elif layer_jump_only and declared == dominant:
    action = RECLASSIFY_ONLY  # Move to correct folder

elif detected_layers == [L6] and declared != L6:
    action = RECLASSIFY_ONLY  # Pure L6 behavior in wrong place

elif DATA_LEAK in violations:
    if L4 in detected and L6 in detected:
        action = EXTRACT_DRIVER  # Mixed behavior needs split
    else:
        action = RECLASSIFY_ONLY  # Pure L6, just move

elif AUTHORITY_LEAK_HTTP in violations:
    action = EXTRACT_AUTHORITY  # L4 doing HTTP things

elif len(detected_layers) >= 3:
    action = SPLIT_FILE  # Too many responsibilities

elif DRIFT in violations:
    action = HEADER_FIX_ONLY  # Default for header mismatches
```

### Recommended Migration Order

Execute in this order for minimal risk and maximum efficiency:

1. **HEADER_FIX_ONLY** → Fast wins, improves signal accuracy
2. **RECLASSIFY_ONLY** → Folder hygiene, zero logic risk
3. **QUARANTINE_DUPLICATE** → Reduces noise, prevents double work
4. **EXTRACT_DRIVER** → Biggest category, needs conventions first
5. **EXTRACT_AUTHORITY** → High risk, requires L4 stability
6. **SPLIT_FILE** → Last, architectural surgery

---

## 5. Whitelist Paths (Excluded)

| Path Pattern | Reason |
|--------------|--------|
| `*/general/L5_utils/*` | Shared utilities |
| `*/general/L5_schemas/*` | Shared schemas |
| `*/__init__.py` | Package markers |
| `*/tests/*` | Test files |
| `*/duplicate/*` | Quarantine folder |

---

## 6. Header Check

**Expected format:**

```python
# Layer: L{X} — {Layer Name}
# AUDIENCE: CUSTOMER | FOUNDER | INTERNAL
# Role: {description}
```

**Validation:**
- Extract declared layer from header
- Compare with detected layer from signals
- If mismatch → DRIFT violation

---

## 7. Output Format

### 7.1 Per-File Analysis (JSON)

```json
{
  "file": "hoc/cus/incidents/L5_engines/incident_read_service.py",
  "header": {
    "declared_layer": "L4",
    "audience": "CUSTOMER"
  },
  "signals": {
    "positive": [
      {"pattern": "class IncidentReadService", "layer": "L4_ENGINE"}
    ],
    "negative": [
      {"pattern": "from sqlalchemy import select", "layer": "L6_DRIVER", "violation": "DATA_LEAK"}
    ]
  },
  "classification": {
    "declared_layer": "L4",
    "detected_layers": {"L4_ENGINE": 1, "L6_DRIVER": 3},
    "dominant_layer": "L6",
    "layer_fit": false
  },
  "misfit": {
    "type": "DRIFT",
    "severity": "HIGH",
    "detail": "Declared L4 Engine but performs L6 Driver operations"
  }
}
```

### 7.2 Summary Report (Markdown)

```markdown
# HOC Layer Fit Analysis Report

| Status | Count | % |
|--------|-------|---|
| LAYER_FIT | 580 | 79% |
| DRIFT | 89 | 12% |
| DATA_LEAK | 42 | 6% |
```

---

## 8. Script Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  PASS 1: SIGNAL DETECTION (layer_analysis.py)               │
│  - Scan imports, classes, decorators                        │
│  - Extract header metadata                                  │
│  - Output: signals_raw.json                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PASS 2: CLASSIFICATION (layer_classifier.py)               │
│  - Apply rules to signals                                   │
│  - Detect violations                                        │
│  - Output: layer_fit_report.json, summary.md                │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/migration/layer_analysis.py` | Pass 1: Signal detection | `signals_raw.json` |
| `scripts/migration/layer_classifier.py` | Pass 2: Classification | `layer_fit_report.json`, `summary.md` |

---

## 10. References

- HOC_LAYER_TOPOLOGY_V1.md - Layer definitions
- PHASE2_MIGRATION_PLAN.md - Migration context
- PIN-467 - Step 1 completion

---

**Document Status:** ACTIVE
**Next Action:** Run layer analysis scripts
