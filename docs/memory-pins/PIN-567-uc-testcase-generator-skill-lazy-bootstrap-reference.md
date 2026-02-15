# PIN-567: UC Testcase Generator Skill + Lazy Bootstrap Reference

**Status:** ✅ COMPLETE
**Created:** 2026-02-15
**Category:** Architecture / Skills / Validation

---

## Summary

Added a new deterministic skill for usecase-driven staged test-pack generation, without auto-executing tests.

The skill now supports:
- Stage 1.1 wiring/trigger-output checks.
- Stage 1.2 synthetic data injection checks (veracity + determinism).
- Stage 2 real-data integrated validation checks (quality, quantity, velocity, veracity, determinism).
- Paired executor-return format (`*_executed.md`) plus deterministic summary parsing.

---

## What Was Added

### 1. New Skill

**Path:** `~/.codex/skills/uc-testcase-generator/`

Artifacts:
- `SKILL.md`
- `agents/openai.yaml`
- `scripts/uc_testcase_pack.py`
- `references/stage_contract.md`
- `references/executed_report_contract.md`

### 2. Intent Mapping

**File:** `config/intent_skill_map.json`

Added intent rule:
- `uc_testcase_generator_staged_handoff` -> `uc-testcase-generator`

### 3. Skills Registry Refresh

**File:** `docs/SKILLS_REGISTRY.md`

Registry regenerated to include:
- installed skill entry for `uc-testcase-generator`
- intent mapping row for staged UC testcase handoff

### 4. Bootstrap Reference (Lazy-Load)

**File:** `~/.codex/skills/hoc-session-bootstrap/references/startup_checklist.md`

Added optional invocation commands:
- `generate` staged pack
- `summarize` executed report

This is an on-demand reference only; no hardcoded preload behavior was introduced.

---

## Execution Contract

Generator output:
1. `<base>.md`
2. `<base>_executed.md`
3. `<base>_synthetic_inputs.json`

Reader output:
1. `<base>_executed_summary.json`
2. `<base>_executed_summary.md`

---

## Canonical Commands

Generate:

```bash
~/.codex/skills/uc-testcase-generator/scripts/uc_testcase_pack.py generate \
  --repo-root /root/agenticverz2.0 \
  --title "UC_STAGED_TESTPACK_YYYY_MM_DD" \
  --out-dir /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases \
  --scope manifest \
  --owner Claude
```

Summarize:

```bash
~/.codex/skills/uc-testcase-generator/scripts/uc_testcase_pack.py summarize \
  --executed-file /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_STAGED_TESTPACK_YYYY_MM_DD_executed.md \
  --output-json /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_STAGED_TESTPACK_YYYY_MM_DD_executed_summary.json \
  --output-md /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_STAGED_TESTPACK_YYYY_MM_DD_executed_summary.md
```

---

## Related Artifacts

- `docs/SKILLS_REGISTRY.md`
- `config/intent_skill_map.json`
- `docs/memory-pins/PIN-566-uat-hardening-reality-closure-and-ops-literature-canonicalization.md`
