# PIN-238: Code Registration & Evolution Governance

**Status:** ✅ COMPLETE
**Created:** 2025-12-29
**Category:** Infrastructure / Governance
**Milestone:** Post-M29 - Registry Governance

---

## Summary

Implemented code registration and evolution governance. All code must be registered before creation/modification. Change records required for all modifications. Claude cannot infer purpose, authority, or relationships.

---

## Details

## Summary

Implemented comprehensive governance framework enforcing that:
1. All code must be registered in the Codebase Purpose & Authority Registry
2. All code modifications require explicit change records
3. Claude cannot infer purpose, ownership, or relationships
4. Pause-and-ask protocol enforced for unclear situations

---

## Governing Principles

> All executable or semantically meaningful code MUST be registered in the Codebase Purpose & Authority Registry before it can be created, modified, or reasoned about.

> Code evolution is authority. Authority must be declared.

> Claude must not infer purpose, ownership, or relationships where they are not explicitly registered.

---

## Deliverables

### New Files Created

| File | Purpose |
|------|---------|
| `docs/codebase-registry/change-schema-v1.yaml` | Schema for change records (FROZEN) |
| `docs/codebase-registry/changes/` | Change record storage directory |
| `docs/contracts/CODE_EVOLUTION_CONTRACT.md` | Constitutional contract |
| `scripts/ops/change_record.py` | Change record helper script |

### Updated Files

| File | Changes |
|------|---------|
| `docs/playbooks/SESSION_PLAYBOOK.yaml` | v2.0 → v2.1, added Section 20 |
| `CLAUDE_BEHAVIOR_LIBRARY.md` | v1.3.0 → v1.4.0, added BL-CODE-REG-* rules |
| `CLAUDE.md` | Added governance section and change_record.py docs |
| `PIN-237` | Updated artifact counts (113 total) |

---

## Blocking Rules Added

### Code Registration Rules (SESSION_PLAYBOOK Section 20)

| Rule ID | Name | Enforcement |
|---------|------|-------------|
| CODE-REG-001 | Registration Required for Code Existence | BLOCKING |
| CODE-REG-002 | Purpose and Semantic Clarity Required | BLOCKING |
| CODE-REG-003 | Product and Surface Traceability | BLOCKING |
| CODE-REG-004 | Pause on Unclear Relationships | MANDATORY |
| CODE-CHANGE-001 | Change Registration Required | BLOCKING |
| CODE-CHANGE-002 | Pause on Unregistered Code Change | MANDATORY |
| CODE-CHANGE-003 | Artifact-Change Traceability | BLOCKING |

### Behavior Library Rules

| Rule ID | Name | Class |
|---------|------|-------|
| BL-CODE-REG-001 | Codebase Registry Supremacy | code_registration |
| BL-CODE-REG-002 | No Silent Semantics | silent_inference |
| BL-CODE-REG-003 | Change Record Before Modification | untracked_changes |

---

## Code Evolution Contract (Constitutional)

Five principles now enforced:

1. **No code change is valid without a declared purpose**
2. **No declared purpose is valid without a registered change record**
3. **Change records are immutable once created**
4. **Authority or behavior changes must be explicitly declared**
5. **Retrospective justification is not allowed**

---

## Helper Scripts

### artifact_lookup.py (AOS-OP-OPS-ALK-001)
```bash
python scripts/ops/artifact_lookup.py <name>        # Search by name
python scripts/ops/artifact_lookup.py --id <ID>     # Search by ID
python scripts/ops/artifact_lookup.py --product ai-console  # Filter
```

### change_record.py (AOS-OP-OPS-CHR-001)
```bash
python scripts/ops/change_record.py next            # Get next ID
python scripts/ops/change_record.py list            # List records
python scripts/ops/change_record.py create \
    --purpose "Why" --type bugfix --artifacts AOS-XX-XXX-001
```

---

## Operational Effect

### What Claude Cannot Do
- Create code without registry entries
- Modify code without change records
- Infer purpose from filenames alone
- Guess authority based on behavior
- Assume "minor" changes don't need registration

### What Claude Must Do
- Always check registry first
- Stop and ask when unclear
- Create change records before modifications
- Link artifacts to change records
- Wait for approval before proceeding

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│           CODE REGISTRATION DISCIPLINE                      │
├─────────────────────────────────────────────────────────────┤
│  1. SEARCH: artifact_lookup.py <name>                       │
│  2. IF NOT FOUND: Propose registration, wait for approval   │
│  3. IF MODIFYING: Create change record first                │
│  4. IF UNCLEAR: Stop and ask for clarification              │
│  5. NEVER INFER: Purpose, authority, or relationships       │
└─────────────────────────────────────────────────────────────┘
```

---

## One-Line Summary

> Code may only exist if its purpose, authority, and placement are known—and code may only change if its reason for changing is explicitly recorded, linked, and auditable.

---

## References

- SESSION_PLAYBOOK.yaml Section 20
- CODE_EVOLUTION_CONTRACT.md
- CLAUDE_BEHAVIOR_LIBRARY.md (BL-CODE-REG-*)
- change-schema-v1.yaml
- PIN-237 (Codebase Registry Survey)


---

## Related PINs

- [PIN-237](PIN-237-codebase-registry-survey.md) - Codebase Registry Survey (113 artifacts)
- [PIN-235](PIN-235-products-first-architecture-migration.md) - Products-First Architecture Migration
- [PIN-236](PIN-236-code-purpose-authority-registry.md) - Customer Console Constitution
