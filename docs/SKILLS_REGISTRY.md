# Codex Skills Registry

Generated artifact for lazy-load skill discovery. Do not hardcode full skill loads in bootstrap.

- Generated: `2026-02-15 10:16:40 UTC`
- Skills root: `/root/.codex/skills`
- Intent map: `/root/agenticverz2.0/config/intent_skill_map.json`

## Installed Skills

| Skill | Description | Path | Type |
|------|-------------|------|------|
| `codebase-arch-audit-gatepass` | Audit codebase health for bugs, runtime-risk errors, and architecture/design deviations, then run deterministic machine checks and gatepass validation with reproducible artifacts. Use when asked to audit code quality, detect improper design, verify architecture conformance, or produce pass/fail gate evidence. | `/root/.codex/skills/codebase-arch-audit-gatepass/SKILL.md` | project |
| `git-commit-push` | Safely stage, commit, and push repository changes with explicit scope control, clean commit summaries, and guarded push behavior. Use when asked to commit and/or push code, create a normal commit, or prepare a branch update for remote. | `/root/.codex/skills/git-commit-push/SKILL.md` | project |
| `hoc-session-bootstrap` | Bootstrap HOC work sessions with mandatory governance context loading, architecture invariant confirmation, and UC/readiness status snapshots. Use when a new session starts, when resuming paused UC work, when auditing current UC closure state, or before any HOC domain implementation or review task. | `/root/.codex/skills/hoc-session-bootstrap/SKILL.md` | project |
| `hoc-uc-closure` | Drive HOC usecase closure from RED to GREEN with deterministic governance gates, script-to-UC linkage, and evidence artifact generation. Use when asked to add new UC sections, map domain scripts to UCs, expand governance tests, run architecture gates, update INDEX/HOC_USECASE_CODE_LINKAGE/PROD_READINESS trackers, and produce implementation or reality-audit markdown artifacts. | `/root/.codex/skills/hoc-uc-closure/SKILL.md` | project |
| `llm-task-plan-handoff` | Create detailed LLM execution handoff plans with TODO matrices and deterministic return templates. Use when asked to produce a *_plan.md for Claude (or another coding LLM) and a paired *_plan_implemented.md that the executor fills when returning results. | `/root/.codex/skills/llm-task-plan-handoff/SKILL.md` | project |
| `strategic-thinker-northstar` | Build strategic direction from vision/mission plus live codebase reality by invoking audit gatepass checks, then generate Claude execution handoff plans with measurable iteration scorecards. Use when asked for strategy, north-star planning, iteration direction, or progress-measured technical roadmaps. | `/root/.codex/skills/strategic-thinker-northstar/SKILL.md` | project |
| `uc-testcase-generator` | Generate staged use-case test packs from registered UC artifacts, including route/operation evidence and paired executor-return templates. Use when asked to create a `*.md` test document and matching `*_executed.md` report template for Claude to execute manually (without this skill running tests), especially for Stage 1.1 wiring checks, Stage 1.2 synthetic-data determinism checks, and Stage 2 real-data integrated validation. | `/root/.codex/skills/uc-testcase-generator/SKILL.md` | project |

## Intent to Skill Mapping

Lazy-load rule: match intent first, then load only selected skill `SKILL.md`, and only needed references.

| Intent ID | Match Any | Skill | Confidence |
|-----------|-----------|-------|------------|
| `hoc_session_start_or_resume` | `bootstrap`, `session start`, `resume hoc`, `load project context`, `startup checklist` | `hoc-session-bootstrap` | high |
| `hoc_uc_closure_and_mapping` | `uc closure`, `usecase mapping`, `red to green`, `hoc linkage`, `governance gates` | `hoc-uc-closure` | high |
| `git_commit_and_push` | `commit`, `push`, `git commit`, `git push`, `publish branch` | `git-commit-push` | high |
| `codebase_audit_bugs_architecture_determinism` | `audit codebase`, `bugs and errors`, `architecture deviation`, `improper design`, `determinism checks`, `gatepass` | `codebase-arch-audit-gatepass` | high |
| `llm_task_todo_detailed_plan_handoff` | `detailed plan`, `todo plan`, `claude execute`, `plan md`, `plan_implemented`, `taskpack for claude` | `llm-task-plan-handoff` | high |
| `strategic_direction_northstar_cycle` | `strategic thinker`, `north star`, `strategic direction`, `iteration strategy`, `vision mission analyze codebase`, `measure progress each iteration` | `strategic-thinker-northstar` | high |
| `uc_testcase_generator_staged_handoff` | `test case generator`, `use case registered tests`, `staged test pack`, `stage 1.1 stage 1.2 stage 2`, `executed md report`, `routes and means to test` | `uc-testcase-generator` | high |

## Activation Policy (Summary)

- Activation mode: `lazy`
- Max skills per task: `2`
- Low confidence behavior: `ask`
- Never preload full skill bodies at bootstrap; load on-demand per task intent.

