# Apis — Software Bible

**Domain:** apis  
**L2 Features:** 0  
**Scripts:** 1  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-12, Wave-4 Script Coverage Audit)

- Wave-4 target scope for apis is fully classified:
- `2` scripts total (`0 UC_LINKED`, `2 NON_UC_SUPPORT`, `0 UNLINKED` in target scope).
- These scripts are retained as support infrastructure and are intentionally not mapped to standalone UC ownership.
- Deterministic gates remain clean in Wave-4 audit, with governance suite at `308` passing tests.

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| keys_driver | L6 | `KeysDriver.fetch_key_by_id` | LEAF | 0 | L3:customer_keys_adapter | L5:keys_shim | L5:keys_engine | YES |

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 0 |
| GAP (L2→L5 direct) | 0 |

## Wrapper Inventory

_2 thin delegation functions._

- `keys_driver.KeysDriver.__init__` → ?
- `keys_driver.get_keys_driver` → ?

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`
