# Apis — Software Bible

**Domain:** apis  
**L2 Features:** 0  
**Scripts:** 1  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

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
