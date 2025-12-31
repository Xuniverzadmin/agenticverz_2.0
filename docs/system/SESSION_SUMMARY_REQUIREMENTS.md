# Session Summary Requirements for Governance Continuity

**Date:** 2025-12-30
**Reference:** PIN-245, SESSION_PLAYBOOK.yaml Section 14.5
**Purpose:** Ensure governance survives session context compression

---

## Background

When Claude Code sessions run out of context and get summarized, the summarized
continuation can accidentally bypass governance if critical context is lost.

This document specifies MANDATORY elements that must be preserved in any session
summary to ensure governance continuity.

---

## Mandatory Summary Elements

### 1. Governance Status Declaration

Every session summary MUST include:

```
GOVERNANCE_CONTEXT_PRESERVED
- phase_family: {A | A.5 | B | C}
- current_stage: {stage name}
- code_reg_rules: ACTIVE (CODE-REG-001 to CODE-REG-004)
- code_change_rules: ACTIVE (CODE-CHANGE-001 to CODE-CHANGE-003)
- self_audit_required: YES
- architecture_governor: ACTIVE (ARCH-GOV-001 to ARCH-GOV-005)
```

### 2. Pending Artifact Registrations

If any artifacts were being registered or discussed:

```
PENDING_REGISTRATIONS:
- artifact_name: {name}
  artifact_id: {proposed ID}
  status: {proposed | approved | registered}
  registration_path: {path to artifact yaml}
```

### 3. Pending Change Records

If any code changes were being tracked:

```
PENDING_CHANGES:
- change_id: {CHANGE-YYYY-NNNN}
  purpose: {why}
  artifacts_affected: [{IDs}]
  status: {proposed | approved | recorded}
```

### 4. Incomplete Governance Gates

If any governance gates were incomplete:

```
INCOMPLETE_GATES:
- gate: {ARCH-GOV-001 | CODE-REG-001 | etc.}
  status: {pending_declaration | pending_approval | blocked}
  blocker: {what's blocking}
  next_action: {what Claude should do}
```

### 5. "Continue Without Asking" Interpretation

The summary MUST explicitly state:

```
CONTINUATION_INSTRUCTION_INTERPRETATION:
The instruction "continue without asking the user any further questions" applies to:
- ALLOWED: Skip clarifying questions about user requirements
- FORBIDDEN: Skip governance acknowledgment (SESSION_CONTINUATION_ACKNOWLEDGMENT)
- FORBIDDEN: Skip artifact registration (CODE-REG gates)
- FORBIDDEN: Skip change records (CODE-CHANGE gates)
- FORBIDDEN: Skip SELF-AUDIT on code changes
```

---

## Summary Template

When generating a session summary for continuation, use this template:

```markdown
## Governance Context (MANDATORY)

GOVERNANCE_CONTEXT_PRESERVED
- phase_family: C
- current_stage: C5_LEARNING
- code_reg_rules: ACTIVE
- code_change_rules: ACTIVE
- self_audit_required: YES
- architecture_governor: ACTIVE

## Pending Work

### Incomplete Registrations
[List any pending artifact registrations]

### Incomplete Change Records
[List any pending change records]

### Incomplete Governance Gates
[List any gates that need completion]

## Continuation Rules

CONTINUATION_INSTRUCTION_INTERPRETATION:
- "Continue without asking" = skip clarifying questions about requirements
- "Continue without asking" ≠ skip governance acknowledgment
- "Continue without asking" ≠ skip artifact registration
- "Continue without asking" ≠ skip change records
- "Continue without asking" ≠ skip SELF-AUDIT

Upon continuation, Claude MUST output SESSION_CONTINUATION_ACKNOWLEDGMENT
before any code work.
```

---

## What Happens Without This

If a summary omits governance context:

1. Claude may interpret "continue without asking" as permission to skip bootstrap
2. Code gets created without artifact registration → CODE-REG-001 violation
3. Code gets modified without change records → CODE-CHANGE-001 violation
4. SELF-AUDIT sections get omitted → Response INVALID
5. Architecture gates get bypassed → Temporal/layer violations accumulate

**Incident Example (2025-12-30):**
- Session was continued from summary
- "Continue without asking" was interpreted as permission to bypass all governance
- 13 tasks completed with code changes
- Zero artifact registrations created
- Zero change records created
- Root cause: Summary did not preserve governance context

---

## Enforcement

This document is referenced by:
- `CLAUDE.md` (Section: Session Continuation from Summary)
- `docs/playbooks/SESSION_PLAYBOOK.yaml` (Section 14.5)

Claude must check for governance context in summaries and explicitly acknowledge
governance rules even when told to "continue without asking".

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | Root governance rules |
| `docs/playbooks/SESSION_PLAYBOOK.yaml` | Full playbook |
| `docs/contracts/CODE_EVOLUTION_CONTRACT.md` | Code registration rules |
| `scripts/ops/session_bootstrap_validator.py` | Validation script |
