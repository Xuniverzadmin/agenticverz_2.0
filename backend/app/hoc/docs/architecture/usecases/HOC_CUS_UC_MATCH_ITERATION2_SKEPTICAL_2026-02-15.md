# HOC CUS Script-vs-Usecase Matching - Iteration 2 Skeptical Audit (2026-02-15)

## Skeptical Findings
- `WEAK_EVIDENCE_CSV_ONLY`: `134`
- `RECOVERED_FROM_LEGACY_OR_BLANK`: `28`
- `UNRESOLVED`: `30`
- Total flagged rows: `192` / `264`

## Domain Hotspots
| Domain | Flagged | WEAK_EVIDENCE_CSV_ONLY | RECOVERED_FROM_LEGACY_OR_BLANK | UNRESOLVED |
| --- | ---: | ---: | ---: | ---: |
| account | 13 | 13 | 0 | 0 |
| activity | 7 | 0 | 0 | 7 |
| analytics | 22 | 11 | 8 | 3 |
| api_keys | 5 | 5 | 0 | 0 |
| controls | 8 | 6 | 1 | 1 |
| hoc_spine | 56 | 47 | 1 | 8 |
| incidents | 24 | 10 | 7 | 7 |
| integrations | 8 | 7 | 0 | 1 |
| logs | 22 | 17 | 2 | 3 |
| overview | 2 | 2 | 0 | 0 |
| policies | 25 | 16 | 9 | 0 |

## Skeptical Conclusion
1. Keep unresolved rows unmapped; no force-fit applied.
2. Treat CSV-only matches as provisional until explicit UC section anchors are added.
3. Require domain-owner signoff for recovered legacy/blank mappings before contract lock.

## Artifact
- Skeptical flags CSV: `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_MATCH_ITERATION2_FLAGS_2026-02-15.csv`
