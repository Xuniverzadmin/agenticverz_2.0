# AgenticVerz Machine-Native Working Environment

**Purpose:** Clean, focused context for M8-M14 implementation sessions.

---

## Contents

| File | Purpose |
|------|---------|
| `milestone_plan.md` | M8-M14 roadmap with acceptance criteria |
| `auth_blocker_notes.md` | PIN-009 auth integration blocker |
| `demo_checklist.md` | Demo productionization tasks |
| `sdk_packaging_checklist.md` | Python/JS SDK packaging tasks |
| `auth_integration_checklist.md` | Real auth provider setup |
| `repo_snapshot.md` | Current codebase state |

---

## How to Use This Folder

### For New Sessions

1. Read `repo_snapshot.md` first (current state)
2. Read `milestone_plan.md` (what we're building)
3. Pick a checklist to work on

### For Focused Work

Each checklist is self-contained with:
- Current state
- Tasks with effort estimates
- Acceptance criteria
- Verification commands

### Keep It Clean

- Update checklists as you complete items
- Remove completed files or archive them
- Add new context files only if needed

---

## M8 Priority Order

```
1. auth_integration_checklist.md   ← BLOCKING, do first
2. sdk_packaging_checklist.md      ← Parallel with auth
3. demo_checklist.md               ← After SDK packaged
```

---

## Quick Links

| Resource | Location |
|----------|----------|
| Full PIN-033 | `../docs/memory-pins/PIN-033-m8-m14-machine-native-realignment.md` |
| PIN Index | `../docs/memory-pins/INDEX.md` |
| Auth Requirements | `../docs/AUTH_SERVICE_REQUIREMENTS.md` |
| API Guide | `../docs/API_WORKFLOW_GUIDE.md` |

---

## Session Template

When starting a new session:

```
1. What am I working on? (Check milestone_plan.md)
2. What's blocking? (Check auth_blocker_notes.md)
3. What's the checklist? (Pick one checklist)
4. Mark items complete as you go
5. Update repo_snapshot.md if major changes
```

---

**Created:** 2025-12-05
**Status:** Ready for M8
