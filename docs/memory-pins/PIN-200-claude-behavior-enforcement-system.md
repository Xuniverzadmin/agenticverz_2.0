# PIN-200: Claude Behavior Enforcement System

**Status:** ✅ COMPLETE
**Created:** 2025-12-27
**Category:** Governance / Claude Discipline
**Milestone:** Phase B.1

---

## Summary

Implemented comprehensive Claude behavior enforcement system with boot contract, pre-code discipline, and automated response validation. Ensures Claude follows PLAN-VERIFY-ACT model and cannot skip required checks.

---

## Details

## Overview

Implemented a three-layer behavior enforcement system for Claude that ensures disciplined, predictable behavior even across session restarts.

## Problem Solved

Claude, as a stateless LLM, cannot "remember" rules between sessions. Previous approaches relied on:
- Human vigilance to catch skipped steps
- Social contract (Claude "promising" to follow rules)
- Memory that gets lost on session restart

This does not scale and fails under fatigue.

## Solution: Behavior Enforcement Loop (BEL)

Three mechanisms working together:

```
1. Instruction Injection (every session)
2. Output Validation (automatic, not human)
3. Hard Failure on Violation (mechanical)
```

## Implementation

### Layer 1: Boot Contract (Instruction Injection)

**File:** `CLAUDE_BOOT_CONTRACT.md`

Every session starts with mandatory boot sequence:

```
BOOT STEP 1: Load memory pins, lessons, contracts
BOOT STEP 2: Identify current phase (A/A.5/B/C)
BOOT STEP 3: Follow P-V-A (Plan → Verify → Act)
BOOT STEP 4: Avoid forbidden actions
BOOT STEP 5: Include SELF-AUDIT for code
BOOT STEP 6: Report BLOCKED if conflict
```

Required acknowledgement:
> "AgenticVerz boot sequence acknowledged.
> I will comply with memory pins, lessons learned, and system contracts.
> Current phase: [PHASE]"

### Layer 2: Pre-Code Discipline (Task Checklist)

**File:** `CLAUDE_PRE_CODE_DISCIPLINE.md`

Seven mandatory tasks before code:

| Task | Phase | Purpose | Required Output |
|------|-------|---------|-----------------|
| 0 | Accept | Acknowledge contract | Explicit statement |
| 1 | PLAN | System state inventory | SYSTEM STATE INVENTORY |
| 2 | VERIFY | Risk assessment | CONFLICT & RISK SCAN |
| 3 | PLAN | Migration intent | MIGRATION INTENT |
| 4 | PLAN | Execution plan | EXECUTION PLAN |
| 5 | ACT | Write code | Actual changes |
| 6 | VERIFY | Self-check | SELF-AUDIT |

### Layer 3: Automated Validation (Machine Enforcement)

**File:** `scripts/ops/claude_response_validator.py`

Validates Claude responses automatically:

```bash
# Validate response file
python claude_response_validator.py response.md

# Validate from stdin
echo "response text" | python claude_response_validator.py --stdin
```

Checks performed:
- Boot acknowledgement present
- SELF-AUDIT section present (if code detected)
- Database verification mentioned
- Memory pins check mentioned
- Historical mutation risk assessed

Invalid responses are REJECTED - not accepted for use.

## PLAN → VERIFY → ACT Model

```
┌────────────────────────────────────────────────────────────────┐
│                    P-V-A DISCIPLINE                             │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                │
│   │   PLAN   │ →  │  VERIFY  │ →  │   ACT    │                │
│   └──────────┘    └──────────┘    └──────────┘                │
│        │               │               │                       │
│   Tasks 1,3,4      Tasks 2,6        Task 5                    │
│   What will        Is it safe?      Write code                │
│   change?          Conflicts?       (only now)                │
│                                                                 │
│   NO CODE UNTIL PLAN+VERIFY COMPLETE                           │
└────────────────────────────────────────────────────────────────┘
```

## Enforcement Summary

| Layer | File | Purpose | Enforcement |
|-------|------|---------|-------------|
| 1 | `CLAUDE_BOOT_CONTRACT.md` | Session initialization | Instruction injection |
| 2 | `CLAUDE_PRE_CODE_DISCIPLINE.md` | Task checklist | Required output format |
| 3 | `claude_response_validator.py` | Output validation | Machine rejection |
| 4 | `CLAUDE.md` | Quick reference | First section in context |
| 5 | `session_start.sh` | Operator reminder | Script output |
| 6 | `claude_session_boot.sh` | Full boot prompt | Copy-paste ready |

## Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `CLAUDE_BOOT_CONTRACT.md` | Created | Session boot sequence |
| `CLAUDE_PRE_CODE_DISCIPLINE.md` | Created | Pre-code task set |
| `scripts/ops/claude_response_validator.py` | Created | Automated validation |
| `scripts/ops/claude_session_boot.sh` | Created | Boot prompt generator |
| `CLAUDE.md` | Modified | Added enforcement section |
| `scripts/ops/session_start.sh` | Modified | Added discipline reminder |

## How Behavior Changes

### Before (Session Start)
```
1. User asks Claude to do something
2. Claude starts coding immediately
3. Mistakes caught (or not) by human review
```

### After (Session Start)
```
1. Claude reads CLAUDE.md, sees enforcement section FIRST
2. Claude must acknowledge boot sequence
3. For code changes, Claude must complete Tasks 0-4 first
4. Claude must include SELF-AUDIT in response
5. Response validated by machine before acceptance
6. Invalid responses rejected automatically
```

## Forbidden Actions (Mechanically Blocked)

| Action | Why Forbidden | How Blocked |
|--------|---------------|-------------|
| Skip SELF-AUDIT | No self-check | Validator rejects |
| Mutate history | Violates S1/S6 | DB trigger + validator |
| Assume schema | Causes forks | Task 2 required |
| Code before verify | Skips safety | Task order enforced |

## Usage

### For Operators

```bash
# Run session start
./scripts/ops/session_start.sh

# Generate boot prompt for Claude
./scripts/ops/claude_session_boot.sh

# Validate Claude response
python scripts/ops/claude_response_validator.py response.md
```

### For Claude (in every session)

1. Read `CLAUDE.md` (enforcement section first)
2. Acknowledge boot sequence
3. For code tasks: complete Tasks 0-6 in order
4. Always include SELF-AUDIT for code changes

## Truth Guarantee

This system ensures Claude:
- Cannot skip verification steps
- Cannot assume schema state
- Cannot mutate history accidentally
- Cannot "helpfully" shortcut
- Cannot produce invalid responses (they're rejected)

The human is removed from the enforcement loop.
Claude becomes a **disciplined, predictable engineering agent**.

---

## Related PINs

- [PIN-199](PIN-199-.md)
