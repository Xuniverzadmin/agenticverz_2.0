# PIN-492: HOC Domain Literature Generator + CSV Matrix

**Status:** ✅ COMPLETE
**Created:** 2026-01-30
**Category:** Architecture

---

## Summary

Two scripts built: (1) hoc_domain_literature_generator.py generates 305 .md files (292 per-file + 12 summaries + INDEX) for L5/L6/L7 across all customer domains. (2) hoc_domain_literature_csv.py generates LITERATURE_MATRIX.csv with 292 rows x 25 columns including linkage_chain showing L4-L5-L6-L7 wiring. Output at literature/hoc_domain/. CSV at https://github.com/Xuniverzadmin/agenticverz_2.0/blob/main/literature/hoc_domain/LITERATURE_MATRIX.csv. Coverage: 197 L5 + 66 L6 + 29 L7 files, 262/292 have discovered callers, 39 call L6, 56 call L7, 15 cross-domain. Disposition column empty for review.

---

## Details

### Script 1: `scripts/ops/hoc_domain_literature_generator.py`

AST-based generator that produces per-file `.md` literature for every Python file under `hoc/cus/{domain}/` at L5, L6, and L7 layers.

**Output:** `literature/hoc_domain/` — 305 `.md` files:
- 292 per-file `.md` files (one per Python source file)
- 12 domain `_summary.md` files
- 1 master `INDEX.md`

**Per-file .md contains:**
- Metadata table: path, layer, domain, audience, artifact class
- Description + Intent (from `# Role:`, `# Reference:`, `# Callers:` headers)
- Purpose (module docstring first paragraph)
- Functions: signature, async flag, decorators, docstring, outbound calls (AST-extracted)
- Classes: bases, methods, class variables, docstring
- Module attributes (constants, assignments)
- Import analysis table: L5 Engine, L5 Schema, L6 Driver, L7 Model, Cross-Domain, External
- Callers (from file header)
- Export contract (YAML block)
- Evaluation notes: Disposition (KEEP / MODIFY / QUARANTINE / DEPRECATED) — empty for review

**CLI:**
```bash
python3 scripts/ops/hoc_domain_literature_generator.py --generate
python3 scripts/ops/hoc_domain_literature_generator.py --generate --domain policies
python3 scripts/ops/hoc_domain_literature_generator.py --generate --layer L5
python3 scripts/ops/hoc_domain_literature_generator.py --json
python3 scripts/ops/hoc_domain_literature_generator.py --index
```

---

### Script 2: `scripts/ops/hoc_domain_literature_csv.py`

Produces a single CSV for spreadsheet-based review with layer linkage chain.

**Output:** `literature/hoc_domain/LITERATURE_MATRIX.csv` — 292 rows, 25 columns.

**25 Columns:**

| Column | Description |
|--------|-------------|
| domain | Domain name (policies, account, etc.) |
| layer | L5, L6, or L7 |
| folder | Subfolder (L5_engines, L6_drivers, models, etc.) |
| filename | Python file stem |
| rel_path | Relative path from project root |
| lines | Line count |
| purpose | One-liner from `# Role:` header or docstring |
| functions | Pipe-separated function names |
| fn_count | Function count |
| async_count | Async function count |
| classes | Pipe-separated class names |
| cls_count | Class count |
| calls_l5 | L5 engine imports (downstream) |
| calls_l5_schema | L5 schema imports (downstream) |
| calls_l6 | L6 driver imports (downstream, L5→L6 link) |
| calls_l7 | L7 model imports (downstream, L6→L7 link) |
| cross_domain | Imports from other domains |
| external_deps | External libraries (sqlalchemy, pydantic, etc.) |
| called_by | Who imports this file (with layer prefix, grep-discovered) |
| caller_layers | Upstream layer summary (e.g. `L2 + L4 + L5`) |
| header_callers | Declared callers from file header |
| header_allowed_imports | Governance: allowed imports from header |
| header_forbidden_imports | Governance: forbidden imports from header |
| linkage_chain | Full wiring: `L2 + L4 → THIS(L5) → L6 + L7` |
| disposition | Empty — for KEEP / MODIFY / QUARANTINE / DEPRECATED |

**CLI:**
```bash
python3 scripts/ops/hoc_domain_literature_csv.py
python3 scripts/ops/hoc_domain_literature_csv.py --domain policies
python3 scripts/ops/hoc_domain_literature_csv.py --skip-callers
```

---

### Coverage Stats (2026-01-30)

| Metric | Count |
|--------|-------|
| Total files processed | 292 |
| L5 files | 197 |
| L6 files | 66 |
| L7 files | 29 |
| Files with discovered callers | 262/292 |
| Files calling L6 drivers | 39 |
| Files calling L7 models | 56 |
| Cross-domain imports | 15 |
| Orphans (no callers, excl L7) | 29 |

### Domains Covered

| Domain | Files |
|--------|-------|
| policies | 76 |
| integrations | 47 |
| logs | 30 |
| analytics | 29 |
| _models (L7) | 29 |
| incidents | 28 |
| controls | 22 |
| account | 13 |
| activity | 11 |
| api_keys | 4 |
| overview | 2 |
| apis | 1 |

### Output Locations

- Literature: `literature/hoc_domain/{domain}/{folder}/{md_name}.md`
- Summaries: `literature/hoc_domain/{domain}/_summary.md`
- Index: `literature/hoc_domain/INDEX.md`
- CSV: `literature/hoc_domain/LITERATURE_MATRIX.csv`
- GitHub: https://github.com/Xuniverzadmin/agenticverz_2.0/blob/main/literature/hoc_domain/LITERATURE_MATRIX.csv

### Design Notes

- Reuses AST extraction patterns from `hoc_spine_study_validator.py` (PIN-491)
- `_models` is synthetic grouping for L7 shared ORM at `backend/app/models/` (not under `hoc/cus/`)
- Excluded: `__init__.py`, L2 (`hoc/api/cus/`), L4 (`hoc_spine/`, `L4_runtime/`), adapters folders
- Filename convention: `hoc_cus_{domain}_{folder}_{filename}.md` or `hoc_models_{filename}.md`
- Caller discovery uses `grep -rl` (ripgrep not available to subprocess)
- Linkage chain built from: grep upstream callers + AST-classified downstream imports
