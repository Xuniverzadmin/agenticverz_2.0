# AURORA_L2 — Authoritative UI Intent Pipeline

**Status:** LOCKED
**Version:** 1.0
**Created:** 2026-01-10
**Supersedes:** L2.1 CSV-based UI intent pipeline
**Scope:** UI intent → semantics → backend binding → projection → rendering

---

## 1. Purpose

AURORA_L2 is the **authoritative, deterministic pipeline** for translating
human intent into UI behavior **without inference, heuristics, or silent drift**.

It replaces the legacy L2.1 pipeline which relied on:
- CSV as source of truth
- Implicit semantics
- Multi-step intermediate artifacts
- UI-side inference

AURORA_L2 enforces:
- Explicit intent
- Governed semantics
- Backend binding visibility
- Projection-driven UI

---

## 2. Core Principles (Non-Negotiable)

1. **One source of truth per layer**
2. **Intent is declarative, never executable**
3. **Semantics are explicit and finite**
4. **Backend capability gaps must surface before UI**
5. **UI renders projections, not intent**
6. **Compiler is deterministic (zero AI)**

Any system violating these principles is **invalid**.

---

## 3. Migration Governance Statement (LOCKED)

> **During migration, correctness is enforced at the projection layer; intent specs remain mechanically migrated and UNREVIEWED until explicitly revised.**

### Migration Constraints (NON-NEGOTIABLE)

| Constraint | Enforcement |
|------------|-------------|
| Do NOT modify `AURORA_L2_INTENT_*.yaml` files | BLOCKING |
| Treat `migration_status=UNREVIEWED` as structurally valid but semantically weak | MANDATORY |
| Compensating logic ONLY in Projection Builder and UI Renderer | BLOCKING |
| Projection rules must be deterministic, reversible, overridable | MANDATORY |
| No inferred semantics may be written back to intent YAMLs or SQL | BLOCKING |

---

## 4. Pipeline Overview

```
Human Intent (Natural Language)
        ↓
AURORA_L2_INTENT_SPEC (YAML, registry-gated)
        ↓
AURORA_L2_COMPILER (deterministic Python)
        ↓
AURORA_L2_UI_INTENT_STORE (SQL)
        ↓
AURORA_L2_PROJECTION_BUILDER (shock absorber)
        ↓
AURORA_L2_UI_RENDERER
```

---

## 5. Authoritative Artifacts & File Map

### 5.1 Intent Governance

```
design/l2_1/
├─ AURORA_L2_INTENT_REGISTRY.yaml       # Allow-list gate
└─ intents/
   └─ *.yaml                            # 54 intent specs
```

**Responsibilities:**
- Declare panels, orders, info, controls, actions
- Declare semantics (verb / object / effect)
- Declare topology (order, section, role, expansion)

**Must NOT:**
- Define UI widgets
- Define backend APIs
- Infer behavior

### 5.2 Semantic & Topology Registries

```
design/l2_1/
├─ AURORA_L2_SEMANTIC_REGISTRY.yaml
└─ AURORA_L2_EXPANSION_MODE_REGISTRY.yaml
```

**Semantic Registry (Closed Vocabulary):**

| Category | Values |
|----------|--------|
| Verbs | VIEW, APPROVE, EXPORT, REJECT, DEACTIVATE, ACKNOWLEDGE, RESOLVE, FILTER, SORT, NAVIGATE, DOWNLOAD |
| Objects | POLICY, POLICY_RULE, POLICY_PROPOSAL, INCIDENT, RUN, TRACE, AUDIT_LOG |
| Effects | STATE_CHANGE, FILE_DOWNLOAD, CONTEXT_SWITCH, NAVIGATION, SELECTION |

**Expansion Modes (Closed Enum):**
- INLINE
- COLLAPSIBLE
- CONTEXTUAL
- OVERLAY
- NAVIGATE

---

## 6. AURORA_L2 Compiler

### 6.1 Entry Point

```
backend/aurora_l2/compiler.py
```

**This is the ONLY writer to the UI intent store.**

### 6.2 Compiler Responsibilities (Strict Order)

1. Load intent registry
2. Load intent YAMLs
3. Validate schemas
4. Validate semantics (against registry)
5. Normalize identifiers
6. Classify interactions (INFO / CONTROL / ACTION / NAV)
7. Build topology (order / section / expansion)
8. Check backend capability bindings
9. Emit SQL transactionally
10. Emit compile report

**No partial writes. Any failure aborts.**

### 6.3 Compiler Schemas

```
backend/aurora_l2/schema/
├─ intent_spec_schema.json
└─ compiled_intent_schema.json
```

---

## 7. UI Intent Store (Machine Truth)

```
design/l2_1/exports/
├─ intent_store_seed.sql
└─ intent_store_compiled.json
```

**Canonical Tables:**
- `aurora_l2_intent_store` (main table)

**Rules:**
- Write-only via compiler
- Read-only for all consumers
- Never manually edited

---

## 8. Backend Capability Registry

```
backend/AURORA_L2_CAPABILITY_REGISTRY/
├─ capability_map.yaml
├─ capability_definitions.yaml
└─ permission_requirements.yaml
```

**Each capability declares:**
- capability_id
- implementation status
- auth requirements
- side effects

**Invariant:**
> No ACTION is executable without a declared capability.

---

## 9. Binding Gate (Safety Layer)

Binding status is determined during compilation:

| Status | Meaning |
|--------|---------|
| BOUND | Backend capability exists and is wired |
| DRAFT | Capability declared but not implemented |
| UNBOUND | No capability declared |

