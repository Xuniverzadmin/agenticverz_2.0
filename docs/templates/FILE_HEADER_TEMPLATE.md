# File Header Template

**Status:** MANDATORY
**Reference:** PIN-245 (Integration Integrity System), PIN-240 (Seven-Layer Model), PIN-248 (Artifact Classes)

---

## Purpose

Every new file must be classified. Header requirements depend on artifact class.

---

## Artifact Class Determines Header Requirement

| Class | Type | Header Required? |
|-------|------|-----------------|
| CODE | Executable | **YES** - Full header mandatory |
| TEST | Executable | **YES** - Full header mandatory |
| DATA | Non-Executable | NO - Layer inferred from path |
| STYLE | Non-Executable | NO - Layer inferred (L1) |
| CONFIG | Non-Executable | Optional - Brief header acceptable |
| DOC | Non-Executable | NO - Layer inferred (L7) |

**Principle:** Not everything executes, but nothing escapes the system.

---

## Python File Header (CODE/TEST)

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
# Reference: PIN-{xxx}

"""
Module docstring here.
"""
```

### Example (L4 Domain Engine)

```python
# Layer: L4 — Domain Engine (System Truth)
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Policy evaluation and violation detection
# Callers: L2 APIs, L3 adapters
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-242 (Baseline Freeze)

"""
Policy Engine - Evaluates policy rules and detects violations.
"""
```

### Example (L2 API)

```python
# Layer: L2 — Product API
# Product: ai-console
# Temporal:
#   Trigger: user
#   Execution: async
# Role: REST endpoint for incident queries
# Callers: L1 (frontend)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L5 (workers)
# Reference: PIN-244 (L3 Adapter Contract)

"""
Incident API endpoints.
"""
```

---

## TypeScript/React File Header

```typescript
/**
 * Layer: L{x} — {Layer Name}
 * Product: {product | system-wide}
 * Temporal:
 *   Trigger: {user|api|worker|scheduler}
 *   Execution: {sync|async}
 * Role: {single-line responsibility}
 * Callers: {who renders/uses this?}
 * Allowed Imports: L{x}, L{y}
 * Forbidden Imports: L{z}
 * Reference: PIN-{xxx}
 */
```

### Example (L1 Page)

```typescript
/**
 * Layer: L1 — Product Experience
 * Product: ai-console
 * Temporal:
 *   Trigger: user
 *   Execution: sync
 * Role: Incidents list page with filters and search
 * Callers: Router (AppLayout)
 * Allowed Imports: L2 (via API hooks)
 * Forbidden Imports: L4, L5, L6
 * Reference: PIN-245 (BIT coverage required)
 */
```

---

## YAML/Config File Header

```yaml
# Layer: L{x} — {Layer Name}
# Product: {product | system-wide}
# Role: {single-line responsibility}
# Reference: PIN-{xxx}
```

---

## Shell Script Header

```bash
#!/bin/bash
# Layer: L7 — Ops & Deployment
# Product: system-wide
# Role: {single-line responsibility}
# Reference: PIN-{xxx}
```

---

## Validation Rules

A file header is **invalid** if:

1. Layer is missing or ambiguous
2. Product is missing (use `system-wide` if unsure)
3. Temporal information is missing for executable code
4. Role is empty or says "TODO"

---

## CI Enforcement

The CI pipeline will validate file headers using:

```bash
scripts/ops/file_header_validator.py
```

Files without valid headers will **block the build**.

---

## Non-Executable Artifact Classification

Non-executable files don't require headers but must be classified:

### DATA Files
- Located in `/data/` directories or have `.json` extension
- Layer inferred: L4 (domain data) or L6 (platform data) based on path
- Example: `backend/app/data/failure_catalog.json` → L4

### STYLE Files
- CSS/SCSS files
- Layer inferred: L1 (Product Experience)
- Example: `website/aos-console/console/src/index.css` → L1

### CONFIG Files
- YAML, INI, TOML, Dockerfile, Makefile
- Layer inferred: L7 (Ops & Deployment)
- Optional brief header for clarity:
```yaml
# Layer: L7 — Ops & Deployment
# Role: Prometheus scrape configuration
```

### DOC Files
- Markdown documentation
- Layer inferred: L7 (Ops & Deployment)
- No header required

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Template created (PIN-245) |
| 2025-12-30 | Added artifact class guidance (PIN-248) |
