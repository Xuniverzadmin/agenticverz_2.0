# PIN-478: Claude Context Modularization — CLAUDE.md split + rules + hooks + project context

**Status:** COMPLETE
**Created:** 2026-01-27
**Category:** Infrastructure / Claude Memory Optimization

---

## Summary

Split monolithic CLAUDE.md (3,494 lines, ~30K tokens) into a lean core (232 lines, ~5K tokens) + 8 path-scoped rule files + project context file + 2 hook scripts. Claude now loads only relevant governance rules based on which files are being edited.

---

## Problem

CLAUDE.md was a 3,494-line monolith loaded in full every session (~30,000 tokens). This caused:
1. ~15% of context window consumed before any work began
2. Governance rules for unrelated domains loaded unnecessarily (e.g., SDSR rules when editing shell scripts)
3. No deterministic enforcement — all rules were advisory text
4. No project-specific context — Claude had no awareness of vision, mission, or current status
5. session_start.sh dumped governance text instead of showing live project state

## Changes Made

### 1. Created `.claude/project-context.md` (56 lines)
Project "soul" file: vision, mission, product, current phase, project status, development status, key references, governance model. Loaded at session start (~3K tokens).

### 2. Created 8 path-scoped rule files in `.claude/rules/`

| File | Lines | Scope | Always On? |
|------|-------|-------|-----------|
| governance-core.md | 171 | `**` | Yes |
| artifact-registration.md | 80 | `**` | Yes |
| hoc-layer-topology.md | 62 | `hoc/**`, `backend/app/hoc/**` | No |
| auth-architecture.md | 64 | `backend/app/auth/**`, `backend/app/api/**` | No |
| database-authority.md | 65 | `backend/alembic/**`, `backend/app/db/**` | No |
| sdsr-contract.md | 74 | `backend/scripts/sdsr/**`, `backend/aurora_l2/**` | No |
| ui-pipeline.md | 94 | `design/**`, `website/**` | No |
| audience-classification.md | 51 | `backend/**/*.py` | No |
| **Total** | **661** | | |

### 3. Rewrote lean CLAUDE.md (232 lines)
Retains only operational reference: tech stack, services, directories, commands, env vars, bootstrap sequence, behavior triggers, web infra, APIs, key PINs, notes. Points to `.claude/project-context.md` and `.claude/rules/` for governance.

### 4. Created hook scripts in `scripts/hooks/`

| Hook | Trigger | Checks |
|------|---------|--------|
| post_edit_check.sh | After Edit/Write | AUDIENCE/Layer headers, generated file markers, migration contract headers |
| post_bash_check.sh | After Bash | DB_AUTHORITY and DB_ROLE for alembic commands |

Both are non-blocking (exit 0, warnings only).

### 5. Created `.claude/settings.json`
Configures PostToolUse hooks for Edit/Write/Bash tools pointing to the hook scripts.

### 6. Modified `scripts/ops/session_start.sh`
Replaced "CLAUDE BEHAVIOR ENFORCEMENT" text dump (lines 324-346) with smart project context: recent PINs, HOC domain status, governance pointers.

## Token Budget (Before vs After)

| Scenario | Before | After |
|----------|--------|-------|
| Editing a .sh script or docs | ~30K | ~22K |
| Editing hoc/ Python file | ~30K | ~26.5K |
| Editing backend/app/api/ | ~30K | ~29.5K |
| Editing design/ or website/ | ~30K | ~31K |
| Reading/exploring only | ~30K | ~22K |

**Typical savings: 0-8K tokens depending on context. Best case (non-python, non-design): 27% reduction.**

## Files Created
- `.claude/project-context.md` (project vision, mission, status)
- `.claude/rules/governance-core.md`
- `.claude/rules/artifact-registration.md`
- `.claude/rules/hoc-layer-topology.md`
- `.claude/rules/auth-architecture.md`
- `.claude/rules/database-authority.md`
- `.claude/rules/sdsr-contract.md`
- `.claude/rules/ui-pipeline.md`
- `.claude/rules/audience-classification.md`
- `.claude/settings.json` (hooks config)
- `scripts/hooks/post_edit_check.sh`
- `scripts/hooks/post_bash_check.sh`

## Files Modified
- `CLAUDE.md` (3,494 → 232 lines)
- `scripts/ops/session_start.sh` (governance dump → project context summary)

## Files Preserved
- `CLAUDE.md.bak.20260127` (full original backup)

## Rule ID Coverage Audit

All rule IDs from original CLAUDE.md are present in exactly one rule file:

| Rule IDs | File |
|----------|------|
| BL-BOOT-001/002/003, FA-001-007, ARCH-CANON-001, GC-001-007, ARCH-GOV-001-006, BI-001-006, P1-P6 | governance-core.md |
| CODE-REG-001-004, CODE-CHANGE-001-003, AC-001-004, BOUNDARY-001-005, BV-001-005 | artifact-registration.md |
| BL-HOC-LAYER-001, API-002-CR-001/002 | hoc-layer-topology.md |
| BL-ENV-CONTRACT-001, RBAC-D1-D8, INV-001-005, BL-AUTH-001/002 | auth-architecture.md |
| DB-AUTH-001 | database-authority.md |
| SDSR-CONTRACT-001-003, CAP-E2E-001, GR-1-6, SDSR-PROP-001-004 | sdsr-contract.md |
| BL-UI-PIPELINE-001, BL-UI-CONSTRAINT-001, SDSR-UI-001-004, BL-SOURCE-CHAIN-001, BL-ARCH-CONSTRAINT-001 | ui-pipeline.md |
| BL-AUD-001 | audience-classification.md |

---

## Related PINs

- [PIN-474](PIN-474-.md) — Validator → scheduled scan
- [PIN-475](PIN-475-.md) — Worker pool manual restart
- [PIN-476](PIN-476-optimize-amavisd-reduce-to-1-worker-disable-broken-clamav.md) — Amavis optimization
- [PIN-477](PIN-477-.md) — Journal limits + bloat audit
