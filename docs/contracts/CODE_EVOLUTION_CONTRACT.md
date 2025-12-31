# Code Evolution Contract

**Status:** ENFORCED
**Version:** v1
**Effective:** 2025-12-29
**Reference:** SESSION_PLAYBOOK.yaml Section 20, PIN-237

---

## Constitutional Principles

### 1. No code change is valid without a declared purpose

Every modification to the codebase—whether a bugfix, refactor, optimization, or feature—must have an explicit purpose statement that answers: "Why is this change being made?"

### 2. No declared purpose is valid without a registered change record

Purpose statements are not comments or commit messages. They are formal change records in `docs/codebase-registry/changes/` following `change-schema-v1.yaml`.

### 3. Change records are immutable once created

Once a change record is created, it cannot be modified. If the scope or purpose changes, create a new change record.

### 4. Authority or behavior changes must be explicitly declared

Any change that modifies:
- Authority level (observe → mutate)
- Observable behavior
- API/interface contracts
- Data schemas

Must be explicitly flagged in the change record's `impact` section.

### 5. Retrospective justification is not allowed

You cannot:
- Add change records after the code is already modified
- Justify changes after the fact
- Bundle past changes into new records

Change records must precede or accompany code changes.

---

## Governing Rules

| Rule ID | Name | Enforcement |
|---------|------|-------------|
| CODE-REG-001 | Registration Required for Code Existence | BLOCKING |
| CODE-REG-002 | Purpose and Semantic Clarity Required | BLOCKING |
| CODE-REG-003 | Product and Surface Traceability | BLOCKING |
| CODE-REG-004 | Pause on Unclear Relationships | MANDATORY |
| CODE-CHANGE-001 | Change Registration Required | BLOCKING |
| CODE-CHANGE-002 | Pause on Unregistered Code Change | MANDATORY |
| CODE-CHANGE-003 | Artifact-Change Traceability | BLOCKING |

---

## What This Means in Practice

### Before Creating Code

1. Check if artifact exists: `python scripts/ops/artifact_lookup.py <name>`
2. If not registered, propose a registry entry
3. Get approval before writing code

### Before Modifying Code

1. Look up the artifact: `python scripts/ops/artifact_lookup.py --id <ID>`
2. Create a change record in `docs/codebase-registry/changes/`
3. Fill out all required fields (purpose, scope, impact)
4. Only then proceed with the modification

### Change Record Required Fields

```yaml
change_id: CHANGE-YYYY-NNNN
date: YYYY-MM-DD
author: human | claude | pair
change_type: bugfix | refactor | behavior_change | ...
purpose: Why this change is being made
scope:
  artifacts_modified:
    - AOS-XX-XXX-XXX-NNN
impact:
  authority_change: none | increased | reduced
  behavior_change: yes | no
  interface_change: yes | no
  data_change: yes | no
risk_level: low | medium | high
backward_compatibility: yes | no | unknown
validation:
  tests_added: yes | no
  tests_modified: yes | no
  manual_verification: required | not_required
```

---

## What Claude Must Do

1. **Always check registry first** before reasoning about code
2. **Never infer purpose** from filenames or behavior
3. **Stop and ask** when relationships are unclear
4. **Create change records** before modifying code
5. **Link artifacts** to change records

---

## What Claude Cannot Do

1. Create code without registry entries
2. Modify code without change records
3. Guess authority levels
4. Assume "minor" changes don't need registration
5. Auto-generate change records without approval

---

## Operational Effect

After this contract is in effect:

- Claude **cannot** add, modify, or reason about code unless it is registered
- Claude **must** create change records before modifications
- Claude **must** ask clarifying questions instead of assuming
- All code evolution becomes **auditable and traceable**

This transforms Claude from:
> "Helpful but risky"

To:
> "Strict but trustworthy"

---

## One-Line Summary

> Code may only exist if its purpose, authority, and placement are known—and code may only change if its reason for changing is explicitly recorded, linked, and auditable.

---

## References

- Schema: `docs/codebase-registry/schema-v1.yaml`
- Change Schema: `docs/codebase-registry/change-schema-v1.yaml`
- Artifacts: `docs/codebase-registry/artifacts/`
- Changes: `docs/codebase-registry/changes/`
- Lookup Tool: `scripts/ops/artifact_lookup.py`
- Survey PIN: PIN-237
- Session Playbook: Section 20
