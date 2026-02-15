# HOC CUS Usecase Usage Inventory - 2026-02-15

## Scope
- Target codebase: `backend/app/hoc/cus/*` (`.py` files).
- Usecase set: canonical registry `UC-001..UC-040` from `INDEX.md`.
- Linkage source: `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`.

## Snapshot
- Generated at (UTC): `2026-02-15T06:05:02Z`
- `hoc/cus` python files on disk: `573`
- Classification rows: `573`
- Classification path misses: `0`
- `UC_LINKED`: `264`
- `NON_UC_SUPPORT`: `309`
- Canonical UCs with >=1 linked script: `24/40`
- Canonical UCs with 0 linked scripts: `16`

## Canonical UC Coverage Summary
| UC | Status | Linked Scripts | Domains |
| --- | --- | ---: | --- |
| UC-001 | `GREEN` | 17 | controls,hoc_spine,overview |
| UC-002 | `GREEN` | 31 | account,api_keys,hoc_spine,integrations |
| UC-003 | `GREEN` | 6 | logs |
| UC-004 | `GREEN` | 0 | - |
| UC-005 | `GREEN` | 0 | - |
| UC-006 | `GREEN` | 0 | - |
| UC-007 | `GREEN` | 0 | - |
| UC-008 | `GREEN` | 0 | - |
| UC-009 | `GREEN` | 8 | policies |
| UC-010 | `GREEN` | 0 | - |
| UC-011 | `GREEN` | 0 | - |
| UC-012 | `GREEN` | 0 | - |
| UC-013 | `GREEN` | 0 | - |
| UC-014 | `GREEN` | 0 | - |
| UC-015 | `GREEN` | 0 | - |
| UC-016 | `GREEN` | 0 | - |
| UC-017 | `GREEN` | 11 | logs |
| UC-018 | `GREEN` | 1 | policies |
| UC-019 | `GREEN` | 2 | policies |
| UC-020 | `GREEN` | 0 | - |
| UC-021 | `GREEN` | 3 | controls |
| UC-022 | `GREEN` | 0 | - |
| UC-023 | `GREEN` | 1 | policies |
| UC-024 | `GREEN` | 10 | analytics,hoc_spine |
| UC-025 | `GREEN` | 3 | analytics,hoc_spine |
| UC-026 | `GREEN` | 1 | hoc_spine |
| UC-027 | `GREEN` | 9 | analytics,hoc_spine |
| UC-028 | `GREEN` | 0 | - |
| UC-029 | `GREEN` | 5 | controls,policies |
| UC-030 | `GREEN` | 1 | incidents |
| UC-031 | `GREEN` | 9 | incidents |
| UC-032 | `GREEN` | 0 | - |
| UC-033 | `GREEN` | 26 | hoc_spine |
| UC-034 | `GREEN` | 6 | hoc_spine |
| UC-035 | `GREEN` | 17 | hoc_spine |
| UC-036 | `GREEN` | 33 | hoc_spine |
| UC-037 | `GREEN` | 3 | integrations |
| UC-038 | `GREEN` | 1 | integrations |
| UC-039 | `GREEN` | 1 | integrations |
| UC-040 | `GREEN` | 1 | account |

## Canonical UCs With 0 Explicit Script Links
- UC-004, UC-005, UC-006, UC-007, UC-008, UC-010, UC-011, UC-012, UC-013, UC-014, UC-015, UC-016, UC-020, UC-022, UC-028, UC-032

## Unresolved UC_LINKED Rows (Need Canonical Mapping Cleanup)
- Total unresolved UC-linked rows: `58`
- Blank uc_id: `42`
- Legacy `UC-MON-*`: `16`
- Other non-canonical: `0`

## Domain Distribution
| Domain | Total | UC_LINKED | NON_UC_SUPPORT | Canonical UC_LINKED | Unresolved (blank/UC-MON/other) |
| --- | ---: | ---: | ---: | ---: | ---: |
| __init__.py | 1 | 0 | 1 | 0 | 0 |
| account | 37 | 14 | 23 | 14 | 0 |
| activity | 21 | 7 | 14 | 0 | 7 |
| agent | 5 | 0 | 5 | 0 | 0 |
| analytics | 42 | 22 | 20 | 11 | 11 |
| api_keys | 10 | 5 | 5 | 5 | 0 |
| apis | 2 | 0 | 2 | 0 | 0 |
| controls | 24 | 8 | 16 | 6 | 2 |
| hoc_spine | 179 | 122 | 57 | 113 | 9 |
| incidents | 38 | 24 | 14 | 10 | 14 |
| integrations | 59 | 13 | 46 | 12 | 1 |
| logs | 44 | 22 | 22 | 17 | 5 |
| ops | 5 | 0 | 5 | 0 | 0 |
| overview | 6 | 2 | 4 | 2 | 0 |
| policies | 100 | 25 | 75 | 16 | 9 |

## Artifacts
- Summary CSV: `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_USAGE_INVENTORY_2026-02-15.csv`
- Detail CSV (canonical UC-linked rows): `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_USAGE_DETAIL_2026-02-15.csv`
- Unresolved CSV (blank/non-canonical UC ids): `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_USAGE_UNRESOLVED_2026-02-15.csv`
