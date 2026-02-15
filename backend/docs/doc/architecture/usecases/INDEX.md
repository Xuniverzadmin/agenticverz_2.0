> **DEPRECATED (2026-02-11):** This file is NON-CANONICAL. The canonical usecase registry is at:
> `backend/app/hoc/docs/architecture/usecases/INDEX.md`
> Do not update this file. All changes must go to the canonical root.

# HOC Usecase Registry

> Canonical index of all usecases tracked in the HOC architecture.
> Each usecase has a stable ID, audience classification, and status.

## Registry

| ID | Usecase | Audience | Status | Last Updated |
|----|---------|----------|--------|-------------|
| UC-001 | LLM Run Monitoring | cust,int,fdr | GREEN | 2026-02-11 |
| UC-002 | Customer Onboarding | cust,int,fdr | GREEN | 2026-02-11 |
| UC-003 | Ingest Run + Deterministic Trace | cust | GREEN | 2026-02-11 |
| UC-004 | Runtime Controls Evaluation | cust | GREEN | 2026-02-11 |

## Status Definitions

- **GREEN**: All audit criteria met, endpoint-to-handler mapping complete, CI enforced
- **YELLOW**: Core structure in place, audited, some gaps remain (e.g., endpoint mapping, schema enforcement)
- **RED**: Structural violations present, functional bugs, or missing domain authority
- **TBD**: Not yet scoped

## Rules

1. One stable ID per usecase (`UC-###`)
2. Audience labels: `cust` (customer), `int` (internal), `fdr` (founder) only
3. Status must be synchronized between this index and `HOC_USECASE_CODE_LINKAGE.md`
4. Register in this file FIRST, then add detailed section in linkage doc

## Workflow

```
INDEX.md (register UC-###) -> HOC_USECASE_CODE_LINKAGE.md (add/update section) -> sync status
```
