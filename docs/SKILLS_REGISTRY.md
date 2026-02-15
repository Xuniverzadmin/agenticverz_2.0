# Codex Skills Registry

Generated artifact for lazy-load skill discovery. Do not hardcode full skill loads in bootstrap.

- Generated: `2026-02-15 09:25:06 UTC`
- Skills root: `/root/.codex/skills`
- Intent map: `/root/agenticverz2.0/config/intent_skill_map.json`

## Installed Skills

| Skill | Description | Path | Type |
|------|-------------|------|------|
| `git-commit-push` | Safely stage, commit, and push repository changes with explicit scope control, clean commit summaries, and guarded push behavior. Use when asked to commit and/or push code, create a normal commit, or prepare a branch update for remote. | `/root/.codex/skills/git-commit-push/SKILL.md` | project |
| `hoc-session-bootstrap` | Bootstrap HOC work sessions with mandatory governance context loading, architecture invariant confirmation, and UC/readiness status snapshots. Use when a new session starts, when resuming paused UC work, when auditing current UC closure state, or before any HOC domain implementation or review task. | `/root/.codex/skills/hoc-session-bootstrap/SKILL.md` | project |
| `hoc-uc-closure` | Drive HOC usecase closure from RED to GREEN with deterministic governance gates, script-to-UC linkage, and evidence artifact generation. Use when asked to add new UC sections, map domain scripts to UCs, expand governance tests, run architecture gates, update INDEX/HOC_USECASE_CODE_LINKAGE/PROD_READINESS trackers, and produce implementation or reality-audit markdown artifacts. | `/root/.codex/skills/hoc-uc-closure/SKILL.md` | project |

## Intent to Skill Mapping

Lazy-load rule: match intent first, then load only selected skill `SKILL.md`, and only needed references.

| Intent ID | Match Any | Skill | Confidence |
|-----------|-----------|-------|------------|
| `hoc_session_start_or_resume` | `bootstrap`, `session start`, `resume hoc`, `load project context`, `startup checklist` | `hoc-session-bootstrap` | high |
| `hoc_uc_closure_and_mapping` | `uc closure`, `usecase mapping`, `red to green`, `hoc linkage`, `governance gates` | `hoc-uc-closure` | high |
| `git_commit_and_push` | `commit`, `push`, `git commit`, `git push`, `publish branch` | `git-commit-push` | high |

## Activation Policy (Summary)

- Activation mode: `lazy`
- Max skills per task: `2`
- Low confidence behavior: `ask`
- Never preload full skill bodies at bootstrap; load on-demand per task intent.

