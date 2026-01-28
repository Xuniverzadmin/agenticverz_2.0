---
paths:
  - "**"
alwaysApply: true
---

# Artifact Registration & Code Change Rules

These rules apply to ALL files. Every artifact must be registered, every change recorded.

## Code Registration (CODE-REG-001 to CODE-REG-004)

| Rule ID | Name | Enforcement |
|---------|------|-------------|
| CODE-REG-001 | Registration Required for Code Existence | BLOCKING |
| CODE-REG-002 | Purpose and Semantic Clarity Required | BLOCKING |
| CODE-REG-003 | Product and Surface Traceability | BLOCKING |
| CODE-REG-004 | Pause on Unclear Relationships | MANDATORY |

Before creating code: `python scripts/ops/artifact_lookup.py <name>`
If not found: Propose a registry entry for approval. Wait for confirmation.

## Code Change Records (CODE-CHANGE-001 to CODE-CHANGE-003)

| Rule ID | Name | Enforcement |
|---------|------|-------------|
| CODE-CHANGE-001 | Change Registration Required | BLOCKING |
| CODE-CHANGE-002 | Pause on Unregistered Code Change | MANDATORY |
| CODE-CHANGE-003 | Artifact-Change Traceability | BLOCKING |

Before modifying code:
1. Look up artifact: `python scripts/ops/artifact_lookup.py --id <ID>`
2. Create change record: `python scripts/ops/change_record.py create`
3. Get approval before proceeding

## Artifact Class Rules (AC-001 to AC-004)

| Rule | Enforcement |
|------|-------------|
| AC-001: Every file must have artifact_class | BLOCKING |
| AC-002: UNKNOWN is never acceptable | BLOCKING |
| AC-003: Every artifact must have a layer | BLOCKING |
| AC-004: Executable artifacts require headers | BLOCKING |

Classes: CODE, TEST, DATA, STYLE, CONFIG, DOC. UNKNOWN is never acceptable.

## Product Boundary Enforcement

### Prime Invariant

No code artifact may be created, modified, or reasoned about unless ALL declared:
1. Product ownership (ai-console / system-wide / product-builder)
2. Invocation ownership (who calls this?)
3. Boundary classification (surface / adapter / platform)
4. Failure jurisdiction (what breaks if this is removed?)

### Three Blocking Questions

| Question | Unacceptable Answers |
|----------|---------------------|
| Who calls this in production? | "Not sure", "Later", "Probably" |
| What breaks if AI Console is deleted? | "I don't know", "Everything" |
| Who must NOT depend on this? | "Anyone can use it", "No restrictions" |

### Bucket Classification

| Bucket | Definition |
|--------|------------|
| Surface | User-facing, product-specific |
| Adapter | Thin translation layer (< 200 LOC, no business logic) |
| Platform | Shared infrastructure |
| Orphan | No production callers → ILLEGAL |

## File Renames (HIGH-RISK)

Renames require: change record with `change_type: rename`, risk_level >= medium, interface_change: yes, backward_compatibility: no, manual_verification: required.

## Linting Technical Debt (PIN-438)

New violations are blocked; existing debt is tolerated. BLCA: all backend files, YES blocking. Ruff: staged files only. Pyright: Zone A warning only.
