# HOC FDR API Ledger Wave 2 Audit

- Generated UTC: 2026-02-21T07:28:00Z
- Worktree: /tmp/hoc-wave2-fdr-ledger
- Branch: `hoc/wave2-hoc-api-ledger-fdr`

## Artifact Generation

```bash
python3 /root/.codex/skills/hoc-cus-api-ledger-rollout/scripts/build_cus_api_ledger.py \
  --repo-root /tmp/hoc-wave2-fdr-ledger \
  --openapi-source /tmp/hoc-wave2-fdr-ledger/docs/openapi.json \
  --path-prefix /hoc/api/fdr/ \
  --source-scan-root /tmp/hoc-wave2-fdr-ledger/backend/app/hoc/api/fdr \
  --out-json docs/api/HOC_FDR_API_LEDGER.json \
  --out-csv docs/api/HOC_FDR_API_LEDGER.csv \
  --out-md docs/api/HOC_FDR_API_LEDGER.md
```

- Result: OpenAPI produced 0 rows; source fallback produced 66 rows.

## Mismatch Audit

```bash
python3 <inline>  # compare docs/openapi.json vs HOC_FDR_API_LEDGER.json by method+path
```

- Output files:
  - `docs/api/HOC_FDR_API_LEDGER_MISMATCH_AUDIT_2026-02-21.md`
  - `docs/api/HOC_FDR_API_LEDGER_MISMATCH_AUDIT_2026-02-21.json`
- Result:
  - source unique: 66
  - openapi unique under `/hoc/api/fdr/*`: 0
  - source-only: 66
  - openapi-only: 0

## Publication Logic Validation

```bash
cd backend && PYTHONPATH=. python3 - <<'PY'
from app.hoc.fdr.ops.engines.stagetest_read_engine import get_apis_ledger_snapshot
snap = get_apis_ledger_snapshot()
print(snap["run_id"], len(snap["endpoints"]))
print(any(e["path"].startswith("/hoc/api/cus/") for e in snap["endpoints"]))
print(any(e["path"].startswith("/hoc/api/fdr/") for e in snap["endpoints"]))
PY
```

- Result:
  - run_id: `ledger-hoc-all`
  - endpoints: `568`
  - includes CUS rows: true
  - includes FDR rows: true

## Governance Checks

```bash
cd backend && PYTHONPATH=. pytest -q tests/api/test_stagetest_read_api.py
cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
cd /tmp/hoc-wave2-fdr-ledger && python3 scripts/ci/check_openapi_snapshot.py
cd /tmp/hoc-wave2-fdr-ledger && python3 scripts/ops/capability_registry_enforcer.py check-pr --files <changed_py>
cd /tmp/hoc-wave2-fdr-ledger && python3 scripts/ops/layer_segregation_guard.py --scope hoc
```

- Results:
  - pytest: `10 passed`
  - layer boundaries: PASS
  - openapi snapshot: PASS
  - capability check-pr: PASS with 2 non-blocking `MISSING_EVIDENCE` warnings
  - layer segregation hoc-wide: FAIL with 93 legacy violations (unchanged debt lane)
