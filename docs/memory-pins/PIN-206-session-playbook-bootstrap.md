# PIN-206: Session Playbook Bootstrap (SPB)

**Status:** FROZEN
**Date:** 2025-12-27
**Category:** Infrastructure / Session Management
**Frozen:** 2025-12-27

---

## Problem Statement

Claude sessions have no memory continuity. Every session starts fresh with no guarantee that constraints, frozen decisions, or behavioral rules are loaded.

**Failure Modes Before SPB:**
- Session resumed without loading constraints, caused regression
- "I assumed visibility was optional" (Phase B gap)
- Phase C forgets Phase B rules
- New session silently weaker than previous
- Human forgets to restate rules

**Core Truth:**
> Memory decays. Contracts don't.
> Sessions must boot like systems, not humans.

---

## Solution: Session Playbook Bootstrap

The equivalent of a DB migration head check, but for agent behavior.

### Architecture

| Component | Location | Purpose |
|-----------|----------|---------|
| Playbook | `docs/playbooks/SESSION_PLAYBOOK.yaml` | Single source of truth for mandatory documents |
| Behavior Rule | `BL-BOOT-001` in `behavior_library.yaml` | Enforces first-response bootstrap |
| Validator | `scripts/ops/session_bootstrap_validator.py` | Mechanically validates bootstrap |
| CLAUDE.md | Reference | Documents the requirement |

---

## Mandatory Load (v1.0)

These documents MUST be loaded and acknowledged at session start:

| Document | Purpose | Phase |
|----------|---------|-------|
| CLAUDE_BOOT_CONTRACT.md | Boot sequence and forbidden actions | Core |
| behavior_library.yaml | Behavior rules and triggers | Core |
| visibility_contract.yaml | O1-O4 visibility declarations | Core |
| LESSONS_ENFORCED.md | 15 enforced invariants | Core |
| PIN-199-pb-s1-retry-immutability.md | Retry creates NEW execution | B |
| PIN-202-pb-s2-crash-recovery.md | Crashed runs never silently lost | B |
| PIN-203-pb-s3-controlled-feedback-loops.md | Feedback observes but never mutates | B |
| PIN-204-pb-s4-policy-evolution-with-provenance.md | Policies proposed, never auto-enforced | B |
| PIN-205-pb-s5-prediction-without-determinism-loss.md | Predictions advise, never influence | B |

---

## Bootstrap Confirmation Format

Claude's first response MUST be:

```
SESSION_BOOTSTRAP_CONFIRMATION
- playbook_version: 1.0
- loaded_documents:
  - CLAUDE_BOOT_CONTRACT.md
  - behavior_library.yaml
  - visibility_contract.yaml
  - LESSONS_ENFORCED.md
  - PIN-199-pb-s1-retry-immutability.md
  - PIN-202-pb-s2-crash-recovery.md
  - PIN-203-pb-s3-controlled-feedback-loops.md
  - PIN-204-pb-s4-policy-evolution-with-provenance.md
  - PIN-205-pb-s5-prediction-without-determinism-loss.md
- restrictions_acknowledged: YES
- current_phase: B
```

Nothing else is allowed in the first response.

---

## Forbidden Actions (Before Bootstrap)

These actions are BLOCKED until SESSION_BOOTSTRAP_CONFIRMATION is complete:

| Action | Reason |
|--------|--------|
| phase_testing | Cannot test without knowing phase constraints |
| acceptance_declaration | Cannot declare acceptance without knowing criteria |
| code_changes | Cannot modify code without knowing invariants |
| migration_creation | Cannot create migrations without knowing schema rules |
| api_creation | Cannot create APIs without knowing visibility contract |

---

## Validation Results (2025-12-27)

```
✓ Valid bootstrap (all 9 docs, correct version) → PASS
✗ Missing bootstrap section → BLOCK
✗ Partial documents (7 missing) → BLOCK
✗ Phase B work without bootstrap → BLOCK
```

---

## Phase Extension Mechanism

When new phases are frozen, their PINs are added to `SESSION_PLAYBOOK.yaml`:

```yaml
# Add Phase C when frozen
mandatory_load:
  # ... existing documents ...
  - path: docs/memory-pins/PIN-210-pc-s1-telemetry.md
    purpose: PC-S1 Telemetry constraints
    required: true
    phase: C
```

**Key Property:** The enforcement mechanism stays the same forever. Only the playbook changes.

---

## What This Prevents

| Failure Mode | Status |
|--------------|--------|
| Claude starts testing without constraints | BLOCKED |
| "I assumed visibility was optional" | BLOCKED |
| Phase C forgets Phase B rules | BLOCKED |
| New session silently weaker than previous | BLOCKED |
| Human forgets to restate rules | BLOCKED |

---

## Usage

### Check Playbook Structure
```bash
python3 scripts/ops/session_bootstrap_validator.py --check-playbook
```

### Generate Bootstrap Template
```bash
python3 scripts/ops/session_bootstrap_validator.py --generate-template
```

### Validate a Response
```bash
python3 scripts/ops/session_bootstrap_validator.py --response /path/to/response.txt
```

---

## Related Artifacts

| Artifact | Location |
|----------|----------|
| Session Playbook | `docs/playbooks/SESSION_PLAYBOOK.yaml` |
| BL-BOOT-001 Rule | `docs/behavior/behavior_library.yaml` |
| Bootstrap Validator | `scripts/ops/session_bootstrap_validator.py` |
| Visibility Contract | `docs/contracts/visibility_contract.yaml` |
| CLAUDE.md | Project root |

---

## Truth Anchor

> Memory decays. Contracts don't.
> Sessions must boot like systems, not humans.

Anything that must hold across sessions must be **injected and verified** at session start, not remembered.

---

*Generated: 2025-12-27*
*Frozen: 2025-12-27*
*Reference: Last Mile Guarantee / Session-Level Inevitability*