**Rule:**
> No ACTION may reach UI without an explicit binding_status.

---

## 10. Projection Layer (Shock Absorber)

### 10.1 Projection Builder

```
frontend/aurora_l2/projection_builder.ts
```

**Consumes:** `aurora_l2_intent_store`

**Produces:** `AURORA_L2_UI_PROJECTION_LOCK.json`

**Allowed Compensating Logic:**

| Action | Allowed |
|--------|---------|
| Group multiple orders into one panel | ✅ |
| Default expansion modes | ✅ |
| Hide low-signal controls | ✅ |
| Downgrade ACTION → INFO if UNBOUND | ✅ |
| Collapse noisy sections | ✅ |
| Apply visual hierarchy heuristics | ✅ |

**All projection rules must be:**
- Deterministic (same input → same output)
- Reversible (can be overridden by reviewed intent)
- Overridable (future review can change behavior)

### 10.2 Projection Rules

```
frontend/aurora_l2/
├─ projection_rules.ts
├─ projection_builder.ts
└─ PROJECTION_RULES.md
```

---

## 11. UI Rendering

### 11.1 Renderer Entry

```
website/app-shell/src/components/panels/PanelContentRegistry.tsx
```

**Consumes:** `AURORA_L2_UI_PROJECTION_LOCK.json`

**Must NOT:**
- Read intent YAML
- Read SQL directly
- Infer semantics
- Guess backend wiring

### 11.2 Renderer Behavior

**Allowed:**

| Action | Allowed |
|--------|---------|
| Choose dialog vs inline | ✅ |
| Choose primary vs secondary CTA | ✅ |
| Add affordances ("Coming soon", "Not wired") | ✅ |

**Forbidden:**

| Action | Forbidden |
|--------|-----------|
| Invent new actions | ❌ |
| Hide binding gaps silently | ❌ |

---

## 12. Derived Exports (Non-Authoritative)

```
design/l2_1/exports/
├─ intent_store_seed.sql
├─ intent_store_compiled.json
└─ AURORA_L2_COMPILE_REPORT.json
```

Used for:
- Human review
- LLM inspection
- Debugging

**Never treated as source of truth.**

---

## 13. Deprecation Policy (Legacy L2.1)

The following are deprecated and frozen:

```
scripts/tools/l2_pipeline.py
scripts/tools/l2_cap_expander.py
scripts/tools/l2_raw_intent_parser.py
scripts/tools/intent_normalizer.py
scripts/tools/surface_to_slot_resolver.py
scripts/tools/intent_compiler.py
scripts/tools/ui_projection_builder.py
design/l2_1/ui_contract/ui_intent_ir_raw.json
design/l2_1/ui_contract/ui_intent_ir_normalized.json
design/l2_1/ui_contract/ui_intent_ir_slotted.json
design/l2_1/ui_contract/ui_intent_ir_compiled.json
design/l2_1/supertable/L2_1_UI_INTENT_SUPERTABLE.csv
design/l2_1/supertable/l2_supertable_manifest.json
design/l2_1/supertable/l2_supertable_v*_cap_expanded.xlsx
```

They may be deleted **only after** AURORA_L2 validation passes.

---

## 14. Migration Rules

- Migration occurs on branch: `aurora-l2-migration`
- Existing CSV intents are mechanically migrated to YAML
- Migrated intents are marked `UNREVIEWED`
- No semantic enrichment during migration

### Accepted Debt (Explicit)

| Debt | Status |
|------|--------|
| Some panels will be ugly initially | ACCEPTED |
| Some semantics will be shallow | ACCEPTED |
| Some actions will be disabled or hidden | ACCEPTED |

### Rejected Risks

| Risk | Status |
|------|--------|
| Silent behavior changes | REJECTED |
| Backend/UI mismatch | REJECTED |
| Loss of traceability | REJECTED |

---

## 15. Review Protocol

When reviewing individual intents:

1. Change `migration_status: UNREVIEWED` → `REVIEWED`
2. Add `reviewed_by: <name>`
3. Add `reviewed_at: <date>`
4. Optionally refine semantics, controls, expansion modes

Reviewed intents override projection compensation rules.

---

## 16. Final Invariant (Authoritative)

> **If a UI behavior cannot be traced through AURORA_L2 artifacts, it is invalid by definition.**

AURORA_L2 is the only sanctioned UI intent pipeline.

---

## 17. Current Status

| Component | Location | Status |
|-----------|----------|--------|
| Intent Registry | `design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml` | ✅ POPULATED (54 intents) |
| Intent Specs | `design/l2_1/intents/*.yaml` | ✅ 54 files, UNREVIEWED |
| Semantic Registry | `design/l2_1/AURORA_L2_SEMANTIC_REGISTRY.yaml` | ✅ LOCKED (14 verbs, 14 objects, 7 effects) |
| Expansion Modes | `design/l2_1/AURORA_L2_EXPANSION_MODE_REGISTRY.yaml` | ✅ LOCKED (5 modes) |
| JSON Schemas | `backend/aurora_l2/schema/` | ✅ COMPLETE |
| Compiler | `backend/aurora_l2/compiler.py` | ✅ COMPLETE |
| SQL Exports | `design/l2_1/exports/` | ✅ COMPLETE |
| Capability Registry | `backend/AURORA_L2_CAPABILITY_REGISTRY/` | ⏳ PLACEHOLDER |
| Projection Builder | `frontend/aurora_l2/projection_builder.ts` | ✅ COMPLETE |
| Projection Rules | `frontend/aurora_l2/projection_rules.ts` | ✅ COMPLETE |
