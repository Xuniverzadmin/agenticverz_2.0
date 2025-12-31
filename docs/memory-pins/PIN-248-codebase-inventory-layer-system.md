# PIN-248: Codebase Inventory & Layer Classification System

**Status:** ACTIVE
**Created:** 2025-12-30
**Category:** Architecture / Governance
**Milestone:** Post-M28 (Operational Maturity)

---

## Summary

Established a complete codebase inventory system that maps every file to the L1-L8 layer model. This enables predictable debugging, safe refactoring, and governance enforcement.

---

## Problem Statement

Before this work:
- 96.9% of files (783/808) lacked layer headers
- 183 files were classified as UNKNOWN
- Debugging was guesswork — no clear ownership
- Refactoring risked destroying intent
- No way to verify architectural boundaries

---

## Solution: Layer-Based Inventory System

### The Layer Model (L1-L8)

| Layer | Name | Description | Import Rules |
|-------|------|-------------|--------------|
| L1 | Product Experience | UI pages, components, hooks | → L2 only |
| L2 | Product APIs | REST endpoints, surface contracts | → L3, L4, L6 |
| L3 | Boundary Adapters | LLM adapters, external integrations | → L4, L6 |
| L4 | Domain Engines | Policy, workflow, skills, agents | → L5, L6 |
| L5 | Execution & Workers | Jobs, tasks, runtime | → L6 only |
| L6 | Platform Substrate | DB, auth, models, utils, SDK | → None |
| L7 | Ops & Deployment | Docs, scripts, config, monitoring | → L6 |
| L8 | Catalyst / Meta | Tests, validators, CI | → Any |

### File Header Format

Every classified code file has a standard header:

```python
# Layer: L{x} — {Layer Name}
# Product: {product | system-wide}
# Temporal:
#   Trigger: {user|api|worker|scheduler|external}
#   Execution: {sync|async|deferred}
# Role: {single-line responsibility}
# Callers: {who calls this?}
# Allowed Imports: L{x}, L{y}
# Forbidden Imports: L{z}
# Reference: {PIN or system}
```

### Non-Executable Artifact Classes

Not all files are executable code. The system classifies all artifacts:

| Class | Description | Layer Inference |
|-------|-------------|-----------------|
| CODE | Executable code with imports (.py, .ts, .js, .sh) | From path or header |
| TEST | Test files (executable but categorized separately) | L8 |
| DATA | Static data files (.json in /data/, etc) | L4/L6 based on path |
| STYLE | Stylesheets (.css, .scss) | L1 |
| CONFIG | Configuration files (.yaml, .ini, .toml) | L7 |
| DOC | Documentation (.md) | L7 |

**Principle:** Nothing escapes the system. Not everything executes.

**Invariant:** UNKNOWN = 0 at all times. Every artifact has both a class AND a layer.

---

## Final Inventory (1,445 files)

### Layer Distribution

| Layer | Count | % | Description |
|-------|------:|---|-------------|
| L7 | 750 | 52.0% | Docs, scripts, config |
| L8 | 192 | 13.3% | Tests |
| L4 | 154 | 10.7% | Domain engines |
| L6 | 123 | 8.5% | Platform substrate |
| L1 | 106 | 7.4% | Frontend |
| L2 | 60 | 4.2% | APIs |
| L5 | 29 | 2.0% | Workers |
| L3 | 25 | 1.7% | Adapters |
| UNKNOWN | 0 | 0.0% | Must be zero |

### Directory Mapping

| Directory | Files | Primary Layers |
|-----------|------:|----------------|
| `backend/` | 523 | L4, L8, L6 |
| `docs/` | 538 | L7 |
| `scripts/` | 180 | L7, L8 |
| `website/` | 137 | L1, L2 |
| `monitoring/` | 33 | L7 |
| `sdk/` | 29 | L6 |
| `config/` | 1 | L7 |

### Confidence Distribution

| Confidence | Count | Meaning |
|------------|------:|---------|
| HIGH | 210 | Explicit header declaration |
| MEDIUM | 1,209 | Path-inferred classification |
| LOW | 22 | Weak inference |

---

## Research Pass Results

Added 186 explicit headers across 5 batches:

| Batch | Files | Categories |
|-------|------:|------------|
| 1 | 7 | Foundational (main.py, db.py, auth.py) |
| 2 | 66 | Security, Policy, Optimization, Routing |
| 3 | 56 | Traces, Storage, Models, Schemas |
| 4 | 30 | Auth, Workflow, Skills, Policy Runtime |
| 5 | 27 | `__init__.py` + Frontend utilities |

**Result:** UNKNOWN reduced from 183 → 2 (99% reduction)

---

## Artifacts Created

| Artifact | Path | Purpose |
|----------|------|---------|
| Inventory Report | `docs/codebase-registry/CODEBASE_INVENTORY.md` | Full layer mapping |
| Triage Log | `docs/codebase-registry/UNKNOWN_TRIAGE.md` | Research pass record |
| Inventory Script | `scripts/inventory/full_inventory.py` | Scanning tool |
| UNKNOWN Finder | `scripts/inventory/find_unknown_files_v2.py` | Gap detector |

---

## Governance Integration

### Session Requirements (Added to SESSION_PLAYBOOK.yaml)

1. **Inventory Update Rule:** After every task, update codebase inventory if files were added/modified
2. **Hygiene Print Rule:** Print artifact hygiene summary after every task

### Validation Checks

| Check | Tool | Frequency |
|-------|------|-----------|
| UNKNOWN count | `find_unknown_files_v2.py` | Per session |
| Layer violations | Import checker | Per commit |
| Header presence | Inventory script | Weekly |

---

## Key Invariants

1. **UNKNOWN ≈ 0** — Every file must have a layer
2. **L4 is largest domain layer** — Business logic concentrated
3. **Product boundaries intact** — L1-L3 product-specific, L4-L8 system-wide
4. **Headers earned confidence** — HIGH = explicit, MEDIUM = inferred

---

## Usage

### Check Inventory Status

```bash
python3 scripts/inventory/full_inventory.py --json | jq '.statistics'
```

### Find UNKNOWN Files

```bash
python3 scripts/inventory/find_unknown_files_v2.py
```

### Add Header to New File

Use the standard header format at the top of every new file.

---

## Related PINs

- PIN-245: Architecture Governor Role
- PIN-237: Codebase Registry Survey
- PIN-170: System Contract Governance Framework

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-30 | Initial inventory complete |
| 2025-12-30 | 186 headers added via research pass |
| 2025-12-30 | UNKNOWN: 183 → 2 |
| 2025-12-30 | Session playbook updated with hygiene rules |
| 2025-12-30 | Non-Executable Artifact Classes introduced (CODE, DATA, STYLE, CONFIG, DOC, TEST) |
| 2025-12-30 | UNKNOWN: 2 → 0 (true zero achieved) |
| 2025-12-30 | Governance updates: ARCH-GOV-006, CODE-REG-002, Section 24 Artifact Class Contract |
| 2025-12-30 | Templates updated: ARTIFACT_INTENT.yaml, FILE_HEADER_TEMPLATE.md |
| 2025-12-30 | SESSION_PLAYBOOK v2.6 with full artifact class enforcement |
