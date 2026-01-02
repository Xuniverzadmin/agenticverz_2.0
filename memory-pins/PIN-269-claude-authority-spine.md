# PIN-269: Claude Authority Spine Document

**Status:** ACTIVE (FROZEN)
**Created:** 2026-01-01
**Category:** Governance / Authority System
**Related PINs:** PIN-267 (test protection), PIN-268 (guidance upgrade)

---

## Executive Summary

`CLAUDE_AUTHORITY.md` is now the highest non-human authority document in the repository. It codifies the authority hierarchy, pre-flight requirements, and behavioral principles that Claude must follow.

---

## Authority Hierarchy (Frozen)

| Rank | Authority | Override Conditions |
|------|-----------|---------------------|
| 1 | Human instruction (current session) | None |
| 2 | CLAUDE_AUTHORITY.md | Human only |
| 3 | SESSION_PLAYBOOK.yaml | Ranks 1-2 |
| 4 | Memory PINs | Ranks 1-3 |
| 5 | CI rules and scripts | Ranks 1-4 |
| 6 | Tests | Ranks 1-5 |
| 7 | Existing code | Ranks 1-6 |

---

## Section Mapping to Existing Systems

| Section | Codifies | Implementation |
|---------|----------|----------------|
| §3 Classification | GU-002 CI buckets | `@pytest.mark.ci_bucket` |
| §4 Intent | GU-003 Feature Intent | `FEATURE_INTENT` boilerplate |
| §5 Invariants | GU-001 Invariant docs | `docs/invariants/` |
| §6 Guidance | GU-004 Danger fences | `app/infra/danger_fences.py` |
| §7 Artifacts | Artifact accountability | Required output schema |
| §9 Evolution | Learning codification | PIN creation rule |

---

## Frozen Status

This document is **FROZEN**. Changes require:

1. Explicit human ratification in session
2. PIN update with rationale
3. CI guard verification (if implemented)

---

## CI Protection (Proposed)

Add to `.github/workflows/ci.yml`:

```yaml
claude-authority-guard:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Verify CLAUDE_AUTHORITY.md exists
      run: |
        if [ ! -f "CLAUDE_AUTHORITY.md" ]; then
          echo "ERROR: CLAUDE_AUTHORITY.md missing"
          exit 1
        fi
    - name: Check for unauthorized changes
      run: |
        # Hash check against known good version
        EXPECTED_HASH="<sha256_of_ratified_version>"
        ACTUAL_HASH=$(sha256sum CLAUDE_AUTHORITY.md | cut -d' ' -f1)
        if [ "$ACTUAL_HASH" != "$EXPECTED_HASH" ]; then
          echo "WARNING: CLAUDE_AUTHORITY.md has been modified"
          echo "This change requires human ratification"
        fi
```

---

## Implementation Progress

| Priority | Task | Status | Artifact |
|----------|------|--------|----------|
| 1 | Add CI guard for CLAUDE_AUTHORITY.md | COMPLETE | `.github/workflows/ci.yml` |
| 2 | Create "New Feature Skeleton" template | COMPLETE | `docs/templates/NEW_FEATURE_SKELETON.md` |
| 3 | Integrate with SESSION_PLAYBOOK | COMPLETE | `docs/playbooks/SESSION_PLAYBOOK.yaml` v2.29 |

**Note:** Task 3 was refined from "prune duplications" to "integrate governance relationship".
Rather than risky deletions, we added:
- CLAUDE_AUTHORITY.md to `mandatory_load` as highest authority
- `governance_relationship` section mapping playbook → authority sections
- `deduplication_note` clarifying principle vs procedure distinction

---

## Ratified Hash

```
v1: SHA256: 910e483c2606c2e0ffe0a161e732ec098266b1cd61d2336993136d477fde834f
v2: SHA256: a1e84ff3d2e050470d30086d1d877b1bd6b13fccfc243c06ac33107941b53a8f
```

**v2 Change (PIN-270):** Added §3.5 Infrastructure State Declaration.

Changes require `AUTHORITY_RATIFIED` commit flag or CI will block.

---

## References

- `/root/agenticverz2.0/CLAUDE_AUTHORITY.md` (this spine)
- PIN-267 (Test System Protection Rule)
- PIN-268 (Guidance System Upgrade)
- `docs/playbooks/SESSION_PLAYBOOK.yaml`
- `docs/templates/INTENT_BOILERPLATE.md`
- `docs/templates/NEW_FEATURE_SKELETON.md` (new feature template)
